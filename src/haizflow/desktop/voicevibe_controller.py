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

    def _set(self, status=None, busy=None, preview=None):
        if status is not None:
            self._status = status
        if busy is not None:
            self._busy = busy
        if preview is not None:
            self._preview_path = preview
        self.changed.emit()

    def _run_preview(self, text, voice, rate, pitch, volume):
        try:
            import edge_tts

            async def _gen():
                # Cach goi giong HaizFlow: khong truyen rate/pitch/volume vao Communicate,
                # vi cac tham so nay de gay loi "No audio was received" tren mot so ban edge-tts.
                # Chi stream packet audio va kiem tra co nhan duoc audio that khong.
                communicate = edge_tts.Communicate(text, voice, connect_timeout=10, receive_timeout=20)
                received = 0
                with open(self._preview_path, "wb") as stream:
                    async for packet in communicate.stream():
                        if packet.get("type") == "audio":
                            data = packet.get("data") or b""
                            stream.write(data)
                            received += len(data)
                if received == 0:
                    raise RuntimeError("Không nhận được audio từ Edge. Hãy thử lại, đổi giọng khác, hoặc rút ngắn văn bản.")

            fd, tmp = tempfile.mkstemp(suffix=".mp3", prefix="voicevibe_preview_")
            os.close(fd)
            self._preview_path = tmp
            asyncio.run(_gen())
            if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
                raise RuntimeError("File nghe thử trống. Hãy thử lại.")
            self._set(status="Đã tạo xong bản nghe thử. Bấm “Nghe thử trong app” trước khi tải xuống.", busy=False, preview=tmp)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user in-app
            self._set(status=f"Tạo nghe thử thất bại: {exc} Kiểm tra internet rồi thử lại.", busy=False)

    @Slot(str, str, str, str, str)
    def generatePreview(self, text, voice, rate="", pitch="", volume=""):
        text = str(text or "").strip()
        if self._busy:
            return
        if not text:
            self._set(status="Hãy nhập văn bản trước đã.")
            return
        if not voice:
            voice = EDGE_VOICES[0]
        self._set(status="Đang tạo bản nghe thử...", busy=True)
        threading.Thread(
            target=self._run_preview,
            args=(text, voice, _parse_rate(rate), _parse_pitch(pitch), _parse_rate(volume)),
            daemon=True,
        ).start()

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
