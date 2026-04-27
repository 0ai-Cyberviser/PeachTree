"""
PeachTree Integration Examples for Multiple LLM Frameworks

Demonstrates how to use PeachTree security datasets with various LLM training frameworks.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


# ============================================================================
# 1. MISTRAL INTEGRATION
# ============================================================================

def prepare_mistral_dataset(
    source_dataset: str,
    output_file: str,
    system_prompt: str = "You are a helpful cybersecurity AI assistant."
) -> None:
    """
    Prepare PeachTree dataset for Mistral fine-tuning.
    
    Mistral uses ChatML format with specific tokenization.
    
    Args:
        source_dataset: Path to PeachTree JSONL dataset
        output_file: Output file for Mistral training
        system_prompt: System prompt for the model
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # Mistral ChatML format
                mistral_record = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": record.get("instruction", "")},
                        {"role": "assistant", "content": record.get("response", "")}
                    ],
                    "id": record.get("id"),
                    "metadata": {
                        "source_repo": record.get("source_repo"),
                        "license": record.get("license"),
                        "quality_score": record.get("quality_score", 0)
                    }
                }
                records.append(mistral_record)
    
    # Save in Mistral format
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ Mistral dataset ready: {len(records)} conversations")


def train_mistral_model(
    dataset_path: str,
    model_name: str = "mistralai/Mistral-7B-v0.1",
    output_dir: str = "models/mistral-security"
) -> None:
    """
    Train Mistral model with PeachTree security dataset.
    
    Uses QLoRA for efficient fine-tuning on consumer hardware.
    """
    
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM,
        TrainingArguments,
        Trainer
    )
    from peft import LoraConfig, get_peft_model
    from datasets import load_dataset
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_4bit=True,
        device_map="auto"
    )
    
    # LoRA configuration for Mistral
    lora_config = LoraConfig(
        r=64,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    
    # Load dataset
    dataset = load_dataset("json", data_files=dataset_path)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
        warmup_steps=100
    )
    
    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"]
    )
    
    trainer.train()
    trainer.save_model(output_dir)
    print(f"✅ Mistral model saved to {output_dir}")


# ============================================================================
# 2. PHI-3 INTEGRATION
# ============================================================================

def prepare_phi3_dataset(
    source_dataset: str,
    output_file: str,
    max_length: int = 2048
) -> None:
    """
    Prepare PeachTree dataset for Phi-3 fine-tuning.
    
    Phi-3 uses a specific format and has 2K context window.
    
    Args:
        source_dataset: Path to PeachTree JSONL dataset
        output_file: Output file for Phi-3 training
        max_length: Maximum sequence length (Phi-3 supports 2K/4K)
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # Phi-3 format
                phi3_record = {
                    "conversations": [
                        {
                            "from": "human",
                            "value": record.get("instruction", "")
                        },
                        {
                            "from": "gpt",
                            "value": record.get("response", "")
                        }
                    ],
                    "source": record.get("source_repo"),
                    "quality": record.get("quality_score", 0)
                }
                
                # Skip if too long for Phi-3 context
                text_length = len(record.get("instruction", "")) + len(record.get("response", ""))
                if text_length <= max_length * 4:  # Rough char to token estimate
                    records.append(phi3_record)
    
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ Phi-3 dataset ready: {len(records)} conversations")


# ============================================================================
# 3. GEMMA INTEGRATION
# ============================================================================

def prepare_gemma_dataset(
    source_dataset: str,
    output_file: str
) -> None:
    """
    Prepare PeachTree dataset for Gemma fine-tuning.
    
    Gemma uses instruction format similar to Alpaca.
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # Gemma instruction format
                gemma_record = {
                    "instruction": record.get("instruction", ""),
                    "input": "",  # Gemma separates input from instruction
                    "output": record.get("response", ""),
                    "metadata": {
                        "source": record.get("source_repo"),
                        "license": record.get("license"),
                        "provenance": record.get("provenance", {})
                    }
                }
                records.append(gemma_record)
    
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ Gemma dataset ready: {len(records)} instructions")


def train_gemma_model(
    dataset_path: str,
    model_name: str = "google/gemma-7b",
    output_dir: str = "models/gemma-security"
) -> None:
    """
    Train Gemma model with PeachTree security dataset.
    
    Uses Google's Gemma architecture with LoRA.
    """
    
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        TrainingArguments,
        Trainer
    )
    from peft import LoraConfig, get_peft_model
    from datasets import load_dataset
    
    # Load Gemma model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype="auto"
    )
    
    # LoRA config for Gemma
    lora_config = LoraConfig(
        r=32,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    
    # Load and train
    dataset = load_dataset("json", data_files=dataset_path)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=16,
        num_train_epochs=2,
        learning_rate=1e-4,
        logging_steps=10,
        save_steps=100
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"]
    )
    
    trainer.train()
    trainer.save_model(output_dir)
    print(f"✅ Gemma model saved to {output_dir}")


# ============================================================================
# 4. LLAMA-3 INTEGRATION
# ============================================================================

def prepare_llama3_dataset(
    source_dataset: str,
    output_file: str,
    system_prompt: str = "You are a cybersecurity expert AI assistant."
) -> None:
    """
    Prepare PeachTree dataset for Llama-3 fine-tuning.
    
    Llama-3 uses a specific chat template format.
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # Llama-3 chat format
                llama3_record = {
                    "text": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
                            f"<|start_header_id|>user<|end_header_id|>\n\n{record.get('instruction', '')}<|eot_id|>"
                            f"<|start_header_id|>assistant<|end_header_id|>\n\n{record.get('response', '')}<|eot_id|>",
                    "metadata": {
                        "id": record.get("id"),
                        "source": record.get("source_repo"),
                        "quality": record.get("quality_score", 0)
                    }
                }
                records.append(llama3_record)
    
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ Llama-3 dataset ready: {len(records)} examples")


# ============================================================================
# 5. CLAUDE (ANTHROPIC) FINE-TUNING INTEGRATION
# ============================================================================

def prepare_claude_dataset(
    source_dataset: str,
    output_file: str
) -> None:
    """
    Prepare PeachTree dataset for Claude fine-tuning via Anthropic API.
    
    Claude uses a specific JSONL format for fine-tuning.
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # Claude fine-tuning format
                claude_record = {
                    "prompt": f"\n\nHuman: {record.get('instruction', '')}\n\nAssistant:",
                    "completion": f" {record.get('response', '')}",
                    "metadata": {
                        "source_repo": record.get("source_repo"),
                        "license": record.get("license"),
                        "quality_score": record.get("quality_score", 0)
                    }
                }
                records.append(claude_record)
    
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ Claude dataset ready: {len(records)} prompt-completion pairs")


# ============================================================================
# 6. OPENAI GPT FINE-TUNING INTEGRATION
# ============================================================================

def prepare_openai_dataset(
    source_dataset: str,
    output_file: str,
    system_prompt: str = "You are a helpful cybersecurity AI assistant."
) -> None:
    """
    Prepare PeachTree dataset for OpenAI GPT fine-tuning.
    
    OpenAI uses chat completion format for fine-tuning.
    """
    
    records = []
    with open(source_dataset) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                
                # OpenAI chat completion format
                openai_record = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": record.get("instruction", "")},
                        {"role": "assistant", "content": record.get("response", "")}
                    ]
                }
                records.append(openai_record)
    
    Path(output_file).write_text('\n'.join(json.dumps(r) for r in records))
    print(f"✅ OpenAI dataset ready: {len(records)} conversations")
    print(f"Upload to OpenAI: openai api fine_tuning.jobs.create -t {output_file} -m gpt-3.5-turbo")


# ============================================================================
# 7. UNIFIED EXPORT FUNCTION
# ============================================================================

def export_for_framework(
    source_dataset: str,
    framework: str,
    output_file: str,
    **kwargs
) -> None:
    """
    Unified export function for all supported frameworks.
    
    Args:
        source_dataset: Path to PeachTree JSONL dataset
        framework: Target framework (mistral, phi3, gemma, llama3, claude, openai, hancock)
        output_file: Output file path
        **kwargs: Framework-specific arguments
    """
    
    framework = framework.lower()
    
    if framework == "mistral":
        prepare_mistral_dataset(source_dataset, output_file, **kwargs)
    elif framework == "phi3":
        prepare_phi3_dataset(source_dataset, output_file, **kwargs)
    elif framework == "gemma":
        prepare_gemma_dataset(source_dataset, output_file, **kwargs)
    elif framework == "llama3":
        prepare_llama3_dataset(source_dataset, output_file, **kwargs)
    elif framework == "claude":
        prepare_claude_dataset(source_dataset, output_file, **kwargs)
    elif framework == "openai":
        prepare_openai_dataset(source_dataset, output_file, **kwargs)
    elif framework == "hancock":
        # Hancock uses same format as Llama (based on Llama-2)
        prepare_llama3_dataset(source_dataset, output_file, **kwargs)
    else:
        raise ValueError(f"Unsupported framework: {framework}")
    
    print(f"✅ Dataset exported for {framework.upper()}")


# ============================================================================
# 8. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    
    # Source PeachTree dataset
    source = "data/datasets/multi-org-security-training.jsonl"
    
    # Export for different frameworks
    export_for_framework(
        source,
        framework="mistral",
        output_file="data/exports/mistral-security.jsonl",
        system_prompt="You are Mistral Security Assistant"
    )
    
    export_for_framework(
        source,
        framework="phi3",
        output_file="data/exports/phi3-security.jsonl",
        max_length=2048
    )
    
    export_for_framework(
        source,
        framework="gemma",
        output_file="data/exports/gemma-security.jsonl"
    )
    
    export_for_framework(
        source,
        framework="llama3",
        output_file="data/exports/llama3-security.jsonl"
    )
    
    export_for_framework(
        source,
        framework="claude",
        output_file="data/exports/claude-security.jsonl"
    )
    
    export_for_framework(
        source,
        framework="openai",
        output_file="data/exports/openai-security.jsonl"
    )
    
    export_for_framework(
        source,
        framework="hancock",
        output_file="data/exports/hancock-security.jsonl",
        system_prompt="You are Hancock, a cybersecurity AI assistant."
    )
    
    print("\n✅ All framework exports complete!")
    print("\nNext steps:")
    print("1. Mistral: Use Hugging Face Trainer with LoRA")
    print("2. Phi-3: Fine-tune with Microsoft's Phi-3 tools")
    print("3. Gemma: Use Google's Gemma fine-tuning pipeline")
    print("4. Llama-3: Use Meta's Llama recipes")
    print("5. Claude: Upload to Anthropic fine-tuning API")
    print("6. OpenAI: Use OpenAI fine-tuning API")
    print("7. Hancock: Custom Llama-2 based security LLM")
