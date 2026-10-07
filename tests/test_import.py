import json
import sqlite3

import pytest

from src.database import Repository


@pytest.fixture
def repo(tmp_path):
    repository = Repository(tmp_path / "test.db")
    yield repository
    repository.close()


def write_library(tmp_path, payload):
    path = tmp_path / "library.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize("bad_item", [None, {}, {"name": "Bird", "filepath": "bird.mp3", "start_offset": float("nan")}, {"name": "Bird", "filepath": "bird.mp3", "enabled": "false"}, {"name": "Bird", "filepath": "bird.mp3", "aliases": "bird"}])
def test_invalid_import_leaves_library_unchanged(repo, tmp_path, bad_item):
    source = write_library(tmp_path, [{"name": "First", "filepath": "first.mp3"}, bad_item])
    with pytest.raises(ValueError):
        repo.import_library(source)
    assert repo.sounds() == []


def test_reimport_updates_metadata_preserving_history(repo, tmp_path):
    sound_id = repo.save_sound("Bird", "bird.mp3", 0, True, None, [])
    repo.record_training(sound_id, True)
    source = write_library(tmp_path, [{"name": "Robin", "filepath": "bird.mp3", "aliases": ["Bird"]}])
    assert repo.import_library(source) == ["bird.mp3"]
    repo.import_library(source)
    assert len(repo.sounds()) == 1
    assert repo.sound(sound_id).name == "Robin"
    assert repo.aliases(sound_id) == ["Bird"]
    assert repo.statistics()["attempts"] == 1


def test_failed_save_rolls_back_sound_and_aliases(repo):
    sound_id = repo.save_sound("Bird", "bird.mp3", 0, True, None, ["Robin"])
    with pytest.raises(AttributeError):
        repo.save_sound("Changed", "bird.mp3", 0, True, None, [None], sound_id)
    assert repo.sound(sound_id).name == "Bird"
    assert repo.aliases(sound_id) == ["Robin"]


def test_exam_sound_removal_preserves_review(repo):
    sound_id = repo.save_sound("Bird", "bird.mp3", 0, True, None, [])
    exam_id = repo.record_exam(2, "2026-01-01T00:00:00+00:00", [{"sound": repo.sound(sound_id), "result": "correct"}])
    with pytest.raises(ValueError, match="Disable"):
        repo.delete_sound(sound_id)
    assert repo.exam_answers(exam_id)[0]["expected_answer"] == "Bird"
    assert not repo.connection.in_transaction
