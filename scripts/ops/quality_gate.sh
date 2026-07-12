#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_DIR"
"$PYTHON_BIN" scripts/quality_gate.py "$@"
