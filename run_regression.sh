#!/bin/bash
# Fast Regression Test Suite
# Run time target: <10 seconds

set -e

echo "========================================"
echo "🧪 Benchside Regression Test Suite"
echo "========================================"
echo ""

# Backend tests
echo "📦 Backend Tests..."
echo "----------------------------------------"
cd backend

if [ ! -d "tests/regression" ]; then
    echo "❌ Regression test directory not found"
    exit 1
fi

# Run tests with timing
START_TIME=$(date +%s.%N)
python3 -m pytest tests/regression/ -v --tb=short
END_TIME=$(date +%s.%N)

# Calculate elapsed time
ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)
echo ""
echo "----------------------------------------"
echo "⏱️  Backend: ${ELAPSED}s"
echo ""

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All backend tests passed"
else
    echo "❌ Backend tests failed"
    exit 1
fi

# Frontend tests (if they exist)
cd ../frontend

if [ -f "package.json" ] && grep -q "test:regression" package.json; then
    echo ""
    echo "📦 Frontend Tests..."
    echo "----------------------------------------"
    npm run test:regression
    if [ $? -eq 0 ]; then
        echo "✅ All frontend tests passed"
    else
        echo "❌ Frontend tests failed"
        exit 1
    fi
else
    echo ""
    echo "⚠️  Frontend regression tests not configured yet"
fi

echo ""
echo "========================================"
echo "✅ Regression Suite Complete"
echo "========================================"
echo ""
echo "Total time: ${ELAPSED}s"
echo "Target: <10s"
echo ""

# Check if we met the target
if (( $(echo "$ELAPSED < 10" | bc -l) )); then
    echo "✅ Performance target met!"
else
    echo "⚠️  Performance target missed (>${ELAPSED}s)"
fi
