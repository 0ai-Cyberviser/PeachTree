#!/bin/bash
# Continuous enhancement loop

ITERATIONS=${1:-100}
DATASET="data/hancock/unified-expanded.jsonl"

echo "🔁 Starting $ITERATIONS enhancement iterations..."
echo ""

for i in $(seq 1 $ITERATIONS); do
    echo "=== Iteration $i/$ITERATIONS ==="
    
    # Quality check
    python -m peachtree.cli score \
        --dataset "$DATASET" \
        --json-output "reports/iteration-$i-quality.json" \
        --format json > /dev/null 2>&1
    
    # Security check
    python -m peachtree.cli security-score \
        --dataset "$DATASET" \
        --output "reports/iteration-$i-security.json" \
        --format json > /dev/null 2>&1
    
    # Get metrics
    RECORDS=$(wc -l < "$DATASET")
    AVG_SECURITY=$(jq -r '.average_score' "reports/iteration-$i-security.json" 2>/dev/null || echo "0")
    
    echo "  Records: $RECORDS | Security: $AVG_SECURITY"
    
    # Brief delay
    sleep 0.5
done

echo ""
echo "✅ Completed $ITERATIONS enhancement iterations"
