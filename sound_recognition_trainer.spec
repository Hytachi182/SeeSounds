# Build on the target operating system only: Windows on Windows, macOS on macOS.
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("PySide6") + [("assets/sound-recognition-trainer.svg", "assets")]
a = Analysis(["app.py"], pathex=["."], datas=datas, hiddenimports=["PySide6.QtMultimedia"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="SoundRecognitionTrainer", console=False)
