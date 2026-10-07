import random
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from src.database import Repository
from src.models import Sound
from src.services.selection import exam_questions, multiple_choice_options, training_choice


def sounds(count: int = 5) -> list[Sound]:
    return [Sound(i, f"Sound {i}", __import__("pathlib").Path(f"{i}.mp3")) for i in range(count)]


def test_exam_without_repeats_is_unique() -> None:
    result = exam_questions(sounds(), 5, False, random.Random(1))
    assert len({sound.id for sound in result}) == 5


def test_exam_rejects_insufficient_unique_sounds() -> None:
    with pytest.raises(ValueError): exam_questions(sounds(2), 3, False)


def test_multiple_choice_has_one_correct_and_five_options() -> None:
    options = multiple_choice_options(sounds()[0], sounds(), random.Random(2))
    assert len(options) == 5 and sum(s.id == 0 for s in options) == 1


def test_difficult_sound_has_more_weight() -> None:
    sample = [training_choice(sounds(2), {0: 0.0, 1: 1.0}, True, random.Random(seed)).id for seed in range(100)]
    assert sample.count(0) > sample.count(1)


def test_exam_answer_review_is_persisted_with_sound_metadata() -> None:
    with TemporaryDirectory() as folder:
        repo = Repository(Path(folder) / "trainer.db")
        sound_id = repo.save_sound("Robin", "robin.mp3", 2.5, True, "Birds", [])
        sound = repo.sound(sound_id)
        exam_id = repo.record_exam(2, "2026-01-01T10:00:00+00:00", [{"sound": sound, "answer": "robin", "normalized": "robin", "similarity": 100, "result": "correct"}])
        review = repo.exam_answers(exam_id)
        assert review[0]["expected_answer"] == "Robin"
        assert review[0]["start_offset"] == 2.5
        repo.close()
