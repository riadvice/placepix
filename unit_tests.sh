#!/bin/bash

# Test runner script for PlacePix
# Sets up test environment, runs tests with coverage, and cleans up

set -e

# Parse command line arguments
FAST_MODE=false
PARALLEL_JOBS="auto"

while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST_MODE=true
            shift
            ;;
        --jobs|-j)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fast] [--jobs N]"
            exit 1
            ;;
    esac
done

echo "🧪 PlacePix Test Runner"
echo "======================="

# Create test directories
TEST_DATA_DIR="./test_data"
TEST_IMAGES_DIR="./test_images"
TEST_CACHE_DIR="./test_cache"

# Clean up any existing test directories
echo "🧹 Cleaning up previous test artifacts..."
rm -rf "$TEST_DATA_DIR" "$TEST_IMAGES_DIR" "$TEST_CACHE_DIR"

# Create fresh test directories
mkdir -p "$TEST_DATA_DIR" "$TEST_IMAGES_DIR"

# Set test environment
echo "🔧 Setting up test environment..."
export ENV_FILE=".env.test"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install test dependencies if not already installed
echo "📦 Ensuring test dependencies are installed..."
pip install pytest pytest-cov pytest-xdist --quiet

# Build pytest command
PYTEST_CMD="pytest tests/ -n $PARALLEL_JOBS --dist=loadscope"

if [ "$FAST_MODE" = true ]; then
    echo "🚀 Running tests in fast mode (no coverage)..."
    PYTEST_CMD="$PYTEST_CMD -q"
else
    echo "🚀 Running tests with coverage..."
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=term-missing --cov-fail-under=90"
fi

# Run tests
eval $PYTEST_CMD

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    if [ "$FAST_MODE" = false ]; then
        echo "📊 Coverage report generated in htmlcov/"
    fi
else
    echo ""
    if [ "$FAST_MODE" = true ]; then
        echo "❌ Tests failed"
    else
        echo "❌ Tests failed or coverage below 90%"
    fi
    exit 1
fi

# Clean up test directories
echo "🧹 Cleaning up test directories..."
rm -rf "$TEST_DATA_DIR" "$TEST_IMAGES_DIR" "$TEST_CACHE_DIR"

echo "🎉 Test run completed successfully!"
