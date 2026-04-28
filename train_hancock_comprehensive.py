#!/usr/bin/env python3
"""
Hancock Comprehensive v1 - QLoRA Fine-Tuning Script
CPU-optimized training for mistralai/Mistral-7B-Instruct-v0.3

Dataset: comprehensive-training.jsonl (1,721 records)
Base Model: mistralai/Mistral-7B-Instruct-v0.3
Method: 4-bit QLoRA with CPU fallback
"""

import os
import json
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List

print("=" * 80)
print("HANCOCK COMPREHENSIVE V1 - TRAINING")
print("=" * 80)
print(f"Started: {datetime.utcnow().isoformat()}Z")
print()

# Configuration
DATASET_PATH = "data/hancock/comprehensive-training.jsonl"
OUTPUT_DIR = "models/hancock-comprehensive-v1"
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# Training hyperparameters (CPU-optimized)
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 8  # Effective batch size = 8
WARMUP_STEPS = 100
MAX_SEQ_LENGTH = 2048

# LoRA configuration
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05

print("📋 Configuration:")
print(f"  Dataset: {DATASET_PATH}")
print(f"  Base Model: {BASE_MODEL}")
print(f"  Output: {OUTPUT_DIR}")
print(f"  Learning Rate: {LEARNING_RATE}")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Effective Batch Size: {BATCH_SIZE * GRADIENT_ACCUMULATION}")
print(f"  LoRA Rank: {LORA_R}")
print()

# Check if essential packages are available
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset
    
    print("✅ All required packages available")
except ImportError as e:
    print("❌ Missing required packages!")
    print(f"   Error: {e}")
    print()
    print("Install with:")
    print("  pip install transformers peft accelerate datasets bitsandbytes")
    print()
    print("For CPU-only (no CUDA):")
    print("  pip install torch --index-url https://download.pytorch.org/whl/cpu")
    print("  pip install transformers peft accelerate datasets")
    exit(1)

# Load dataset
print("📂 Loading dataset...")
records = []
with open(DATASET_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f"✅ Loaded {len(records)} records")
print()

# Convert to Hugging Face Dataset
def format_record(record: Dict) -> Dict:
    """Convert PeachTree JSONL to training format."""
    instruction = record.get('instruction', '')
    input_text = record.get('input', '')
    output_text = record.get('output', '')
    
    # Create prompt in ChatML format
    if input_text:
        prompt = f"<|im_start|>user\n{instruction}\n{input_text}<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
    
    # Full text for training
    text = f"{prompt}{output_text}<|im_end|>"
    
    return {"text": text}

print("🔄 Formatting dataset...")
formatted_records = [format_record(r) for r in records]
dataset = Dataset.from_list(formatted_records)
print(f"✅ Dataset formatted: {len(dataset)} examples")
print()

# Train/eval split (90/10)
print("✂️  Splitting dataset...")
split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split_dataset['train']
eval_dataset = split_dataset['test']
print(f"✅ Train: {len(train_dataset)} | Eval: {len(eval_dataset)}")
print()

# Check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  Device: {device}")

# Quantization config (if CUDA available)
if device == "cuda":
    print("   Using 4-bit quantization (GPU)")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
else:
    print("   Using full precision (CPU)")
    quantization_config = None

print()

# Load tokenizer
print("📝 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
print("✅ Tokenizer loaded")
print()

# Load base model
print("🤖 Loading base model...")
print(f"   This may take several minutes (downloading ~14GB)...")

model_kwargs = {
    "pretrained_model_name_or_path": BASE_MODEL,
    "trust_remote_code": True,
}

if quantization_config:
    model_kwargs["quantization_config"] = quantization_config
    model_kwargs["device_map"] = "auto"
else:
    # CPU mode - load in full precision
    model_kwargs["torch_dtype"] = torch.float32
    model_kwargs["low_cpu_mem_usage"] = True

model = AutoModelForCausalLM.from_pretrained(**model_kwargs)
print("✅ Model loaded")
print()

# Prepare model for training
if quantization_config:
    print("🔧 Preparing model for k-bit training...")
    model = prepare_model_for_kbit_training(model)
else:
    print("🔧 Preparing model for CPU training...")
    model.train()

# LoRA configuration
print("🎛️  Configuring LoRA...")
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
print()

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
    )

print("🔤 Tokenizing dataset...")
tokenized_train = train_dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
)
tokenized_eval = eval_dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
)
print("✅ Tokenization complete")
print()

# Training arguments
print("⚙️  Setting up training arguments...")
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    learning_rate=LEARNING_RATE,
    warmup_steps=WARMUP_STEPS,
    max_grad_norm=0.3,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    load_best_model_at_end=True,
    fp16=False,  # Don't use FP16 on CPU
    bf16=True if device == "cpu" else False,  # BFloat16 for CPU
    report_to=["none"],  # Disable wandb/tensorboard
    save_total_limit=2,
)
print("✅ Training arguments configured")
print()

# Trainer
print("👨‍🏫 Initializing trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval,
    tokenizer=tokenizer,
)
print("✅ Trainer ready")
print()

# Start training
print("=" * 80)
print("🚀 STARTING TRAINING")
print("=" * 80)
print(f"⏱️  Estimated time: {'1-2 hours (GPU)' if device == 'cuda' else '6-12 hours (CPU)'}")
print()

try:
    trainer.train()
    print()
    print("=" * 80)
    print("✅ TRAINING COMPLETE")
    print("=" * 80)
    print()
    
    # Save final model
    print("💾 Saving final model...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"✅ Model saved to: {OUTPUT_DIR}")
    print()
    
    # Evaluate
    print("📊 Final evaluation...")
    eval_results = trainer.evaluate()
    print("Evaluation metrics:")
    for key, value in eval_results.items():
        print(f"  {key}: {value:.4f}")
    print()
    
    # Save training summary
    summary = {
        "model_name": "hancock-comprehensive-v1",
        "base_model": BASE_MODEL,
        "dataset_path": DATASET_PATH,
        "dataset_size": len(records),
        "train_size": len(train_dataset),
        "eval_size": len(eval_dataset),
        "hyperparameters": {
            "learning_rate": LEARNING_RATE,
            "num_epochs": NUM_EPOCHS,
            "batch_size": BATCH_SIZE,
            "gradient_accumulation": GRADIENT_ACCUMULATION,
            "lora_r": LORA_R,
            "lora_alpha": LORA_ALPHA,
        },
        "device": device,
        "final_eval": eval_results,
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }
    
    summary_path = Path(OUTPUT_DIR) / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Training summary saved: {summary_path}")
    print()
    
    print("=" * 80)
    print("🎉 ALL DONE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print(f"  1. Test the model: python test_hancock_model.py")
    print(f"  2. Find outputs in: {OUTPUT_DIR}")
    print(f"  3. Load for inference:")
    print(f"     from peft import AutoPeftModelForCausalLM")
    print(f"     model = AutoPeftModelForCausalLM.from_pretrained('{OUTPUT_DIR}')")
    
except KeyboardInterrupt:
    print()
    print("⚠️  Training interrupted by user")
    print(f"   Partial model saved to: {OUTPUT_DIR}")
    exit(1)
except Exception as e:
    print()
    print("❌ Training failed!")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
