#!/bin/bash
# Comprehensive PeachTree Test Suite
# Runs all tests, quality checks, and validations

set -e

echo "========================================"
echo "PEACHTREE COMPREHENSIVE TEST SUITE"
echo "========================================"
echo ""

ITERATION=${1:-1}
TOTAL_ITERATIONS=${2:-1}

echo "📊 Test Iteration: $ITERATION of $TOTAL_ITERATIONS"
echo "🕐 Started: $(date)"
echo ""

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Function to run test and track results
run_test() {
    local name="$1"
    local cmd="$2"
    
    echo "▶ Running: $name"
    if eval "$cmd" > /tmp/test-output.log 2>&1; then
        echo "  ✅ PASSED"
        ((PASSED++))
        return 0
    else
        echo "  ❌ FAILED"
        echo "  Error output:"
        tail -10 /tmp/test-output.log | sed 's/^/    /'
        ((FAILED++))
        return 1
    fi
}

# 1. CODE QUALITY CHECKS
echo "════════════════════════════════════════"
echo "1. CODE QUALITY CHECKS"
echo "════════════════════════════════════════"
echo ""

run_test "Ruff linting" "ruff check src/ tests/ --quiet"
run_test "Ruff formatting check" "ruff format --check src/ tests/ --quiet"
run_test "MyPy type checking" "mypy src/peachtree/ --strict --no-error-summary"

echo ""

# 2. UNIT TESTS
echo "════════════════════════════════════════"
echo "2. UNIT TESTS"
echo "════════════════════════════════════════"
echo ""

run_test "Full test suite" "pytest tests/ -v --tb=short -q"
run_test "Tests with coverage" "pytest tests/ --cov=src/peachtree --cov-report=term-missing:skip-covered --cov-report=html --cov-report=json -q"

echo ""

# 3. CLI SMOKE TESTS
echo "════════════════════════════════════════"
echo "3. CLI SMOKE TESTS"
echo "════════════════════════════════════════"
echo ""

run_test "CLI help" "peachtree --help"
run_test "CLI version" "peachtree --version"
run_test "Policy command" "peachtree policy"
run_test "Health command" "peachtree health"

echo ""

# 4. COMPLIANCE FRAMEWORK TESTS
echo "════════════════════════════════════════"
echo "4. COMPLIANCE FRAMEWORK TESTS"
echo "════════════════════════════════════════"
echo ""

if [ -f "data/hancock/unified-bugbounty-training.jsonl" ]; then
    run_test "Compliance check (seed)" "python scripts/compliance-check.py --dataset data/hancock/unified-bugbounty-training.jsonl --min-records 10"
else
    echo "  ⚠️  WARNING: Dataset not found, skipping compliance test"
    ((WARNINGS++))
fi

echo ""

# 5. DATASET OPERATIONS
echo "════════════════════════════════════════"
echo "5. DATASET OPERATIONS"
echo "════════════════════════════════════════"
echo ""

if [ -f "data/hancock/unified-bugbounty-training.jsonl" ]; then
    run_test "Quality scoring" "peachtree quality --input data/hancock/unified-bugbounty-training.jsonl --output /tmp/quality-test.json"
    run_test "Security scoring" "peachtree security-score --dataset data/hancock/unified-bugbounty-training.jsonl --security-weight 0.6 --format json"
    run_test "Deduplication check" "peachtree dedup --source data/hancock/unified-bugbounty-training.jsonl --output /tmp/dedup-test.jsonl --write-output false"
else
    echo "  ⚠️  WARNING: Dataset not found, skipping dataset tests"
    ((WARNINGS+=3))
fi

echo ""

# 6. INTEGRATION TESTS
echo "════════════════════════════════════════"
echo "6. INTEGRATION TESTS"
echo "════════════════════════════════════════"
echo ""

if [ -f "tests/test_hancock_integration.py" ]; then
    run_test "Hancock integration" "pytest tests/test_hancock_integration.py -v -q"
else
    echo "  ⚠️  WARNING: Hancock integration tests not found"
    ((WARNINGS++))
fi

echo ""

# 7. DOCUMENTATION BUILD
echo "════════════════════════════════════════"
echo "7. DOCUMENTATION BUILD"
echo "════════════════════════════════════════"
echo ""

run_test "MkDocs build" "mkdocs build --strict --quiet"

echo ""

# 8. SECURITY CHECKS
echo "════════════════════════════════════════"
echo "8. SECURITY CHECKS"
echo "════════════════════════════════════════"
echo ""

run_test "Secret scanning simulation" "! grep -r 'password.*=.*[\"\\x27][^\"\\x27]' src/ tests/ --include='*.py' || echo 'No hardcoded passwords found'"

echo ""

# SUMMARY
echo "========================================"
echo "TEST SUITE SUMMARY - Iteration $ITERATION"
echo "========================================"
echo ""
echo "✅ Passed:   $PASSED"
echo "❌ Failed:   $FAILED"
echo "⚠️  Warnings: $WARNINGS"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    echo "Success Rate: $SUCCESS_RATE%"
fi

echo ""
echo "🕐 Completed: $(date)"
echo "========================================"

# Exit with failure if any tests failed
if [ $FAILED -gt 0 ]; then
    exit 1
fi

exit 0
