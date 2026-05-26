#!/usr/bin/env bash
# PlacePix Development Setup Script
# Self-contained single-file script for easy dev environment setup
# Idempotent: safe to re-run

set -Eeuo pipefail

# ─── Colours ────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  C_RESET="\033[0m"; C_BOLD="\033[1m"
  C_RED="\033[31m"; C_GREEN="\033[32m"; C_YELLOW="\033[33m"; C_BLUE="\033[34m"
else
  C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""
fi

log()   { printf "${C_BLUE}${C_BOLD}[placepix]${C_RESET} %s\n" "$*"; }
ok()    { printf "${C_GREEN}${C_BOLD}[ ok ]${C_RESET} %s\n" "$*"; }
warn()  { printf "${C_YELLOW}${C_BOLD}[warn]${C_RESET} %s\n" "$*"; }
err()   { printf "${C_RED}${C_BOLD}[err ]${C_RESET} %s\n" "$*" 1>&2; }
die()   { err "$*"; exit 1; }

# ─── Guards ─────────────────────────────────────────────────────────
require_ubuntu() {
  if ! command -v lsb_release >/dev/null 2>&1; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y lsb-release
  fi
  local id; id="$(lsb_release -is)"
  [[ "$id" == "Ubuntu" ]] || die "This script targets Ubuntu (got: $id)"
  local rel; rel="$(lsb_release -rs)"
  log "Detected Ubuntu $rel ($(lsb_release -cs))"
}

# ─── Idempotency helpers ────────────────────────────────────────────
apt_install() {
  local pkgs=("$@")
  local missing=()
  for p in "${pkgs[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    log "Installing: ${missing[*]}"
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"
  else
    ok "Already installed: ${pkgs[*]}"
  fi
}

ensure_line() {
  local line="$1" file="$2"
  grep -qsxF "$line" "$file" 2>/dev/null || echo "$line" >> "$file"
}

# Safely replace content between comment markers
replace_section() {
  local marker="$1" file="$2" content="$3"
  local start_marker="# BEGIN placepix: $marker"
  local end_marker="# END placepix: $marker"
  
  if grep -q "$start_marker" "$file"; then
    # Replace existing section
    sed -i "/$start_marker/,/$end_marker/{ /$start_marker/{ p; r /dev/stdin
d }; /$end_marker/!d; }" "$file" <<< "$content"
  else
    # Append new section
    echo -e "\n$start_marker\n$content\n$end_marker" >> "$file"
  fi
}

# ─── Main Setup ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$SCRIPT_DIR"
VENV_DIR="$ROOT_DIR/venv"

# Python version from pyproject.toml (requires-python >= 3.10)
PYTHON_VERSION="${PYTHON_VERSION:-3.12.7}"

log "Setting up PlacePix development environment"
require_ubuntu

log "Installing system dependencies"
sudo apt-get update -y
apt_install python3 python3-pip python3-venv \
            build-essential libssl-dev zlib1g-dev libbz2-dev \
            libreadline-dev libsqlite3-dev wget curl llvm \
            libncurses-dev xz-utils tk-dev libffi-dev liblzma-dev \
            python3-openssl git ca-certificates libwebp-dev imagemagick

# Check if we have a suitable Python version
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_VER=$("$cmd" --version 2>/dev/null | awk '{print $2}')
    PYTHON_MAJOR=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$PYTHON_MAJOR >= 3.10" | bc -l) -eq 1 ]]; then
      PYTHON_CMD="$cmd"
      log "Found suitable Python: $PYTHON_CMD (version $PYTHON_VER)"
      break
    fi
  fi
done

if [[ -z "$PYTHON_CMD" ]]; then
  warn "No suitable Python 3.10+ found in PATH"
  log "Installing pyenv to manage Python versions"
  
  export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
  if [[ ! -d "$PYENV_ROOT" ]]; then
    curl -fsSL https://pyenv.run | bash
  fi
  
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  
  if ! pyenv versions --bare | grep -qx "$PYTHON_VERSION"; then
    log "Installing Python $PYTHON_VERSION via pyenv (this can take a few minutes)"
    pyenv install "$PYTHON_VERSION"
  fi
  
  pyenv global "$PYTHON_VERSION"
  PYTHON_CMD="$PYENV_ROOT/versions/$PYTHON_VERSION/bin/python3"
  
  # Add pyenv to shell
  PYENV_CONTENT='export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash 2>/dev/null || pyenv init -)"'
  for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    [[ -f "$rc" ]] || continue
    replace_section "pyenv" "$rc" "$PYENV_CONTENT"
  done
fi

# Create or update venv
if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating Python venv at $VENV_DIR"
  "$PYTHON_CMD" -m venv "$VENV_DIR"
else
  ok "Venv already exists at $VENV_DIR"
fi

# Activate venv and install dependencies
log "Installing/updating dependencies"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install uv

# Use uv to install project dependencies
log "Installing project dependencies with uv"
"$VENV_DIR/bin/uv" pip install -e "$ROOT_DIR[dev]"

# Add venv activation to shell
log "Adding venv activation to shell configs"
VENV_CONTENT="source $VENV_DIR/bin/activate"
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [[ -f "$rc" ]] || continue
  replace_section "venv" "$rc" "$VENV_CONTENT"
done

ok "Development environment setup complete!"
log "To activate the venv, run: source $VENV_DIR/bin/activate"
log "Or start a new shell session (venv auto-activates)"
log ""
log "To run the dev server:"
log "  cd $ROOT_DIR"
log "  placepix"
