from __future__ import annotations

from pathlib import Path
import random
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from src.models import Sound


def effective_start_offset(sound: Sound, global_offset: float = 0.0) -> float:
    """Keep per-sound skips while applying a minimum start time to a listening session."""
    return max(0.0, sound.start_offset, global_offset)


class AudioPlayer:
    """One player instance guarantees that clips never overlap."""
    def __init__(self, volume: int = 70) -> None:
        self.output = QAudioOutput()
        self.output.setVolume(max(0, min(volume, 100)) / 100)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.output)
        self._offset_ms = 0
        self._queue: list[Sound] = []
        self._queue_offset = 0.0
        self.player.mediaStatusChanged.connect(self._seek_when_ready)

    def play(self, sound: Sound, global_offset: float = 0.0) -> None:
        self._queue = []
        self._play(sound, global_offset)

    def _play(self, sound: Sound, global_offset: float = 0.0) -> None:
        self.player.stop()
        self._offset_ms = round(effective_start_offset(sound, global_offset) * 1000)
        self.player.setSource(QUrl.fromLocalFile(str(Path(sound.filepath).resolve())))
        self.player.play()

    def _seek_when_ready(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.player.setPosition(self._offset_ms)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia and self._queue:
            self._play(self._queue.pop(0), self._queue_offset)

    def play_queue(self, sounds: list[Sound], global_offset: float = 0.0, shuffle: bool = False) -> None:
        self.stop()
        self._queue = list(sounds)
        if shuffle: random.shuffle(self._queue)
        self._queue_offset = global_offset
        if self._queue: self._play(self._queue.pop(0), global_offset)

    def pause_or_resume(self) -> None:
        self.player.pause() if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState else self.player.play()

    def stop(self) -> None:
        self._queue = []
        self.player.stop()
