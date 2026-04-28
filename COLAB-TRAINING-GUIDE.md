# 🚀 Google Colab Training Guide - Hancock Cybersecurity LLM

**Fast GPU Training**: 30-45 minutes (vs 19 days on CPU!)

---

## 📋 Quick Start (3 Steps)

### Step 1: Open Colab Notebook
1. Go to: https://colab.research.google.com/
2. **File → Upload notebook**
3. Upload `hancock_training_colab.ipynb` from this directory

### Step 2: Enable GPU
1. **Runtime → Change runtime type**
2. **Hardware accelerator** → **T4 GPU**
3. **Save**

### Step 3: Run Training
1. **Runtime → Run all** (or Ctrl+F9)
2. Upload `data/hancock/unified-expanded.jsonl` when prompted
3. Wait 30-45 minutes
4. Download `hancock-v1.zip` when complete

---

## 📤 File Upload

When the notebook prompts for upload, select:
```
/tmp/peachtree/data/hancock/unified-expanded.jsonl
```

**Size**: 3.7 MB  
**Records**: 4,951  

---

## ⚡ Training Progress

Expected output:

```
🔧 Configuration:
   Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
   Dataset: unified-expanded.jsonl
   Batch size: 4 (effective: 16)
   Epochs: 3
   GPU: Tesla T4
   CUDA available: True

📂 Loading dataset from unified-expanded.jsonl...
✅ Loaded 4,951 records

🤖 Loading model and tokenizer...
trainable params: 2,252,800 || all params: 1,102,301,184 || trainable%: 0.2044
✅ Model loaded with QLoRA

🔤 Tokenizing dataset...
✅ Tokenized 4,951 examples

🚀 Starting training...
   Total steps: 928
   Estimated time: 30-45 minutes

Epoch 1/3: 100%|██████████| 309/309 [12:34<00:00,  2.44s/it]
Epoch 2/3: 100%|██████████| 309/309 [12:31<00:00,  2.43s/it]
Epoch 3/3: 100%|██████████| 309/309 [12:28<00:00,  2.42s/it]

✅ Training complete!
💾 Saving model...
✅ Model saved to: /content/hancock-v1
```

---

## 📥 Download Trained Model

After training completes:

1. **Automatic download** starts (`hancock-v1.zip`, ~500MB)
2. Save to your local machine
3. Extract to `/tmp/peachtree/models/hancock-v1/`

**Contents**:
```
hancock-v1/
├── adapter_config.json       # LoRA adapter config
├── adapter_model.safetensors # Trained LoRA weights (~9MB)
├── tokenizer_config.json     # Tokenizer configuration
├── special_tokens_map.json   # Special tokens
├── tokenizer.model           # SentencePiece model
├── training_summary.json     # Training metadata
└── README.md                 # Model card
```

---

## 🧪 Testing the Model

### In Colab (Optional)
The notebook includes a test cell that runs 3 example prompts:
- SQL injection explanation
- ASLR security feature
- nmap usage guide

### Locally After Download
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    load_in_4bit=True,
    device_map="auto"
)

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "models/hancock-v1")
tokenizer = AutoTokenizer.from_pretrained("models/hancock-v1")

# Test
prompt = "Explain SQL injection vulnerability"
inputs = tokenizer(f"### Instruction:\n{prompt}\n\n### Response:\n", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=150)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

## 🔧 Troubleshooting

### Upload Fails
**Error**: File too large for browser upload  
**Solution**: Use Google Drive instead:

```python
from google.colab import drive
drive.mount('/content/drive')

# Copy dataset from Drive
!cp /content/drive/MyDrive/unified-expanded.jsonl .
```

### GPU Out of Memory
**Error**: `CUDA out of memory`  
**Solution**: Reduce batch size in configuration cell:

```python
BATCH_SIZE = 2  # Instead of 4
GRADIENT_ACCUMULATION = 8  # Instead of 4
```

### Slow Training (>2 hours)
**Check**: Runtime type is set to **GPU** (not CPU)
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Should show GPU name
```

### Download Interrupted
**Solution**: Re-run download cell or use Drive:

```python
# Save to Google Drive instead
!cp -r /content/hancock-v1 /content/drive/MyDrive/
```

---

## ⚙️ Advanced Configuration

### Longer Training (Better Quality)
```python
EPOCHS = 5  # Instead of 3 (+15-20 min)
```

### Larger Model (More Capable)
```python
MODEL_NAME = "microsoft/phi-2"  # 2.7B params (+30 min training)
```

### Custom Dataset
Replace upload with your own JSONL:
```python
DATASET_PATH = "my-custom-dataset.jsonl"
```

**Required format**:
```json
{"instruction": "Question or task", "output": "Answer or response"}
{"instruction": "Another question", "output": "Another answer"}
```

---

## 📊 Training Metrics

**Expected performance**:
- **Speed**: 2.4 seconds/step on T4 GPU
- **Total time**: 
  - Epoch 1: ~12-13 minutes
  - Epoch 2: ~12-13 minutes  
  - Epoch 3: ~12-13 minutes
  - **Total**: ~36-40 minutes + upload/download time
- **Memory**: 4-5GB VRAM (4-bit quantization)
- **Model size**: ~500MB compressed, ~9MB adapter weights

---

## 🎯 Success Criteria

Training is successful when:
- ✅ All 3 epochs complete without errors
- ✅ Model saved to `/content/hancock-v1/`
- ✅ `training_summary.json` shows `"status": "complete"`
- ✅ Test prompts generate reasonable responses
- ✅ `hancock-v1.zip` downloads successfully

---

## 📚 Additional Resources

- **Colab Docs**: https://colab.research.google.com/notebooks/intro.ipynb
- **Transformers**: https://huggingface.co/docs/transformers
- **PEFT/LoRA**: https://huggingface.co/docs/peft
- **TinyLlama**: https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0

---

## 🚨 Important Notes

### Free Tier Limits
- **GPU time**: 12-15 hours/day (resets ~daily)
- **Session timeout**: 90 minutes idle, 12 hours active
- **Recommendation**: Complete training in one session (~40 min)

### Save Your Work
- Download `hancock-v1.zip` immediately after training
- Colab sessions reset - files are deleted!
- Consider saving to Google Drive for persistence

### Cost (Colab Pro)
If you need guaranteed GPU access:
- **Colab Pro**: $9.99/month (faster GPUs, longer sessions)
- **Colab Pro+**: $49.99/month (priority access, more resources)

---

## ✅ Checklist

Before starting:
- [ ] Colab notebook uploaded
- [ ] Runtime set to **T4 GPU**
- [ ] Dataset file ready (`unified-expanded.jsonl`, 3.7 MB)
- [ ] Stable internet connection
- [ ] 40-60 minutes available

During training:
- [ ] Keep browser tab open (avoid timeout)
- [ ] Monitor progress (check for errors)
- [ ] Don't close Colab tab

After training:
- [ ] Download `hancock-v1.zip` immediately
- [ ] Verify file size (~500MB)
- [ ] Extract and test locally
- [ ] Celebrate! 🎉

---

**Created**: April 28, 2026  
**Author**: Trainer Handoff Agent  
**Project**: PeachTree / Hancock Cybersecurity LLM  
**Organization**: 0ai-Cyberviser
