from src.models import Sound
from src.services.audio import effective_start_offset


def test_global_start_offset_skips_every_sound_to_the_requested_second() -> None:
    sound = Sound(1, "Robin", __import__("pathlib").Path("robin.mp3"), start_offset=2.5)
    assert effective_start_offset(sound, 10.0) == 10.0


def test_later_sound_specific_offset_is_not_lost() -> None:
    sound = Sound(1, "Robin", __import__("pathlib").Path("robin.mp3"), start_offset=12.0)
    assert effective_start_offset(sound, 10.0) == 12.0
