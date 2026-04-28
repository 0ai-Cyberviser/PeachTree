# IGRFT Memory Optimization Guide

## ⚠️ System Crashes During Training - CRITICAL FIX

**Symptom**: zsh/Chrome crashes with SEGFAULT/BUS errors during model training

**Root Cause**: Memory exhaustion when loading 7B parameter models on CPU

**Your System Status** (as of Apr 28, 2026 03:08):
```
RAM:  18GB total, 10GB free, 6.2GB used
Swap: 12GB total, 4.5GB used (⚠️ HIGH - indicates memory pressure)
/tmp: 59% full (5.6GB used)
```

## 🚨 Critical Actions BEFORE Training

### 1. Free Up Memory (Do ALL of these)

```bash
# Close Chrome/browsers (saves 2-4GB)
pkill -9 chrome
pkill -9 chromium

# Close VS Code if not editing (saves 1-2GB)
# Or at minimum, close unused VS Code windows

# Clear swap to start fresh
sudo swapoff -a && sudo swapon -a

# Verify free memory
free -h
# Should show at least 12GB free RAM
```

### 2. Set Memory Limits for Training

```bash
# Limit Python memory usage to 10GB
ulimit -v 10485760  # 10GB in KB

# Monitor memory during training
watch -n 2 'free -h'
```

### 3. Use Smaller Model (RECOMMENDED)

Instead of Mistral-7B (8GB+ RAM), use a smaller model:

```python
# In inference_recursive_learning.py, change:
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Only 2GB RAM!
# or
MODEL_NAME = "microsoft/phi-2"  # 3GB RAM
```

## 📋 Safe Training Workflow

### Option A: Minimal Memory Mode (< 6GB RAM)

```bash
# 1. Close all non-essential apps
pkill chrome
pkill code  # Close VS Code

# 2. Use TinyLlama model
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/unified-expanded.jsonl \
    --cycles 3 \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --output-dir data/hancock/igrft \
    --verbose

# 3. Monitor memory in another terminal
watch -n 5 'free -h && ps aux | grep python | head -5'
```

### Option B: Batch Processing (Recommended)

Don't run full training - just **generate the training scripts**, then run them **one at a time** while monitoring:

```bash
# Step 1: Generate training scripts only (low memory)
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/unified-expanded.jsonl \
    --cycles 5 \
    --generate-only

# Step 2: Train ONE cycle at a time
# Close all other apps first!
python models/igrft-cycles/train_cycle_1.py

# Wait for completion, monitor memory
# Then run next cycle
python models/igrft-cycles/train_cycle_2.py
```

### Option C: Swap to Disk-Based Inference (No Training)

If training keeps crashing, skip fine-tuning and just use inference:

```bash
# Run inference only (no training, low memory)
python -c "
from pathlib import Path
import json

# Load dataset
records = []
for line in Path('data/hancock/unified-expanded.jsonl').read_text().splitlines():
    if line.strip():
        records.append(json.loads(line))

print(f'Loaded {len(records)} records')
print(f'Sample: {records[0][\"instruction\"][:100]}...')
"
```

## 🔧 Code Modifications for Low Memory

### Update `inference_recursive_learning.py`

Add memory-safe defaults:

```python
# At top of CPUOptimizedTrainer class
DEFAULT_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Changed from Mistral-7B

# In prepare_training_script method
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,  # Keep at 1
    gradient_accumulation_steps=4,   # Reduced from 8
    num_train_epochs=1,              # Reduced from 3 (faster, less memory)
    max_steps=100,                   # Early stopping
    learning_rate=2e-4,
    bf16=False,                      # Disable for more compatibility
    logging_steps=5,
    save_steps=50,
    save_total_limit=1,              # Only keep 1 checkpoint (saves disk)
    gradient_checkpointing=True,
    max_grad_norm=0.3,
    use_cpu=True,
    no_cuda=True,
    dataloader_num_workers=0,        # No parallel loading (saves memory)
    max_length=512                    # Limit sequence length (saves memory)
)
```

## 📊 Memory Monitoring Commands

```bash
# Real-time memory monitoring
watch -n 1 'free -h && echo "---" && ps aux --sort=-%mem | head -10'

# Check for OOM killer activity
dmesg | grep -i "killed process"

# Monitor swap usage
vmstat 2 5

# Check /tmp disk space
df -h /tmp

# See which process is using most memory
ps aux --sort=-%mem | head -10
```

## ✅ Success Criteria

Training is safe to run when:
- [ ] Free RAM ≥ 12GB (`free -h` shows 12GB+ available)
- [ ] Swap used < 2GB
- [ ] Chrome/browsers closed
- [ ] /tmp has > 4GB free space
- [ ] Using TinyLlama or Phi-2 (not Mistral-7B)

## 🚀 Alternative: Cloud Training

If local memory continues to be an issue:

```bash
# Option 1: Google Colab (Free tier has 12GB RAM)
# Upload dataset to Colab, run training there

# Option 2: GitHub Codespaces (4-core, 16GB)
# 60 hours/month free

# Option 3: Vast.ai ($0.10/hour for CPU training)
```

## 📝 Quick Reference

| Model | RAM Required | Training Time (5 cycles) | Quality |
|-------|--------------|-------------------------|---------|
| TinyLlama-1.1B | 2-3GB | 2-3 hours | Good |
| Phi-2 (2.7B) | 4-5GB | 4-6 hours | Better |
| Mistral-7B | 8-12GB | 12-18 hours | Best |

**Recommendation**: Start with TinyLlama, verify it works, then try larger models.

## 🔥 Emergency: Training Hanging/Crashed

```bash
# Kill all Python processes
pkill -9 python

# Clear memory cache
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Check what's using memory
ps aux --sort=-%mem | head -20

# Reboot if needed
sudo reboot
```
