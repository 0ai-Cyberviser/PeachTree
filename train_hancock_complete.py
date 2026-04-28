#!/usr/bin/env python3
"""
Complete IGRFT Training Script for Hancock Cybersecurity LLM
Implements full QLoRA fine-tuning on CPU with memory optimization
"""

import os
import json
import torch
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DATASET_PATH = "data/hancock/unified-expanded.jsonl"
OUTPUT_DIR = "models/hancock-v1"
MAX_LENGTH = 512
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 8
EPOCHS = 3
LEARNING_RATE = 2e-4

def load_jsonl_dataset(path: str) -> Dataset:
    """Load JSONL dataset and format for training"""
    logger.info(f"Loading dataset from {path}")
    
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    record = json.loads(line)
                    # Format as instruction-following
                    text = f"### Instruction:\n{record['instruction']}\n\n### Response:\n{record['output']}"
                    records.append({"text": text})
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    
    logger.info(f"Loaded {len(records)} records")
    return Dataset.from_list(records)

def prepare_model_and_tokenizer():
    """Load model and tokenizer with QLoRA configuration"""
    logger.info(f"Loading model: {MODEL_NAME}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Configure 4-bit quantization for memory efficiency
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True
    )
    
    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="cpu",
        trust_remote_code=True
    )
    
    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    lora_config = LoraConfig(
        r=8,  # Low rank for memory efficiency
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer

def preprocess_function(examples, tokenizer):
    """Tokenize examples"""
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length"
    )

def main():
    """Main training function"""
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load dataset
    dataset = load_jsonl_dataset(DATASET_PATH)
    logger.info(f"Dataset size: {len(dataset)} records")
    
    # Load model and tokenizer
    model, tokenizer = prepare_model_and_tokenizer()
    
    # Tokenize dataset
    logger.info("Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        lambda x: preprocess_function(x, tokenizer),
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # Training arguments (CPU-optimized)
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=False,  # CPU doesn't support FP16
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        gradient_checkpointing=True,
        max_grad_norm=0.3,
        warmup_steps=100,

        report_to="none",
        logging_dir=f"{OUTPUT_DIR}/logs"
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator
    )
    
    # Train
    logger.info("🚀 Starting training...")
    logger.info(f"   Model: {MODEL_NAME}")
    logger.info(f"   Dataset: {DATASET_PATH} ({len(dataset)} records)")
    logger.info(f"   Epochs: {EPOCHS}")
    logger.info(f"   Batch size: {BATCH_SIZE} (effective: {BATCH_SIZE * GRADIENT_ACCUMULATION})")
    logger.info(f"   Output: {OUTPUT_DIR}")
    
    try:
        trainer.train()
        
        # Save final model
        logger.info("💾 Saving final model...")
        trainer.save_model(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        logger.info("✅ Training complete!")
        logger.info(f"   Model saved to: {OUTPUT_DIR}")
        
        # Save training summary
        summary = {
            "model": MODEL_NAME,
            "dataset": DATASET_PATH,
            "records": len(dataset),
            "epochs": EPOCHS,
            "output_dir": OUTPUT_DIR,
            "status": "complete"
        }
        
        summary_path = Path(OUTPUT_DIR) / "training_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"   Summary: {summary_path}")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
