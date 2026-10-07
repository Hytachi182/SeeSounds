"""Exercise the documented macOS installer/launcher from a clean, spaced path."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


root = Path(__file__).resolve().parents[1]
reports = root / "build" / "mac-validation"
reports.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="SeeSounds clean install ") as folder:
    workspace = Path(folder) / "Project with spaces"
    workspace.mkdir()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    for name in filter(None, tracked):
        destination = workspace / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, destination)
    # Exercise the incomplete-environment recovery path on first launch.
    (workspace / ".venv").mkdir()
    interpreter = Path(folder) / "Python with spaces"
    interpreter.symlink_to(sys.executable)
    env = {**os.environ, "PYTHON": str(interpreter)}
    env.pop("QT_QPA_PLATFORM", None)
    env.pop("PYTHONPATH", None)
    tone = workspace / "tests" / "fixtures" / "tone.mp3"

    def launch(name, environment):
        report = reports / f"{name}.json"
        with (reports / f"{name}.log").open("w") as log:
            subprocess.run(["bash", str(workspace / "run_mac.sh"), "--self-test", "--audio", str(tone), "--report", str(report)], cwd=folder, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=True)
        assert json.loads(report.read_text())["success"]

    launch("first-install", env)
    assert list(workspace.glob(".venv.invalid-*")), "Incomplete environment was not backed up"
    # A valid install must relaunch without pip/network access.
    launch("offline-relaunch", {**env, "PIP_NO_INDEX": "1", "PIP_INDEX_URL": "http://127.0.0.1:9"})
    # Interrupted installs can leave package metadata without the package itself.
    venv_python = workspace / ".venv" / "bin" / "python"
    module = Path(subprocess.check_output([str(venv_python), "-c", "import rapidfuzz; print(rapidfuzz.__path__[0])"]).decode().strip())
    shutil.move(str(module), str(Path(folder) / "rapidfuzz-backup"))
    launch("dependency-repair", env)
    print("PASS: first install, spaced paths, incomplete environment, offline relaunch and missing-package repair")
