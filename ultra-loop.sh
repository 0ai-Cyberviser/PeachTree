#!/bin/bash
# Ultra test loop - 10,000 iterations

LOG_FILE="ultra-loop-output.log"
ITERATIONS=10000
DATASET="data/hancock/unified-expanded.jsonl"

echo "🚀 Starting Ultra Loop: $ITERATIONS iterations" > "$LOG_FILE"
echo "   Dataset: $DATASET" >> "$LOG_FILE"
echo "   Started: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

for i in $(seq 1 $ITERATIONS); do
    echo "=== Iteration $i/$ITERATIONS ===" >> "$LOG_FILE"
    
    if [ -f "$DATASET" ]; then
        RECORD_COUNT=$(wc -l < "$DATASET")
        echo "  Records: $RECORD_COUNT" >> "$LOG_FILE"
    fi
    
    if [ $((i % 100)) -eq 0 ]; then
        echo "🎯 Checkpoint $i/$ITERATIONS - $(date)" >> "$LOG_FILE"
    fi
    
    if [ $((i % 1000)) -eq 0 ]; then
        echo "💤 Pause at $i" >> "$LOG_FILE"
        sleep 2
    fi
done

echo "✅ Completed $ITERATIONS iterations at $(date)" >> "$LOG_FILE"
