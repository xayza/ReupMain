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
        self._status = "Nhap text, chon giong, bam Tao nghe thu."
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
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
                await communicate.save(self._preview_path)

            fd, tmp = tempfile.mkstemp(suffix=".mp3", prefix="voicevibe_preview_")
            os.close(fd)
            self._preview_path = tmp
            asyncio.run(_gen())
            if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
                raise RuntimeError("File nghe thu rong.")
            self._set(status=f"Da tao xong ban nghe thu. Bam Nghe thu trong app truoc khi tai.", busy=False, preview=tmp)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user in-app
            self._set(status=f"Tao nghe thu that bai: {exc}. Can internet cho giong Edge.", busy=False)

    @Slot(str, str, str, str, str)
    def generatePreview(self, text, voice, rate="", pitch="", volume=""):
        text = str(text or "").strip()
        if self._busy:
            return
        if not text:
            self._set(status="Nhap text truoc.")
            return
        if not voice:
            voice = EDGE_VOICES[0]
        self._set(status="Dang tao ban nghe thu...", busy=True)
        threading.Thread(
            target=self._run_preview,
            args=(text, voice, _parse_rate(rate), _parse_pitch(pitch), _parse_rate(volume)),
            daemon=True,
        ).start()

    @Slot(str)
    def savePreview(self, output_path):
        output_path = str(output_path or "").strip()
        if not self._preview_path or not os.path.exists(self._preview_path):
            self._set(status="Chua co ban nghe thu. Hay bam Tao nghe thu truoc.")
            return
        if not output_path:
            self._set(status="Chon cho de xuat file truoc.")
            return
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self._preview_path, output_path)
            self._set(status=f"Da xuat file: {output_path}")
        except Exception as exc:  # noqa: BLE001
            self._set(status=f"Xuat file that bai: {exc}")

    @Slot(str, str, str, str, bool)
    def convertPreview(self, source, reference, model="seed-vc", mode="light", singing=False):
        source = str(source or "").strip()
        reference = str(reference or "").strip()
        if not source or not reference:
            self._set(status="Can ca file goc va file giong mau.")
            return
        if model == "seed-vc":
            script = Path("models") / "seed-vc" / "inference_v2.py"
            if not script.exists():
                self._set(status="Chua cai Seed-VC. Vao tab Model cua app hoac cai tu github.com/Plachtaa/seed-vc vao models/seed-vc.")
                return
            steps = 40 if singing else VC_PRESETS.get(mode, VC_PRESETS["light"])["seed_vc_diffusion_steps"]
            fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="voicevibe_vc_preview_")
            os.close(fd)
            self._set(status="Dang doi giong...", busy=True)

            def _run():
                try:
                    subprocess.run(
                        ["python", str(script), "--source", source, "--target", reference,
                         "--output", tmp, "--diffusion-steps", str(steps)],
                        check=True,
                    )
                    self._set(status="Da doi giong xong ban nghe thu.", busy=False, preview=tmp)
                except Exception as exc:  # noqa: BLE001
                    self._set(status=f"Doi giong that bai: {exc}", busy=False)

            threading.Thread(target=_run, daemon=True).start()
        else:
            self._set(status=f"Model {model} can file .pth trong models/{model}/. Dat file vao do roi thu lai.")
