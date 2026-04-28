# Disk Space Solutions for ML Package Installation

## Problem: No Space Left on Device

**Error**: `[Errno 28] No space left on device` at package 46/53 during `pip install transformers peft bitsandbytes accelerate`

**Current Status**:
- `/tmp` partition: 9.5GB total, 6.9GB used, **2.7GB free** (73% full)
- `.venv` size: **4.7GB**
- Packages needed: **~2.3GB** (missing 300MB)

---

## Solution 1: Remove CUDA Packages (Recommended for CPU Training)

You don't need CUDA packages for CPU-only training. Free ~2GB:

```bash
cd /tmp/peachtree

# Remove GPU-specific packages
pip uninstall -y \
  nvidia-cudnn-cu13 \
  nvidia-cublas \
  nvidia-cuda-runtime \
  nvidia-cufft \
  nvidia-curand \
  nvidia-cusolver \
  nvidia-cusparse \
  nvidia-cuda-cupti \
  nvidia-cuda-nvrtc \
  nvidia-nvjitlink \
  nvidia-nvtx \
  nvidia-cusparselt-cu13 \
  nvidia-nccl-cu13 \
  nvidia-nvshmem-cu13 \
  triton

# Install CPU-only PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining packages
pip install transformers peft accelerate datasets

# Run training
python3 train_hancock_comprehensive.py
```

**Result**: Training will work on CPU (6-12 hours estimated)

---

## Solution 2: Google Colab Free GPU (Fastest)

Upload files to Google Colab and train on free T4 GPU (~1-2 hours):

### Step 1: Upload Files
```python
# In Google Colab
from google.colab import files
uploaded = files.upload()  # Upload comprehensive-training.jsonl
uploaded = files.upload()  # Upload train_hancock_comprehensive.py
```

### Step 2: Install Dependencies
```bash
!pip install transformers peft bitsandbytes accelerate datasets
```

### Step 3: Run Training
```python
!python train_hancock_comprehensive.py
```

### Step 4: Download Trained Model
```python
from google.colab import files
!tar -czf hancock-comprehensive-v1.tar.gz models/hancock-comprehensive-v1/
files.download('hancock-comprehensive-v1.tar.gz')
```

**Files to Upload**:
- `data/hancock/comprehensive-training.jsonl` (1.1MB)
- `train_hancock_comprehensive.py` (328 lines)

**Advantages**:
- Free T4 GPU (8 hours/day limit)
- 1-2 hour training time (vs 6-12 hours CPU)
- 15GB RAM available
- 100GB disk space

---

## Solution 3: Clean .venv and Reinstall Essentials

Free space by removing unused packages:

```bash
cd /tmp/peachtree

# Deactivate venv
deactivate

# Remove entire venv
rm -rf .venv

# Recreate minimal venv
python3 -m venv .venv
source .venv/bin/activate

# Install only PeachTree essentials
pip install -e .

# Install ML packages (CPU-only)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers peft accelerate datasets
```

**Result**: Fresh start with ~3GB saved

---

## Solution 4: Move Training to Different Location

Use a partition with more space:

```bash
# Check available partitions
df -h

# Example: Move to home directory
mkdir -p ~/ml-training
cp data/hancock/comprehensive-training.jsonl ~/ml-training/
cp train_hancock_comprehensive.py ~/ml-training/
cd ~/ml-training

# Create venv there
python3 -m venv .venv
source .venv/bin/activate

# Install packages
pip install transformers peft accelerate datasets torch

# Update script paths
sed -i 's|data/hancock/comprehensive-training.jsonl|comprehensive-training.jsonl|g' train_hancock_comprehensive.py

# Train
python3 train_hancock_comprehensive.py
```

---

## Quick Decision Matrix

| Solution | Time to Train | Disk Space Freed | Complexity |
|----------|---------------|------------------|------------|
| **Remove CUDA** | 6-12h (CPU) | ~2GB | Low |
| **Google Colab** | 1-2h (T4 GPU) | 0 (cloud) | Very Low |
| **Clean .venv** | 6-12h (CPU) | ~3GB | Medium |
| **Move location** | 6-12h (CPU) | 0 (uses different partition) | Medium |

---

## Recommended Approach

### For Immediate Local Training:
```bash
# Quick fix (5 minutes)
cd /tmp/peachtree
pip uninstall -y nvidia-cudnn-cu13 nvidia-cublas nvidia-cuda-runtime nvidia-cufft nvidia-curand nvidia-cusolver nvidia-cusparse
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers peft accelerate datasets
python3 train_hancock_comprehensive.py
```

### For Fastest Training:
1. Go to [Google Colab](https://colab.research.google.com)
2. Upload `comprehensive-training.jsonl` and `train_hancock_comprehensive.py`
3. Run training on free T4 GPU
4. Download trained model

---

## Training Status Summary

✅ **Dataset Ready**: `data/hancock/comprehensive-training.jsonl` (1,721 records, 1.1MB)  
✅ **Training Script Ready**: `train_hancock_comprehensive.py` (328 lines)  
✅ **Handoff Manifest Created**: `comprehensive-handoff.json`  
✅ **Quality Report Generated**: `reports/comprehensive-quality.json`  
⏳ **ML Packages**: Installation blocked by disk space (need 300MB more)

---

## After Training Completes

```bash
# Check training results
cat models/hancock-comprehensive-v1/training_summary.json

# Test the model
python3 << 'EOF'
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

model = AutoPeftModelForCausalLM.from_pretrained("models/hancock-comprehensive-v1")
tokenizer = AutoTokenizer.from_pretrained("models/hancock-comprehensive-v1")

prompt = "Analyze SQL injection attempt: SELECT * FROM users WHERE id='1' OR '1'='1'"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0]))
EOF
```

---

## Contact & Support

**Created**: April 28, 2026  
**Dataset**: hancock-comprehensive-v1 (1,721 records)  
**Model**: mistralai/Mistral-7B-Instruct-v0.3  
**Method**: QLoRA fine-tuning

**Files**:
- Training script: `train_hancock_comprehensive.py`
- Dataset: `data/hancock/comprehensive-training.jsonl`
- Handoff: `comprehensive-handoff.json`
- Guide: `START-TRAINING-NOW.md`
