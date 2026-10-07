import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QCheckBox, QDialogButtonBox
from src.database import Repository
from src.ui.main_window import MainWindow, SoundDialog
from src.ui.localization import FRENCH, translated_error
from app import STYLE


@pytest.fixture
def french_window(tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    repo = Repository(tmp_path / "test.db")
    repo.set_settings({"language": "fr"})
    window = MainWindow(repo)
    yield window
    window.audio.stop()
    window.close()
    repo.close()


def test_static_interface_has_french_coverage(french_window):
    neutral = {"Sound Recognition Trainer", "Sound\nRecognition\nTrainer"}
    for widget in french_window.findChildren(QWidget):
        if not isinstance(widget, (QLabel, QPushButton, QCheckBox)):
            continue
        source = widget.property("source_text")
        if source and source not in neutral:
            assert source in FRENCH, f"Missing translation: {source}"
            assert widget.text() == french_window.t(source, **(widget.property("source_values") or {}))
    assert french_window.level.itemText(0) == "Niveau 1 — Choix multiples"
    assert french_window.category_assign.placeholderText() == "Choisir ou saisir une catégorie"
    assert french_window.global_playback_offset.suffix() == " secondes"
    assert "Every preview" not in french_window.global_playback_offset.toolTip()


def test_refresh_and_language_switch_preserve_user_content(french_window):
    window = french_window
    sound_id = window.repo.save_sound("Training", "bird.mp3", 0, True, "Home", [])
    window.repo.record_training(sound_id, True)
    window.refresh_home()
    window.refresh_library()
    window.refresh_stats()
    window.refresh_filters()
    assert "sons actifs" in window.home_summary.text()
    assert "1 tentatives" in window.home_summary.text()
    assert window.table.item(0, 1).text() == "Training"
    assert window.table.item(0, 2).text() == "Home"
    assert window.table.item(0, 4).text() == "Activé"
    assert "Home" in [window.training_category.itemText(i) for i in range(window.training_category.count())]
    window.training_sound = window.repo.sound(sound_id)
    window.reveal_training()
    window.language_choice.setCurrentIndex(window.language_choice.findData("en"))
    assert window.repo.settings()["language"] == "en"
    assert "1 active sounds" in window.home_summary.text()
    assert window.reveal.text() == "Training"
    window.language_choice.setCurrentIndex(window.language_choice.findData("fr"))
    assert window.repo.settings()["language"] == "fr"
    assert "Réussite en entraînement" in window.home_summary.text()
    assert window.reveal.text() == "Training"


def test_sound_dialog_and_errors_use_french(french_window, monkeypatch):
    from src.ui import main_window
    messages = []
    monkeypatch.setattr(main_window.QMessageBox, "warning", lambda parent, title, text: messages.append((title, text)))
    dialog = SoundDialog(french_window, french_window.repo)
    assert dialog.windowTitle() == "Ajouter un son"
    assert dialog.offset.suffix() == " secondes"
    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons.button(QDialogButtonBox.StandardButton.Save).text() == "Enregistrer"
    assert buttons.button(QDialogButtonBox.StandardButton.Cancel).text() == "Annuler"
    dialog.accept()
    assert messages == [("Informations manquantes", "Un nom affiché et un fichier MP3 sont obligatoires.")]
    dialog.close()
    assert translated_error(ValueError("Sound 2 offset must be between 0 and 3600 seconds."), "fr") == "Le décalage du son 2 doit être compris entre 0 et 3600 secondes."


def test_exam_feedback_and_persisted_outcomes_are_localized(french_window, monkeypatch):
    from src.ui import main_window
    window = french_window
    sound_id = window.repo.save_sound("Robin", "robin.mp3", 0, True, None, [])
    sound = window.repo.sound(sound_id)
    window.exam = {"questions": [sound], "index": 0, "answers": [], "difficulty": 2, "reveal": True, "started": "2026-01-01T00:00:00+00:00"}
    messages = []
    monkeypatch.setattr(main_window.QMessageBox, "information", lambda parent, title, text: messages.append((title, text)))
    window.submit_answer("Wrong")
    assert messages[0][0] == "Réponse enregistrée"
    assert messages[0][1].startswith("Réponse attendue : Robin\nIncorrecte")
    assert window.results.item(0, 4).text() == "Incorrecte"
    assert "réponses correctes" in window.result_score.text()
    assert "Durée" in window.result_detail.text()
    assert window.repo.exam_answers(window.last_exam_id)[0]["result"] == "incorrect"
    window.language_choice.setCurrentIndex(window.language_choice.findData("en"))
    assert window.results.item(0, 4).text() == "Incorrect"
    assert "correct answers" in window.result_score.text()


def test_startup_maximizes_without_fullscreen(monkeypatch):
    import app as entrypoint
    window = Mock()
    monkeypatch.setattr(entrypoint, "MainWindow", lambda repo: window)
    monkeypatch.setattr(entrypoint, "Repository", Mock())
    qt_app = Mock()
    qt_app.exec.return_value = 0
    monkeypatch.setattr(entrypoint, "QApplication", lambda argv: qt_app)
    monkeypatch.setattr(entrypoint.sys, "argv", ["app.py"])
    assert entrypoint.main() == 0
    window.showMaximized.assert_called_once()
    window.showFullScreen.assert_not_called()


def test_window_can_restore_and_resize(french_window):
    window = french_window
    window.showMaximized()
    QApplication.processEvents()
    assert window.isMaximized() and not window.isFullScreen()
    window.showNormal()
    window.resize(1100, 750)
    QApplication.processEvents()
    assert not window.isMaximized()
    assert window.width() == 1100
