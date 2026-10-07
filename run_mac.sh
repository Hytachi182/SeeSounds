#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Preparing Sound Recognition Trainer for its first launch..."
  bash "$SCRIPT_DIR/install_mac.sh"
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/app.py"
