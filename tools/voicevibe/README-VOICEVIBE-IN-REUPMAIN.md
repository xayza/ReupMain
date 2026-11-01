# VoiceVibe trong ReupMain - cach de nhat

Day la ban VoiceVibe day du, dat nguyen ven trong ReupMain tai `tools/voicevibe/`,
khong sua code HaizFlow chinh, khong dong vao QML, nen khong lam hong app chinh.

Chay:
```bash
cd tools/voicevibe
pip install -r requirements-qt.txt
python gui_qt.py
```
Build exe tren Windows: chay `build-exe.bat` trong thu muc nay, ra `dist\VoiceVibe.exe`.

Gom: TTS 71 giong HaizFlow, doi giong Seed-VC/RVC/OpenVoice, nghe thu truoc khi tai,
batch, lich su, quan ly/xoa model, cai OmniVoice/VieNeu qua goi HaizFlow, che do light cho may yeu.
Ban goc rieng van o repo VoiceVibe, day la ban bo sung vao ReupMain theo yeu cau de dung chung 1 repo.
