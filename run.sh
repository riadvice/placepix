#!/usr/bin/env bash
# Self-contained runner for PlacePic.
# Usage: ./run.sh [options]
# Creates .venv, installs deps, and starts the server.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# ─── Colours ────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  C_RESET="\033[0m"; C_BOLD="\033[1m"
  C_GREEN="\033[32m"; C_BLUE="\033[34m"; C_YELLOW="\033[33m"
else
  C_RESET=""; C_BOLD=""; C_GREEN=""; C_BLUE=""; C_YELLOW=""
fi

log()   { printf "${C_BLUE}${C_BOLD}[placepix]${C_RESET} %s\n" "$*"; }
ok()    { printf "${C_GREEN}${C_BOLD}[ ok ]${C_RESET} %s\n" "$*"; }
warn()  { printf "${C_YELLOW}${C_BOLD}[warn]${C_RESET} %s\n" "$*"; }

# ─── Create venv ────────────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# ─── Install / update deps ─────────────────────────────────────────
log "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -e "$SCRIPT_DIR"

# ─── Launch ─────────────────────────────────────────────────────────
ok "Dependencies ready"
log "Starting PlacePic server..."
log "API docs: http://127.0.0.1:3000/docs"
log "Web UI : http://127.0.0.1:3000/"
log ""
log "Press Ctrl+C to stop"

# Check if workers should be used (disable reload with workers)
# Read from .env if available, default to 2
if [[ -f ".env" ]]; then
  WORKERS=$(grep -E "^WORKERS=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ')
fi
# Default to 2 if not set or empty
WORKERS="${WORKERS:-2}"

# Ensure WORKERS is a number
if ! [[ "$WORKERS" =~ ^[0-9]+$ ]]; then
  WORKERS=2
fi

if [[ "$WORKERS" -gt 1 ]]; then
  log "Running with $WORKERS workers (reload disabled)"
  exec "$VENV_DIR/bin/python" -m uvicorn src.main:app --host 0.0.0.0 --port 3000 --workers "$WORKERS" "$@"
else
  log "Running with auto-reload (single worker)"
  exec "$VENV_DIR/bin/python" -m uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload --reload-dir src "$@"
fi
