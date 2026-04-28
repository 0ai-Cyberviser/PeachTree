#!/bin/bash
# Continuous Autonomous Defense + PeachFuzz Monitoring
# Runs every 5 minutes, collecting security events and fuzzing results

echo "=========================================="
echo "CONTINUOUS DEFENSE + FUZZING MONITOR"
echo "=========================================="
echo "Started: $(date)"
echo "Interval: 5 minutes"
echo "Output: data/hancock/autonomous/"
echo ""

cd /tmp/peachtree

while true; do
    echo "[$(date '+%H:%M:%S')] Running defense + fuzzing cycle..."
    
    # Run enhanced autonomous defense
    python3 enhanced_autonomous.py
    
    # Update merged dataset
    cat data/hancock/autonomous/*_enriched.jsonl > data/hancock/autonomous/all_autonomous.jsonl
    
    # Show stats
    TOTAL_RECORDS=$(wc -l < data/hancock/autonomous/all_autonomous.jsonl)
    echo "  Total training records: $TOTAL_RECORDS"
    
    echo "[$(date '+%H:%M:%S')] Cycle complete. Sleeping 5 minutes..."
    echo ""
    
    sleep 300  # 5 minutes
done
