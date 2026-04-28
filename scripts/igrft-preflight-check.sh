#!/bin/bash
# IGRFT Pre-Flight Check - Run this BEFORE training
# Ensures system is ready for CPU model training

set -e

echo "🔍 PeachTree IGRFT Pre-Flight Check"
echo "===================================="
echo ""

# Check 1: Memory
echo "📊 Memory Status:"
free -h | grep -E "Mem:|Swap:"

AVAILABLE_MEM=$(free -g | awk '/^Mem:/ {print $7}')
if [ "$AVAILABLE_MEM" -lt 8 ]; then
    echo "⚠️  WARNING: Only ${AVAILABLE_MEM}GB available (need 8GB+)"
    echo "   Action: Close browsers and heavy apps"
    echo ""
fi

# Check 2: Swap usage
SWAP_USED=$(free -g | awk '/^Swap:/ {print $3}')
if [ "$SWAP_USED" -gt 2 ]; then
    echo "⚠️  WARNING: ${SWAP_USED}GB swap in use (should be <2GB)"
    echo "   Action: Close apps or reboot"
    echo ""
fi

# Check 3: Disk space
echo ""
echo "💾 Disk Space (/tmp):"
df -h /tmp | tail -1

TMP_USAGE=$(df /tmp | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$TMP_USAGE" -gt 75 ]; then
    echo "⚠️  WARNING: /tmp is ${TMP_USAGE}% full"
    echo "   Action: Clean with: sudo rm -rf /tmp/tmp* /tmp/pytorch*"
    echo ""
fi

# Check 4: Running processes
echo ""
echo "🏃 Memory-Intensive Processes:"
ps aux --sort=-%mem | head -6

# Check 5: Dataset exists
echo ""
echo "📂 Dataset Check:"
if [ -f "data/hancock/unified-expanded.jsonl" ]; then
    RECORD_COUNT=$(wc -l < data/hancock/unified-expanded.jsonl)
    echo "✅ Dataset found: ${RECORD_COUNT} records"
else
    echo "❌ Dataset not found: data/hancock/unified-expanded.jsonl"
    echo "   Action: Run ingestion first"
fi

# Check 6: Python dependencies
echo ""
echo "🐍 Python Dependencies:"
python3 -c "
import sys
deps = ['transformers', 'peft', 'bitsandbytes', 'accelerate', 'datasets']
missing = []
for dep in deps:
    try:
        __import__(dep)
        print(f'✅ {dep}')
    except ImportError:
        print(f'❌ {dep} - MISSING')
        missing.append(dep)

if missing:
    print(f'\n⚠️  Install: pip install {\" \".join(missing)}')
    sys.exit(1)
" || {
    echo ""
    echo "❌ Missing dependencies"
    echo "   Action: pip install transformers peft bitsandbytes accelerate datasets"
    exit 1
}

# Summary
echo ""
echo "=================================="
echo "🎯 Pre-Flight Check Summary:"
echo "=================================="

if [ "$AVAILABLE_MEM" -ge 8 ] && [ "$SWAP_USED" -le 2 ] && [ "$TMP_USAGE" -le 75 ]; then
    echo "✅ READY FOR TRAINING"
    echo ""
    echo "Next steps:"
    echo "  1. Close browsers if running"
    echo "  2. Run safe training:"
    echo "     python run_safe_igrft.py data/hancock/unified-expanded.jsonl"
    echo ""
else
    echo "⚠️  CAUTION: System may struggle with training"
    echo ""
    echo "Recommended actions:"
    echo "  1. pkill chrome  # Close browsers"
    echo "  2. sudo swapoff -a && sudo swapon -a  # Clear swap"
    echo "  3. python run_safe_igrft.py data/hancock/unified-expanded.jsonl"
    echo ""
    echo "Or use minimal mode:"
    echo "  python run_safe_igrft.py data/hancock/unified-expanded.jsonl --cycles 1"
    echo ""
fi

exit 0
