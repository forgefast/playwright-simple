#!/bin/bash
# Run tests to prevent regressions

set -e

echo "🧪 Running Playwright Simple tests..."
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-asyncio
fi

# Run tests
pytest tests/ -v --tb=short

echo ""
echo "✅ All tests passed!"

