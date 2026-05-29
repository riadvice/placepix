#!/usr/bin/env bash
# One-liner Docker runner for PlacePix.
# Usage: ./docker-run.sh [build]
#   build   Force rebuild the image before running

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="placepix:latest"

# Build if requested or image does not exist
if [[ "${1:-}" = "build" ]] || ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "[placepix] Building Docker image..."
    docker build -t "$IMAGE_NAME" .
fi

echo "[placepix] Starting container on http://localhost:3000"
echo "[placepix] Mounting $(pwd)/images into container"
echo "[placepix] Press Ctrl+C to stop"

exec docker run --rm \
    --name placepix \
    -p 3000:3000 \
    -v "$(pwd)/images:/app/images" \
    -v "$(pwd)/.cache:/app/.cache" \
    -v "$(pwd)/data:/app/data" \
    -e DATA_DIR=/app/data \
    -e IMAGES_DIR=/app/images \
    -e CACHE=true \
    -e HOST=0.0.0.0:3000 \
    "$IMAGE_NAME"
