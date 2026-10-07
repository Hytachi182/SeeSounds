#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]] || ! "$VENV_PYTHON" -c 'import sys, PySide6, rapidfuzz; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
  echo "Preparing or repairing Sound Recognition Trainer..."
  bash "$SCRIPT_DIR/install_mac.sh"
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/app.py" "$@"
