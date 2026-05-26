#!/bin/bash

# Test runner script for PlacePix
# Sets up test environment, runs tests with coverage, and cleans up

set -e

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
pip install pytest pytest-cov --quiet

# Run tests with coverage
echo "🚀 Running tests with coverage..."
pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=90 \
    -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo "📊 Coverage report generated in htmlcov/"
else
    echo ""
    echo "❌ Tests failed or coverage below 90%"
    exit 1
fi

# Clean up test directories
echo "🧹 Cleaning up test directories..."
rm -rf "$TEST_DATA_DIR" "$TEST_IMAGES_DIR" "$TEST_CACHE_DIR"

echo "🎉 Test run completed successfully!"
