"""Verify ordinary startup and diagnostics without a Python runtime on PATH."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("executable", type=Path)
parser.add_argument("--audio", type=Path, required=True)
parser.add_argument("--report", type=Path, required=True)
args = parser.parse_args()
args.report.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="SeeSounds packaged launch ") as folder:
    env = {**os.environ, "HOME": folder, "USERPROFILE": folder}
    env.pop("PYTHONPATH", None)
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32") if os.name == "nt" else "/usr/bin:/bin"
    database = Path(folder) / ".sound-recognition-trainer" / "sound_trainer.db"
    with args.report.with_suffix(".log").open("w") as log:
        process = subprocess.Popen([str(args.executable.resolve())], cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 30
            while not database.exists() and time.monotonic() < deadline:
                assert process.poll() is None, "Packaged application exited during ordinary startup"
                time.sleep(0.1)
            assert database.exists(), "Ordinary startup did not create its local database"
            time.sleep(1)
            assert process.poll() is None, "Packaged application exited after database initialization"
            with closing(sqlite3.connect(database)) as connection:
                assert connection.execute("SELECT COUNT(*) FROM sounds").fetchone()[0] == 0
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run([str(Path(os.environ["SystemRoot"]) / "System32" / "taskkill.exe"), "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, check=True)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    args.report.with_name(args.report.stem + "-startup.json").write_text(json.dumps({"success": True, "checks": ["ordinary startup with isolated HOME", "database initialized", "no Python on PATH"]}, indent=2))
    subprocess.run([str(args.executable.resolve()), "--self-test", "--audio", str(args.audio.resolve()), "--report", str(args.report.resolve())], cwd=folder, env=env, timeout=90, check=True)
    assert json.loads(args.report.read_text())["success"]
print("PASS: ordinary packaged startup and full desktop/audio integration")
