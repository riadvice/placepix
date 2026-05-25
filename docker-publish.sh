#!/usr/bin/env bash
set -euo pipefail

# Configuration
HUB_REPO="riadvice/placepix"
IMAGE_NAME="$HUB_REPO"

# Get current commit SHA
CURRENT_COMMIT=$(git rev-parse HEAD)

# Get the exact tag for the current commit (if any)
EXACT_TAG=$(git tag --points-at HEAD 2>/dev/null | head -n 1)

# Determine the version tag to use
if [ -n "$EXACT_TAG" ]; then
    # Current commit is exactly on a tag, use it
    VERSION_TAG="$EXACT_TAG"
    echo "[placepix] Current commit is on tag: $VERSION_TAG"
else
    # Not on a tag, use git describe to generate a version
    # This will output something like v1.2.3-4-gabcdef if there are commits after the last tag
    # or just the tag if we're exactly on it (but we already checked that case)
    DESCRIBE=$(git describe --tags --always 2>/dev/null || echo "dev")
    
    # If the describe output doesn't start with 'v', prepend it for consistency
    if [[ ! "$DESCRIBE" =~ ^v[0-9] ]]; then
        VERSION_TAG="$DESCRIBE"
    else
        VERSION_TAG="$DESCRIBE"
    fi
    
    echo "[placepix] Current commit is not on a tag, using: $VERSION_TAG"
fi

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
