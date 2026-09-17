#!/usr/bin/env bash
set -euo pipefail

# Manual publish to Docker Hub.
#
# The normal path is CI: pushing a tag triggers .github/workflows/publish.yml,
# which tests the image and pushes it. Use this script only when you need to
# publish from a workstation.

# Configuration
HUB_REPO="riadvice/placepix"
IMAGE_NAME="$HUB_REPO"

# Usage helper
usage() {
    echo "Usage: $0 [TAG]"
    echo "  TAG  Optional git tag to publish (e.g. 0.2)."
    echo "       If omitted, the tag on the current HEAD is used."
    exit 1
}

# Optional: handle --help
if [[ "${1:-}" = "--help" || "${1:-}" = "-h" ]]; then
    usage
fi

# ------------------------------------------------------------------
# Resolve the tag to publish
# ------------------------------------------------------------------
if [[ -n "${1:-}" ]]; then
    # User provided an explicit tag
    VERSION_TAG="$1"
    if ! git rev-parse "refs/tags/$VERSION_TAG" >/dev/null 2>&1; then
        echo "[placepix] ERROR: Tag '$VERSION_TAG' does not exist in this repo."
        echo "[placepix] Available tags:"
        git tag --sort=-v:refname | sed 's/^/  /'
        exit 1
    fi
    HEAD_SHA=$(git rev-parse HEAD)
    TAG_SHA=$(git rev-parse "refs/tags/$VERSION_TAG^{commit}")
    if [[ "$HEAD_SHA" != "$TAG_SHA" ]]; then
        echo "[placepix] ERROR: HEAD is not at tag '$VERSION_TAG'."
        echo "[placepix] The image is built from the working tree, so this would"
        echo "[placepix] publish '$VERSION_TAG' with the wrong code."
        echo "[placepix]   git checkout $VERSION_TAG"
        exit 1
    fi
    echo "[placepix] Publishing explicit tag: $VERSION_TAG"
else
    # Auto-detect tag on current HEAD; sort by version so 0.2 beats 0.1
    EXACT_TAG=$(git tag --points-at HEAD 2>/dev/null | sort -V | tail -n 1)
    if [[ -z "$EXACT_TAG" ]]; then
        CURRENT_COMMIT=$(git rev-parse --short HEAD)
        echo "[placepix] ERROR: Current commit ($CURRENT_COMMIT) is not on a git tag."
        echo "[placepix] Only tagged commits can be auto-published."
        echo "[placepix] You can still publish a specific tag manually:"
        echo "[placepix]   $0 0.2"
        exit 1
    fi
    VERSION_TAG="$EXACT_TAG"
    echo "[placepix] Auto-detected tag on HEAD: $VERSION_TAG"
fi

# ------------------------------------------------------------------
# Verify Docker Hub login
# ------------------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
    echo "[placepix] ERROR: Docker daemon is not running or you are not logged in."
    exit 1
fi

# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------
# Only move :latest when this is the newest release, so publishing a hotfix
# for an older line cannot roll production back.
HIGHEST_TAG=$(git tag --list '[0-9]*' | sort -V | tail -n 1)
BUILD_TAGS=(-t "$IMAGE_NAME:$VERSION_TAG")
PUSH_LATEST=false
if [[ "$VERSION_TAG" == "$HIGHEST_TAG" ]]; then
    BUILD_TAGS+=(-t "$IMAGE_NAME:latest")
    PUSH_LATEST=true
else
    echo "[placepix] $VERSION_TAG is not the highest tag ($HIGHEST_TAG); leaving :latest alone."
fi

echo "[placepix] Building Docker image $IMAGE_NAME:$VERSION_TAG ..."
docker build \
    --target production \
    --build-arg GIT_VERSION="$VERSION_TAG" \
    "${BUILD_TAGS[@]}" \
    .

# ------------------------------------------------------------------
# Push
# ------------------------------------------------------------------
echo "[placepix] Pushing $IMAGE_NAME:$VERSION_TAG ..."
docker push "$IMAGE_NAME:$VERSION_TAG"

if [[ "$PUSH_LATEST" == true ]]; then
    echo "[placepix] Pushing $IMAGE_NAME:latest ..."
    docker push "$IMAGE_NAME:latest"
    echo "[placepix] Done! $VERSION_TAG is now the 'latest' on Docker Hub."
else
    echo "[placepix] Done! $VERSION_TAG published; 'latest' still points at $HIGHEST_TAG."
fi
