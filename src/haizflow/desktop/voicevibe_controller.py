"""VoiceVibe tab inside the main HaizFlow app (not a separate tool).

This controller reuses Edge TTS directly (no HaizFlow project needed) and
the Seed-VC / RVC / OpenVoice engines only when their model folders are
already installed. It never fakes audio: if a voice or model is missing,
it reports that in ``status`` instead of writing an empty file.

Flow, same as the old standalone tool:
1. ``generatePreview`` writes a temp mp3.
2. QML plays ``previewPath`` in-app (QtMultimedia).
3. Only then ``savePreview`` copies it to a path the user chose in a
   FileDialog, so the export location is always the user's choice.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

EDGE_VOICES = [
    "vi-VN-HoaiMyNeural",
    "vi-VN-NamMinhNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-YunxiNeural",
]

VC_PRESETS = {
    "light": {"seed_vc_diffusion_steps": 12},
    "balanced": {"seed_vc_diffusion_steps": 20},
    "quality": {"seed_vc_diffusion_steps": 30},
}


def _parse_rate(text: str) -> str:
    return str(text or "+0%").strip()


def _parse_pitch(text: str) -> str:
    return str(text or "+0Hz").strip()


class VoiceVibeController(QObject):
    changed = Signal()

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self._host = host
        self._status = "Nhập văn bản, chọn giọng, bấm Tạo nghe thử."
        self._busy = False
        self._preview_path = ""

    @Property(str, notify=changed)
    def status(self):
        return self._status

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def previewPath(self):
        return self._preview_path

    @staticmethod
    def _normalize_language(language):
        """Tab language for TTS: 'en' for English, otherwise Vietnamese.

        Previously the tab hardcoded 'vi' here, so even an English script
        read through OmniVoice came out as Vietnamese. The language now
        comes from the tab's language selector, never from a hardcoded value.
        """
        lang = str(language or "vi").strip().lower()
        if lang.startswith("en"):
            return "en"
        if lang.startswith("zh"):
            return "zh"
        return "vi"

    @Slot(str, str, result="QVariantList")
    def linkedVoices(self, provider, language="vi"):
        """Voices straight from the main app catalog, not a copy in this tab.

        The host controller owns the catalog and the resource-pack state, so
        installing a pack in Settings immediately changes what this returns.
        The language argument matters: asking for 'en' returns the English
        catalog (OmniVoice / Edge en-US), not the Vietnamese one.
        """
        host = self._host
        lang = self._normalize_language(language)
        provider = str(provider or "edge").strip().lower()
        # QUAN TRONG: danh muc VieNeu cua app chinh tra ve giong Viet cho moi
        # ngon ngu (tru tieng Trung), ke ca khi language="en". Neu tra nguyen
        # danh sach do ve cho tab tieng Anh, nguoi dung se thay toan giong
        # Viet (Hai Dang, Truc Ly...) va tuong la tab loi, dung nhu anh trong
        # bao cao. VieNeu chi doc tieng Viet, nen voi tieng Anh thi khong tra
        # giong Viet nao ca — giao dien se tu chuyen sang OmniVoice.
        if lang == "en" and provider.startswith("vieneu"):
            return []
        try:
            return host.voiceOptionsForLanguageAndProvider(lang, provider)
        except Exception:
            try:
                return host._voice_options_for_language(lang, str(provider or "edge"))
            except Exception:
                return []

    @Slot(str, result=str)
    def linkedPackStatus(self, provider):
        """One-line pack status for a provider, from the main app's pack rows."""
        host = self._host
        try:
            rows = host.resourcePackageRows or []
        except Exception:
            rows = []
        provider = str(provider or "").lower()
        want = "vieneu" if "vieneu" in provider else "omnivoice" if "omnivoice" in provider else "edge"
        if want == "edge":
            return "Edge: giọng online, không cần gói tài nguyên."
        for row in rows:
            if isinstance(row, dict):
                text = " ".join(str(v) for v in row.values())
                if want in text.lower():
                    name = row.get("name") or row.get("title") or row.get("id") or want
                    status = row.get("status") or row.get("state") or ""
                    if status:
                        return f"{name}: {status}".strip()
                    # Khong stringify ca row (truoc day hien "vieneu: inventory"
                    # rat kho hieu). Chi bao la co trong Goi tai nguyen, de nguoi
                    # dung mo Cai dat > Goi tai nguyen xem da tai xong chua.
                    return f"{name}: có trong Gói tài nguyên — mở Cài đặt > Gói tài nguyên để xem đã tải xong chưa."
            elif want in str(row).lower():
                return f"{want}: có trong Gói tài nguyên — mở Cài đặt > Gói tài nguyên để xem đã tải xong chưa."
        return f"Chưa thấy gói {want} trong Gói tài nguyên. Hãy vào Cài đặt > Gói tài nguyên để cài."

    def _set(self, status=None, busy=None, preview=None):
        if status is not None:
            self._status = status
        if busy is not None:
            self._busy = busy
        if preview is not None:
            self._preview_path = preview
        self.changed.emit()

    def _validate_combo(self, voice, provider, language):
        """Block voice/provider/language mismatches BEFORE any synthesis.

        These mismatches used to fail silently or misleadingly:
        - VieNeu + tieng Anh: VieNeu chi doc tieng Viet, pipeline khong chan
          combo nay (chi chan tieng Trung), nen tieng Anh se bi doc lech.
        - Giong khong dung nha cung cap (vi du giong vieneu: trong khi provider
          la omnivoice, do danh sach giong refresh cham): pipeline
          normalize_voice se am tham doi thanh omnivoice:female, nguoi dung
          nghe giong khac ma tuong la loi.
        - Giong clone ma khong co file mau: pipeline se bao loi, tab nay
          khong co cho chon file mau cho phan doc van ban.
        - Ban -gpu tren may khong co GPU: worker se dung o cuda:0.
        Tra ve thong bao loi ro rang, hoac None neu hop le.
        """
        voice = str(voice or "").strip()
        provider = str(provider or "").strip().lower()
        language = self._normalize_language(language)
        if voice in {"omnivoice:clone", "vieneu:clone"}:
            return ("Giọng nhân bản cần file giọng mẫu, tab này chưa hỗ trợ cho phần đọc văn bản. "
                    "Hãy chọn một giọng có sẵn khác, hoặc dùng giọng nhân bản trong dự án Tự động/Thủ công của app.")
        if language == "en" and provider.startswith("vieneu"):
            return ("VieNeu chỉ đọc tiếng Việt, không đọc tiếng Anh. "
                    "Để đọc tiếng Anh, hãy chọn OmniVoice hoặc Edge, hoặc đổi ngôn ngữ về Tiếng Việt.")
        if provider.startswith("omnivoice") and not voice.startswith("omnivoice:"):
            return (f"Giọng '{voice}' không thuộc OmniVoice, có thể do danh sách giọng chưa kịp tải lại sau khi đổi nhà cung cấp. "
                    "Hãy chọn lại nhà cung cấp rồi chọn lại giọng trong danh sách, sau đó bấm Tạo nghe thử lại.")
        if provider.startswith("vieneu") and not voice.startswith("vieneu:"):
            return (f"Giọng '{voice}' không thuộc VieNeu, có thể do danh sách giọng chưa kịp tải lại sau khi đổi nhà cung cấp. "
                    "Hãy chọn lại nhà cung cấp rồi chọn lại giọng trong danh sách, sau đó bấm Tạo nghe thử lại.")
        if provider == "edge":
            expected = {"vi": "vi-VN-", "en": "en-US-", "zh": "zh-CN-"}.get(language, "")
            if expected and not voice.startswith(expected):
                return (f"Giọng Edge '{voice}' không khớp ngôn ngữ {language}. "
                        "Hãy chọn lại ngôn ngữ rồi chọn lại giọng trong danh sách.")
        if provider.endswith("-gpu"):
            try:
                gpu_available = self._host._project_gpu_available()
            except Exception:
                gpu_available = True
            if gpu_available is False:
                return ("Máy này không có GPU nên không chạy được bản -gpu. "
                        "Hãy chọn bản CPU cùng nhà cung cấp đó (ví dụ OmniVoice thay vì OmniVoice GPU).")
        return None

    def _run_preview(self, text, voice, rate, pitch, volume):
        # Khong gan previewPath truoc khi co audio that: truoc day file rong
        # da duoc gan truoc, nen khi tong hop loi, thanh play van hien ra
        # nhung bam nghe thi im lang, rat de tuong la "giong loi".
        tmp = ""
        try:
            import edge_tts

            async def _gen():
                # Cach goi giong HaizFlow: khong truyen rate/pitch/volume vao Communicate,
                # vi cac tham so nay de gay loi "No audio was received" tren mot so ban edge-tts.
                # Chi stream packet audio va kiem tra co nhan duoc audio that khong.
                communicate = edge_tts.Communicate(text, voice, connect_timeout=10, receive_timeout=20)
                received = 0
                with open(tmp, "wb") as stream:
                    async for packet in communicate.stream():
                        if packet.get("type") == "audio":
                            data = packet.get("data") or b""
                            stream.write(data)
                            received += len(data)
                if received == 0:
                    raise RuntimeError("Không nhận được audio từ Edge. Hãy thử lại, đổi giọng khác, hoặc rút ngắn văn bản.")

            fd, tmp = tempfile.mkstemp(suffix=".mp3", prefix="voicevibe_preview_")
            os.close(fd)
            asyncio.run(_gen())
            if not os.path.exists(tmp) or os.path.getsize(tmp) < 512:
                raise RuntimeError("File nghe thử trống hoặc quá nhỏ. Hãy thử lại.")
            self._set(status="Đã tạo xong bản nghe thử. Bấm “Nghe thử trong app” trước khi tải xuống.", busy=False, preview=tmp)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user in-app
            if tmp:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            # Xoa preview cu de thanh play khong hien file hong.
            self._set(status=f"Tạo nghe thử thất bại: {exc} Kiểm tra internet rồi thử lại.", busy=False, preview="")

    def _run_local_preview(self, text, voice, provider, language="vi"):
        tmp = ""
        try:
            from haizflow.pipeline.tts import generate_single_voice

            fd, tmp = tempfile.mkstemp(suffix=".mp3", prefix="voicevibe_preview_")
            os.close(fd)
            # video_id rong: tab khong thuoc ve du an nao, pipeline chi dung no de ghi log.
            # Ngon ngu lay tu o chon ngon ngu cua tab, KHONG ghi cung "vi" nua:
            # tieng Anh qua OmniVoice phai chay target_language="en" moi doc tieng Anh.
            generate_single_voice(
                text, tmp, voice, "", provider=provider,
                target_language=self._normalize_language(language),
            )
            if not os.path.exists(tmp) or os.path.getsize(tmp) < 512:
                raise RuntimeError("File nghe thử trống hoặc quá nhỏ (dưới 512 byte) — pipeline không tạo được audio thật.")
            self._set(status="Đã tạo xong bản nghe thử. Bấm “Nghe thử trong app” trước khi tải xuống.", busy=False, preview=tmp)
        except Exception as exc:  # noqa: BLE001
            if tmp:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            self._set(
                status=f"Giọng {provider} / {voice} / ngôn ngữ {self._normalize_language(language)} chưa tạo được trong tab này: {exc} "
                       f"Nếu gói {provider} đang tải dở thì đợi tải xong rồi thử lại. "
                       f"Nếu vẫn lỗi, hãy thử một câu ngắn trước để tách lỗi model với lỗi văn bản dài, "
                       f"hoặc dùng giọng này trong dự án Tự động/Thủ công của app.",
                busy=False,
                preview="",
            )

    @Slot(str, str, str, str, str)
    def generatePreview(self, text, voice, rate="", pitch="", volume=""):
        self.generatePreviewWithProvider(text, voice, "edge", rate, pitch, volume)

    @Slot(str, str, str, str, str, str, str)
    def generatePreviewWithProvider(self, text, voice, provider="edge", rate="", pitch="", volume="", language="vi"):
        text = str(text or "").strip()
        if self._busy:
            return
        if not text:
            self._set(status="Hãy nhập văn bản trước đã.")
            return
        if not voice:
            self._set(status="Chưa chọn được giọng nào. Hãy chọn ngôn ngữ, chọn nhà cung cấp rồi chọn 1 giọng trong danh sách.")
            return
        provider = str(provider or "edge").strip().lower()
        language = self._normalize_language(language)
        combo_error = self._validate_combo(voice, provider, language)
        if combo_error:
            self._set(status=combo_error)
            return
        self._set(status="Đang tạo bản nghe thử...", busy=True)
        if provider == "edge":
            # Edge: giong da mang ma ngon ngu trong ten (vi-VN-..., en-US-...),
            # danh sach giong da duoc loc theo ngon ngu o linkedVoices, nen khong
            # can truyen them ngon ngu vao day.
            threading.Thread(
                target=self._run_preview,
                args=(text, voice, _parse_rate(rate), _parse_pitch(pitch), _parse_rate(volume)),
                daemon=True,
            ).start()
        else:
            threading.Thread(target=self._run_local_preview, args=(text, voice, provider, language), daemon=True).start()

    @Slot(str)
    def savePreview(self, output_path):
        output_path = str(output_path or "").strip()
        if not self._preview_path or not os.path.exists(self._preview_path):
            self._set(status="Chưa có bản nghe thử. Hãy bấm Tạo nghe thử trước.")
            return
        if not output_path:
            self._set(status="Hãy chọn chỗ để xuất file trước.")
            return
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self._preview_path, output_path)
            self._set(status=f"Đã xuất file: {output_path}")
        except Exception as exc:  # noqa: BLE001
            self._set(status=f"Xuất file thất bại: {exc}")

    @Slot(str, str, str, str, bool)
    def convertPreview(self, source, reference, model="seed-vc", mode="light", singing=False):
        source = str(source or "").strip()
        reference = str(reference or "").strip()
        if not source or not reference:
            self._set(status="Cần cả file gốc và file giọng mẫu.")
            return
        if model == "seed-vc":
            script = Path("models") / "seed-vc" / "inference_v2.py"
            if not script.exists():
                self._set(status="Chưa cài Seed-VC. Hãy cài từ github.com/Plachtaa/seed-vc vào thư mục models/seed-vc.")
                return
            steps = 40 if singing else VC_PRESETS.get(mode, VC_PRESETS["light"])["seed_vc_diffusion_steps"]
            fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="voicevibe_vc_preview_")
            os.close(fd)
            self._set(status="Đang đổi giọng...", busy=True)

            def _run():
                try:
                    subprocess.run(
                        ["python", str(script), "--source", source, "--target", reference,
                         "--output", tmp, "--diffusion-steps", str(steps)],
                        check=True,
                    )
                    self._set(status="Đã đổi giọng xong bản nghe thử.", busy=False, preview=tmp)
                except Exception as exc:  # noqa: BLE001
                    self._set(status=f"Đổi giọng thất bại: {exc}", busy=False)

            threading.Thread(target=_run, daemon=True).start()
        else:
            self._set(status=f"Model {model} cần file .pth trong models/{model}/. Đặt file vào đó rồi thử lại.")
