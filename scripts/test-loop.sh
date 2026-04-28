#!/bin/bash
# Test Loop - Run comprehensive tests multiple times

ITERATIONS=${1:-10}
RESULTS_DIR="test-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "🔁 Running $ITERATIONS test iterations..."
echo "📁 Results will be saved to: $RESULTS_DIR"
echo ""

TOTAL_PASSED=0
TOTAL_FAILED=0
ITERATION_TIMES=()

for i in $(seq 1 $ITERATIONS); do
    echo "========================================"
    echo "Iteration $i of $ITERATIONS"
    echo "========================================"
    
    START_TIME=$(date +%s)
    
    # Run tests
    if python -m pytest tests/ -q --tb=line > "$RESULTS_DIR/iteration-$i.log" 2>&1; then
        STATUS="✅ PASS"
        ((TOTAL_PASSED++))
    else
        STATUS="❌ FAIL"
        ((TOTAL_FAILED++))
    fi
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    ITERATION_TIMES+=($DURATION)
    
    echo "$STATUS (${DURATION}s)"
    
    # Brief summary
    PASSED=$(grep -c "passed" "$RESULTS_DIR/iteration-$i.log" || echo 0)
    FAILED=$(grep -c "failed" "$RESULTS_DIR/iteration-$i.log" || echo 0)
    echo "  Tests: $PASSED passed, $FAILED failed"
    echo ""
done

# Calculate statistics
AVG_TIME=0
if [ ${#ITERATION_TIMES[@]} -gt 0 ]; then
    TOTAL_TIME=0
    for time in "${ITERATION_TIMES[@]}"; do
        TOTAL_TIME=$((TOTAL_TIME + time))
    done
    AVG_TIME=$((TOTAL_TIME / ${#ITERATION_TIMES[@]}))
fi

# Final summary
echo "========================================"
echo "FINAL SUMMARY"
echo "========================================"
echo "Total Iterations: $ITERATIONS"
echo "Successful Runs:  $TOTAL_PASSED"
echo "Failed Runs:      $TOTAL_FAILED"
echo "Success Rate:     $((TOTAL_PASSED * 100 / ITERATIONS))%"
echo "Average Time:     ${AVG_TIME}s"
echo ""
echo "Results saved to: $RESULTS_DIR/"
echo "========================================"

# Return failure if any iteration failed
if [ $TOTAL_FAILED -gt 0 ]; then
    exit 1
fi

exit 0
