import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from src.database import Repository
from src.ui.main_window import MainWindow
from unittest.mock import Mock
from src.models import Sound
from pathlib import Path


def test_fresh_workspace_opens_every_page(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "test.db")
    window = MainWindow(repo)
    try:
        for index in range(window.nav.count()):
            window.nav.setCurrentRow(index)
            app.processEvents()
            assert window.pages.currentIndex() == index
    finally:
        window.audio.stop()
        window.close()
        repo.close()


def test_wrong_multiple_choice_cannot_pass_via_fuzzy_matching():
    window = Mock()
    window.exam = {"questions": [Sound(1,"Bird song 1",Path("1.mp3"))], "index": 0, "answers": [], "difficulty": 1, "reveal": False}
    MainWindow.submit_answer(window, "Bird song 2", 2)
    assert window.exam["answers"][0]["result"] == "incorrect"
    assert window.exam["answers"][0]["similarity"] == 0


def test_free_text_submit_button_reads_typed_answer(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "test.db")
    window = MainWindow(repo)
    try:
        sound_id = repo.save_sound("Robin", "robin.mp3", 0, True, None, [])
        window.exam = {"questions": [repo.sound(sound_id)], "index": 0, "answers": [], "difficulty": 2, "reveal": False}
        window.finish_exam = Mock()
        window.exam_answer.setText("robin")
        window.submit.click()
        assert window.exam["answers"][0]["answer"] == "robin"
        assert window.exam["answers"][0]["result"] == "correct"
    finally:
        window.audio.stop()
        window.close()
        app.processEvents()
        repo.close()
