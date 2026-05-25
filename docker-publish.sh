#!/usr/bin/env bash
set -euo pipefail

# Configuration
HUB_REPO="riadvice/placepix"
IMAGE_NAME="$HUB_REPO"

# Get current commit SHA
CURRENT_COMMIT=$(git rev-parse HEAD)

# Get the exact tag for the current commit (if any)
EXACT_TAG=$(git tag --points-at HEAD 2>/dev/null | head -n 1)

# Only proceed if current commit is exactly on a tag
if [ -z "$EXACT_TAG" ]; then
    echo "[placepix] ERROR: Current commit is not on a git tag."
    echo "[placepix] Only tagged commits can be published to Docker Hub."
    echo "[placepix] Current commit: $CURRENT_COMMIT"
    echo "[placepix] Please create and push a tag first, e.g.:"
    echo "[placepix]   git tag v1.2.3"
    echo "[placepix]   git push origin v1.2.3"
    exit 1
fi

VERSION_TAG="$EXACT_TAG"
echo "[placepix] Current commit is on tag: $VERSION_TAG"

# Build the image
echo "[placepix] Building Docker image..."
docker build -t "$IMAGE_NAME:$VERSION_TAG" \
    -t "$IMAGE_NAME:latest" \
    . \
    --build-arg GIT_VERSION="$VERSION_TAG"

# Push the versioned tag
echo "[placepix] Pushing Docker image $IMAGE_NAME:$VERSION_TAG..."
docker push "$IMAGE_NAME:$VERSION_TAG"

# Push latest tag
echo "[placepix] Pushing Docker image $IMAGE_NAME:latest..."
docker push "$IMAGE_NAME:latest"

echo "[placepix] Done! Published as $IMAGE_NAME:$VERSION_TAG"
