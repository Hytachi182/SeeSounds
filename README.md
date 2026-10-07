<p align="center">
  <img src="assets/sound-recognition-trainer.svg" width="112" alt="Sound Recognition Trainer icon">
</p>

<h1 align="center">Sound Recognition Trainer</h1>

<p align="center"><strong>English</strong> · <a href="README.fr.md">Français</a></p>

<p align="center">
  Learn the sound. Trust the answer.<br>
  A focused, offline desktop application for serious MP3 sound-recognition practice.
</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/hytachi182"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-support%20the%20project-FFDD00?style=flat-square&logo=buymeacoffee&logoColor=black" alt="Buy Michael a coffee"></a>
</p>

<p align="center">
  <a href="https://github.com/Hytachi182/SeeSounds"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-167277?style=flat-square" alt="Windows and macOS"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-102D38?style=flat-square&logo=python&logoColor=white" alt="Python 3.11 or later">
  <img src="https://img.shields.io/badge/data-local%20SQLite-167277?style=flat-square&logo=sqlite&logoColor=white" alt="Local SQLite data">
  <img src="https://img.shields.io/badge/cloud-not%20required-102D38?style=flat-square" alt="No cloud required">
</p>

<p align="center">
  <a href="#get-started">Get started</a> ·
  <a href="#features">Features</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#develop">Develop</a> ·
  <a href="https://github.com/Hytachi182/SeeSounds/issues">Report an issue</a>
</p>

---

## Get started

Sound Recognition Trainer turns a personal MP3 collection into deliberate practice and clear exam evidence. Everything stays on your computer: audio files are read in place, while the library, scores, settings, and exam history live in a local SQLite database.

| Platform | Recommended path | Start here |
| --- | --- | --- |
| **Windows** | PowerShell | Run the installer script, then the launcher. |
| **macOS** | Terminal | Launch one script; it installs dependencies when needed. |

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
.\run_windows.ps1
```

### macOS

```bash
bash run_mac.sh
```

The first launch creates `.venv`, installs the dependencies, validates them, then opens the app. Later launches open the app directly. Set `PYTHON` when a specific Python 3.11+ executable is needed, for example `PYTHON=python3.12 bash run_mac.sh`.

Requirements: **Python 3.11 or later**. Audio playback uses the Qt multimedia backend bundled with PySide6; make sure your operating system can play the target MP3 files.

> Your local workspace is stored in `~/.sound-recognition-trainer/`, including `sound_trainer.db`. The original MP3 files are never modified.

## Features

| Available today | What it does |
| --- | --- |
| **MP3 library** | Import several files, search by name or category, edit display names, enable or pause sounds, and manage categories. |
| **Playback offsets** | Start each sound after a spoken introduction without editing its MP3 file. |
| **Aliases** | Accept alternate names for a sound during free-text exams. |
| **Focused training** | Listen, replay, reveal the answer, and record whether you were correct—without a timer or penalty. |
| **Difficult-sound priority** | Give sounds with weaker training results more practice time. |
| **Two exam levels** | Level 1 uses five shuffled choices. Level 2 accepts free-text answers. |
| **Forgiving answer matching** | Ignores casing, extra spaces, accents, and simple punctuation; configurable thresholds handle minor typos. |
| **Reviewable results** | See every answer, similarity score, outcome, and replay the sounds that need another pass. |
| **Local statistics** | Track attempts, success rate, per-sound history, and recent exams. |
| **Library portability** | Export and import library metadata as JSON; missing audio paths are reported after import. |

## How it works

1. In **Sound Library**, choose **Add MP3 files**. Names initially come from the file names and can be changed later.
2. Optionally set a **Start playback at** offset (for example, `4.0` or `5.25` seconds), categories, and comma-separated aliases.
3. In **Training**, select a category if useful, play a sound, reveal it when ready, then record whether you knew it.
4. In **Exam**, choose a question count, a level, and whether repetitions are allowed. The app checks the library before the exam begins.
5. Review the result, replay missed sounds, and use **Statistics** to decide what to practise next.

<details>
<summary><strong>Exam rules and answer assessment</strong></summary>

<br>

- **Level 1 — Multiple choice:** requires at least five enabled sounds and presents one correct choice plus four alternatives.
- **Level 2 — Free text:** accepts the main sound name or any configured alias.
- With repetitions disabled, an exam cannot request more questions than the number of enabled sounds.
- By default, an answer scores **correct** from 90% similarity and **almost correct** from 75%. Both thresholds are adjustable in **Settings**.
- Every typed answer, normalized answer, similarity score, and outcome is retained locally with the exam.

</details>

<details>
<summary><strong>Privacy and data</strong></summary>

<br>

No account or cloud service is needed. After setup, the application works without a network connection. The database contains library metadata, aliases, training outcomes, exam results, and settings. It stores paths to your MP3 files; it does not alter or copy the source audio.

</details>

## Develop

Clone the repository, create the virtual environment with the matching platform script, and run the test suite:

```bash
git clone https://github.com/Hytachi182/SeeSounds.git
cd SeeSounds
```

```powershell
# Windows
.\.venv\Scripts\python.exe -m pytest
```

```bash
# macOS
.venv/bin/python -m pytest
```

The tests cover answer normalization, accent removal, aliases, tolerant matching, unique exam selection, multiple-choice construction, difficult-sound weighting, and persisted exam review data.

### Build a desktop package

Build on each target operating system—do not cross-compile macOS on Windows, or the reverse:

```bash
.venv/bin/pyinstaller --noconfirm sound_recognition_trainer.spec
```

On Windows, use:

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm sound_recognition_trainer.spec
```

The generated application is placed in `dist/`.

### Project layout

| Area | Responsibility |
| --- | --- |
| `app.py` | Application composition, local workspace, and visual theme. |
| `src/database` | SQLite schema, persistence, import/export, and local statistics. |
| `src/models` | Sound data model. |
| `src/services` | Audio playback plus training and exam selection rules. |
| `src/utils` | Free-text normalization and answer matching. |
| `src/ui` | PySide6 desktop interface. |
| `tests` | Behavioural tests for the study and assessment rules. |

## Contribute

Have an improvement, a bug report, or a learning workflow to suggest? Please [open an issue](https://github.com/Hytachi182/SeeSounds/issues). Keep changes local-first, preserve source audio, and make assessment rules testable.

## Public preview and license

The source is available under the [MIT license](LICENSE). This is a public preview; real MP3 playback on macOS and standalone package distribution still require validation. See [the release review](PUBLIC_RELEASE_REVIEW.md) for checked items and remaining release work.

JSON imports merge by file path: existing sound metadata is updated while training and exam history is retained. Invalid libraries are rejected without partial writes. Sounds used in completed exams must be disabled rather than removed to preserve their review history.

Library exports include local file paths, names, categories and aliases. Review them before sharing. No audio is bundled: use recordings you are entitled to use or distribute.

Third-party dependencies retain their own licenses. PySide6/Qt offers LGPL/GPL and commercial licensing options; the application's MIT license does not replace those terms. Before distributing standalone executables, review [Qt licensing](https://doc.qt.io/qt-6/licensing.html) and ship the applicable license notices and required dependency source information.

## Creator

Designed and created by Michael Ruffenach.
