# Build on the target operating system only: Windows on Windows, macOS on macOS.
import sys

datas = [("assets/sound-recognition-trainer.svg", "assets"), ("LICENSE", ".")]
a = Analysis(["app.py"], pathex=["."], datas=datas, hiddenimports=["PySide6.QtMultimedia"], noarchive=False)
pyz = PYZ(a.pure)
if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, exclude_binaries=True, name="SoundRecognitionTrainer", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="SoundRecognitionTrainer")
    app = BUNDLE(coll, name="SoundRecognitionTrainer.app", bundle_identifier="com.seesounds.soundrecognitiontrainer")
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="SoundRecognitionTrainer", console=False)
