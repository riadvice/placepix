#!/usr/bin/env bash
# One-liner Docker runner for PlacePix.
# Usage: ./docker-run.sh [build]
#   build   Force rebuild the image before running

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="placepix:latest"
PORT="${PORT:-3000}"

# Build if requested or image does not exist
if [[ "${1:-}" = "build" ]] || ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "[placepix] Building Docker image..."
    docker build -t "$IMAGE_NAME" --build-arg PORT="$PORT" .
fi

echo "[placepix] Starting container on http://localhost:$PORT"
echo "[placepix] Mounting $(pwd)/images into container"
echo "[placepix] Press Ctrl+C to stop"

exec docker run --rm \
    --name placepix \
    -p "$PORT:$PORT" \
    -v "$(pwd)/images:/app/images" \
    -v "$(pwd)/.cache:/app/.cache" \
    -v "$(pwd)/data:/app/data" \
    -e DATA_DIR=/app/data \
    -e IMAGES_DIR=/app/images \
    -e CACHE=true \
    -e PORT="$PORT" \
    -e HOST="0.0.0.0:$PORT" \
    "$IMAGE_NAME"
