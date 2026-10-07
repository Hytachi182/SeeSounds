#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON="${PYTHON:-python3}"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required. Install it from https://www.python.org/downloads/macos/ and run this script again." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  VERSION="$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "Python 3.11 or newer is required; found Python $VERSION." >&2
  exit 1
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  if [[ -e "$SCRIPT_DIR/.venv" ]]; then
    BACKUP_PATH="$SCRIPT_DIR/.venv.invalid-$(date +%Y%m%d-%H%M%S)"
    mv "$SCRIPT_DIR/.venv" "$BACKUP_PATH"
    echo "Existing incomplete virtual environment moved to $(basename "$BACKUP_PATH")."
  fi
  echo "Creating a Python virtual environment..."
  "$PYTHON" -m venv "$SCRIPT_DIR/.venv"
fi

"$VENV_PYTHON" -m pip install --disable-pip-version-check --upgrade pip
"$VENV_PYTHON" -m pip install --disable-pip-version-check -r "$SCRIPT_DIR/requirements.txt"
"$VENV_PYTHON" -c 'import PySide6, rapidfuzz; print("Dependencies validated.")'
echo "Installation complete. Start the application with: bash run_mac.sh"
