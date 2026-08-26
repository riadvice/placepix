#!/bin/bash

# Test runner script for PlacePix
# Sets up test environment, runs tests with coverage, and cleans up

set -e

# Parse command line arguments
FAST_MODE=false
PARALLEL_JOBS="auto"

# Default to all logical CPUs for pytest-xdist parallel execution
if command -v nproc >/dev/null 2>&1; then
    DEFAULT_JOBS=$(nproc)
elif command -v python3 >/dev/null 2>&1; then
    DEFAULT_JOBS=$(python3 -c "import os; print(os.cpu_count() or 1)")
else
    DEFAULT_JOBS=1
fi

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
        --workers|-w)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fast] [--jobs N|--workers N]"
            exit 1
            ;;
    esac
done

# Resolve 'auto' to the number of logical CPUs for the dedicated pytest-xdist runner
if [ "$PARALLEL_JOBS" = "auto" ]; then
    PARALLEL_JOBS=$DEFAULT_JOBS
fi

echo "🧪 PlacePix Test Runner"
echo "======================="

# Create test directories
TEST_DATA_DIR="./test_data"
TEST_IMAGES_DIR="./test_images"
TEST_CACHE_DIR="./test_cache"

# Clean up any existing test directories and stale coverage files
echo "🧹 Cleaning up previous test artifacts..."
rm -rf "$TEST_DATA_DIR" "$TEST_IMAGES_DIR" "$TEST_CACHE_DIR"
rm -f .coverage .coverage.*

# Create fresh test directories
mkdir -p "$TEST_DATA_DIR" "$TEST_IMAGES_DIR"

# Set test environment
echo "🔧 Setting up test environment..."
export ENV_FILE=".env.test"
export TESTING=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Source venv if exists
VENV_DIR="$(pwd)/.venv"
if [[ -d "$VENV_DIR" ]]; then
  echo "🐍 Activating local venv at $VENV_DIR"
  source "$VENV_DIR/bin/activate"
fi

# Install test dependencies if not already installed
echo "📦 Ensuring test dependencies are installed..."
pip install pytest pytest-cov pytest-xdist --quiet

# Build pytest command using pytest-xdist for process-level parallelism
PYTEST_CMD="pytest tests/ -n $PARALLEL_JOBS --dist=loadscope -m 'not slow'"

if [ "$FAST_MODE" = true ]; then
    echo "🚀 Running tests in fast mode (no coverage)..."
    PYTEST_CMD="$PYTEST_CMD -q"
else
    echo "🚀 Running tests with coverage..."
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=90"
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
