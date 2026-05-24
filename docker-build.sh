#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="placepix:latest"
GIT_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")

echo "[placepix] Building Docker image (version: $GIT_VERSION)..."
docker build -t "$IMAGE_NAME" . --no-cache --build-arg GIT_VERSION="$GIT_VERSION"

echo "[placepix] Pushing Docker image..."
docker push "$IMAGE_NAME"

echo "[placepix] Done"
