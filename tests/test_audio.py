from src.models import Sound
from src.services.audio import effective_start_offset
from src.services.audio import AudioPlayer
from PySide6.QtMultimedia import QMediaPlayer
from unittest.mock import Mock


def test_global_start_offset_skips_every_sound_to_the_requested_second() -> None:
    sound = Sound(1, "Robin", __import__("pathlib").Path("robin.mp3"), start_offset=2.5)
    assert effective_start_offset(sound, 10.0) == 10.0


def test_later_sound_specific_offset_is_not_lost() -> None:
    sound = Sound(1, "Robin", __import__("pathlib").Path("robin.mp3"), start_offset=12.0)
    assert effective_start_offset(sound, 10.0) == 12.0


def test_direct_play_discards_old_queue():
    audio = AudioPlayer.__new__(AudioPlayer)
    audio._queue = [Mock()]
    audio._play = Mock()
    sound = Mock()
    audio.play(sound, 3.0)
    assert audio._queue == []
    audio._seek_when_ready(QMediaPlayer.MediaStatus.EndOfMedia)
    audio._play.assert_called_once_with(sound, 3.0)


def test_queue_advances_without_discarding_remaining_sounds():
    audio = AudioPlayer.__new__(AudioPlayer)
    audio.player = Mock()
    audio._play = Mock()
    sounds = [Mock(), Mock(), Mock()]
    audio.play_queue(sounds, 4.0)
    assert audio._queue == sounds[1:]
    audio._seek_when_ready(QMediaPlayer.MediaStatus.EndOfMedia)
    assert audio._queue == sounds[2:]
    audio._play.assert_called_with(sounds[1], 4.0)
