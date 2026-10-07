# Sound Recognition Trainer

A private, offline desktop application for learning to identify sounds stored as MP3 files. It runs on Windows and macOS, keeps its SQLite database on the local computer, and never edits source audio.

## What it includes

- Sound library with multi-file import, search, categories, aliases, activation, editing and JSON metadata import/export.
- Per-sound playback offset: use it to skip a spoken introduction without modifying the MP3.
- Pressure-free training with replay, reveal, per-sound results and optional difficult-sound prioritisation.
- Exam level 1 (five shuffled choices) and level 2 (forgiving free text).
- Offline statistics, exam history and locally saved settings.

## Requirements

Python 3.11+ is required. Audio playback uses the Qt multimedia backend supplied by PySide6. On a particular machine, make sure the operating system can play the relevant MP3 file first.

## Install and run

### Windows

Open PowerShell in this folder, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
.\run_windows.ps1
```

### macOS

In Terminal:

```bash
chmod +x install_mac.sh run_mac.sh
./install_mac.sh
./run_mac.sh
```

The app database is stored at `~/.sound-recognition-trainer/sound_trainer.db` (or the equivalent Windows user directory).

## Using the app

1. Open **Sound Library** and choose **Add MP3 files**. Display names initially come from file names and can be edited later.
2. Set **Start playback at** to a decimal number of seconds, for example `4.0` or `5.25`. Training and exams begin there; the original MP3 remains unchanged.
3. Add alternative accepted names in **Aliases**, separated by commas. They are used by free-text exams.
4. In **Training**, select a category if needed, play a sound, reveal it, and record whether you were correct.
5. In **Exam**, select a question count, level and repetition rule. Level 1 needs at least five enabled sounds. The app explains if a no-repeat exam requests too many questions.

Free-text answers ignore case, surrounding/duplicate spaces, accents and simple punctuation. The default score thresholds are 90% for correct and 75% for almost correct; change them in **Settings**. Every typed answer, normalized answer, score and outcome is stored locally.

## Tests

After installation, run:

```bash
.venv/bin/python -m pytest
```

On Windows use:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests cover normalization, accent removal, aliases, tolerant matching, exam duplicate prevention, multiple-choice construction and weighted training selection.

## Packaging

Build independently on each target operating system—do not cross-compile macOS on Windows or the reverse:

```bash
.venv/bin/pyinstaller --noconfirm sound_recognition_trainer.spec
```

On Windows replace `.venv/bin/pyinstaller` with `.\.venv\Scripts\pyinstaller.exe`. The packaged program will be in `dist/`.

## Development layout

`src/database` owns SQLite persistence; `src/services` owns audio and question selection; `src/utils` owns answer matching; `src/ui` owns PySide6 widgets. This separation keeps the critical exam rules testable without a GUI.

# SeeSounds
