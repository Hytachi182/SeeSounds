"""Opt-in desktop integration checks; never touch the learner's workspace."""
from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QEventLoop
from PySide6.QtMultimedia import QAudioBufferOutput, QMediaPlayer
from PySide6.QtWidgets import QApplication

from src.database import Repository
from src.models import Sound
from src.ui.main_window import MainWindow


def run_self_test(style: str) -> int:
    parser = argparse.ArgumentParser(description="Run isolated desktop integration checks")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"platform": platform.platform(), "architecture": platform.machine(), "frozen": bool(getattr(sys, "frozen", False)), "checks": [], "success": False}
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(style)
    window = None
    repo = None

    def wait_until(predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
            if predicate():
                return
            time.sleep(0.01)
        raise AssertionError("Timed out waiting for desktop/audio state")

    try:
        assert args.audio.is_file(), "Missing synthetic MP3 fixture"
        with tempfile.TemporaryDirectory(prefix="seesounds-self-test-") as folder:
            repo = Repository(Path(folder) / "test.db")
            window = MainWindow(repo)
            window.show()
            wait_until(lambda: window.isVisible())
            assert not window.windowIcon().isNull(), "Application icon was not bundled"
            for language in ("en", "fr"):
                window.language = language
                window.apply_language()
                for index in range(window.nav.count()):
                    window.nav.setCurrentRow(index)
                    app.processEvents()
                    assert window.pages.currentIndex() == index
            report["checks"].append("window, icon and seven pages in both languages")
            ids = [repo.save_sound(f"Tone {i}", str(Path(folder) / f"{i}.mp3"), 0, True, "QA", []) for i in range(5)]
            sound_id = ids[0]
            repo.record_training(sound_id, True)
            for level in (1, 2):
                window.level.setCurrentIndex(level - 1)
                window.play_sound = lambda sound: None
                window.start_exam()
                assert window.exam is not None
                while window.exam:
                    sound = window.exam["questions"][window.exam["index"]]
                    if level == 1:
                        for i in range(window.options.count()):
                            choice = window.options.itemAt(i).widget()
                            if choice.text() == sound.name:
                                choice.click()
                                break
                    else:
                        window.exam_answer.setText(sound.name)
                        window.submit.click()
                assert len(repo.exam_answers(window.last_exam_id)) == 5
                assert repo.recent_exams()[0]["score"] == 5
            export = Path(folder) / "library.json"
            repo.export_library(export)
            repo.import_library(export)
            assert repo.statistics() == {"attempts": 1, "rate": 1.0, "exams": 2}
            report["checks"].append("training, both full exams, review and JSON round trip")

            audio = window.audio
            audio.output.setMuted(True)
            decoded = QAudioBufferOutput()
            audio.player.setAudioBufferOutput(decoded)
            buffers, errors, positions, endings = [], [], [], []
            decoded.audioBufferReceived.connect(lambda buffer: buffers.append(buffer.byteCount()) if buffer.isValid() else None)
            audio.player.errorOccurred.connect(lambda error, message: errors.append(message))
            audio.player.positionChanged.connect(positions.append)
            audio.player.mediaStatusChanged.connect(lambda status: endings.append(status) if status == QMediaPlayer.MediaStatus.EndOfMedia else None)
            tone = Sound(100, "Synthetic tone", args.audio.resolve(), 0.35)
            audio.play(tone)
            wait_until(lambda: bool(buffers) or bool(errors))
            assert not errors, errors
            assert sum(buffers) > 0, "MP3 did not produce decoded audio"
            assert 350 in positions, "Per-sound seek was not applied"
            audio.pause_or_resume()
            assert audio.player.playbackState() == QMediaPlayer.PlaybackState.PausedState
            audio.pause_or_resume()
            assert audio.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            audio.stop()
            endings.clear()
            audio.play_queue([tone, tone])
            wait_until(lambda: len(endings) == 2 or bool(errors))
            assert not errors, errors
            assert len(endings) == 2 and not audio._queue
            report["decoded_bytes"] = sum(buffers)
            report["checks"].append("real MP3 decoding, offset, pause/resume and two-clip queue")
            window.nav.setCurrentRow(0)
            app.processEvents()
            args.report.parent.mkdir(parents=True, exist_ok=True)
            assert window.grab().save(str(args.report.with_suffix(".png")))
            report["success"] = True
            audio.stop()
            window.close()
            repo.close()
            window = repo = None
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if window is not None:
            window.audio.stop()
            window.close()
        if repo is not None:
            repo.close()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["success"] else 1
