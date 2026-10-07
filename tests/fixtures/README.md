# Synthetic audio fixture

`tone.mp3` is a generated 440 Hz sine wave, 1.6 seconds long. It contains no personal recording or third-party sound and is covered by the project's MIT license.

Generated with:

```bash
ffmpeg -f lavfi -i sine=frequency=440:sample_rate=44100 -t 1.6 -codec:a libmp3lame -b:a 32k tone.mp3
```

Integration checks use Qt's real MP3 decoder and capture decoded audio buffers with the output muted. They do not prove audible output through physical speakers.
