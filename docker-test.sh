#!/usr/bin/env bash
set -euo pipefail

GIT_VERSION=$(git describe --tags --always 2>/dev/null || echo "dev")

echo "[placepix] Building test image (version: $GIT_VERSION)..."
docker build --target test -t placepix:test --build-arg GIT_VERSION="$GIT_VERSION" .

echo "[placepix] Running tests in Docker..."
exec docker run --rm placepix:test "$@"
