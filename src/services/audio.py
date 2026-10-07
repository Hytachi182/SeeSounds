from __future__ import annotations

from pathlib import Path
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
        self.player.mediaStatusChanged.connect(self._seek_when_ready)

    def play(self, sound: Sound, global_offset: float = 0.0) -> None:
        self.player.stop()
        self._offset_ms = round(effective_start_offset(sound, global_offset) * 1000)
        self.player.setSource(QUrl.fromLocalFile(str(Path(sound.filepath).resolve())))
        self.player.play()

    def _seek_when_ready(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.player.setPosition(self._offset_ms)

    def pause_or_resume(self) -> None:
        self.player.pause() if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState else self.player.play()

    def stop(self) -> None:
        self.player.stop()
