#!/usr/bin/env bash
# Format and lint script for PlacePix following DeepSource style rules

set -e

echo "🎨 PlacePix Code Formatter"
echo "========================"

# Source venv if exists
VENV_DIR="$(pwd)/.venv"
if [[ -d "$VENV_DIR" ]]; then
  echo "🐍 Activating local venv at $VENV_DIR"
  source "$VENV_DIR/bin/activate"
fi

# Ensure ruff is installed
if ! command -v ruff &> /dev/null; then
    echo "📦 Installing ruff..."
    uv pip install ruff
fi

echo ""
echo "🔍 Running ruff check (lint)..."
ruff check src/ tests/ --fix

echo ""
echo "✨ Running ruff format..."
ruff format src/ tests/

echo ""
echo "🎉 Formatting complete!"
