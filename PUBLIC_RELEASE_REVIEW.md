# Public release review — 2026-10-07

## Verdict

Suitable for a public source preview after this PR passes CI. A stable binary release is not yet validated.

GitHub was already public at review time. Its default branch was `devops`; `main` existed locally at the initial README commit but was absent remotely. This PR establishes `main` as the integration target without merging or changing the default branch automatically.

## Review and changes

- Reviewed the tracked source and all 35 historical Git blobs for private keys, common GitHub/AWS token patterns, assigned secrets, audio and database files. No matches found. This targeted scan is not a guarantee that every possible secret format is absent.
- The application is a local PySide6 desktop app, not a public web service. No application HTTP listener, telemetry, cloud account or outbound API client was found. Dependencies are downloaded during installation.
- SQL values use bound parameters. JSON import uses parsing rather than code execution; audio is passed as a local-file URL.
- Added the MIT license selected by the owner and excluded common local database, audio and environment files from future commits.
- Validated complete JSON libraries before writing; imports now merge by path in one transaction and retain existing IDs/history. Duplicate manual additions are skipped; duplicate edits and file I/O failures produce a message.
- Preserved completed exam review by rejecting deletion of referenced sounds with guidance to disable them.
- Windows installers now fail on native command errors rather than reporting success after failed dependency installation.
- Direct playback clears stale queues; queued playback advances while retaining remaining clips.
- Multiple-choice answers are assessed by selected sound ID, without the free-text typo tolerance accepting a wrong option.
- Free-text submission reads the typed answer rather than passing the button's boolean signal argument into answer matching.
- Included the application SVG in the desktop package.
- Raised pytest to `>=9.0.3,<10` after pip-audit reported PYSEC-2026-1845 for 8.4.2. Advisory: https://github.com/pypa/advisory-database/blob/main/vulns/pytest/PYSEC-2026-1845.yaml
- Added Windows/macOS CI on Python 3.11 and 3.13, including fresh-workspace navigation and regression tests.

## Local evidence

- Windows / Python 3.12: `python -m pytest -q` — 23 passed.
- Installed environment: `python -m pip_audit --local --progress-spinner off` — no known vulnerabilities found after updating pytest. This covers the installed versions, not every version allowed by the dependency ranges or native libraries embedded in Qt.
- Fresh database: all seven application pages opened through a Qt offscreen test. This verifies application construction/navigation, not visual layout or real audio output.
- Git whitespace check passed.

## Before a stable release

1. Confirm the PR's Windows/macOS CI matrix is green; test actual MP3 playback, offsets, queue interruption, training, both exam levels and review on both operating systems.
2. Validate first-time install and launch on clean machines without a development environment, including offline relaunch and failed downloads.
3. Test packaged application launch/audio on each target OS. A Windows build alone does not prove macOS packaging works.
4. Prepare dependency license notices and applicable Qt/FFmpeg source information before sharing executables. MIT covers this project's code; third-party terms remain separate. Reference: https://doc.qt.io/qt-6/licensing.html
5. Confirm that any distributed recordings can be shared. JSON exports include local absolute paths and should be reviewed before publication.
6. Review French coverage: dynamic messages and some controls still use English. Also avoid identical display names in multiple-choice exams, as visually identical options remain confusing even though scoring uses distinct IDs.

After merging, `main` can be made the default branch through repository settings. No production deployment or public binary upload is part of this PR.
