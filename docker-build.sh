#!/usr/bin/env bash
# Build the PlacePix production image locally.
#
# This does NOT push: releases are built and pushed by CI on tag
# (.github/workflows/publish.yml). For a manual publish use ./docker-publish.sh.
#
# Usage: ./docker-build.sh [TAG]
#   TAG  Image tag to build (default: placepix:latest)

set -euo pipefail

IMAGE_NAME="${1:-placepix:latest}"
GIT_VERSION=$(git describe --tags --always 2>/dev/null || echo "dev")
PORT="${PORT:-3000}"

echo "[placepix] Building $IMAGE_NAME (version: $GIT_VERSION, port: $PORT)..."
docker build \
    --target production \
    --build-arg GIT_VERSION="$GIT_VERSION" \
    --build-arg PORT="$PORT" \
    -t "$IMAGE_NAME" \
    .

echo "[placepix] Done: $IMAGE_NAME"
