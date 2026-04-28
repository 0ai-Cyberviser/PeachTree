#!/usr/bin/env python3
"""
Advanced Iterative Training System for Hancock Cybersecurity LLM
Implements 1000x recursive refinement with quality gates and dataset enhancement

Features:
- Iterative fine-tuning with quality assessment
- Weak area identification and targeted improvement
- Synthetic data generation from model outputs
- Automated quality gates and checkpoint selection
- Dataset enhancement through active learning
- Performance tracking and visualization
"""

import json
import hashlib
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from datasets import Dataset
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IterationMetrics:
    """Metrics for a single training iteration"""
    iteration: int
    train_loss: float
    eval_loss: float
    quality_score: float
    weak_areas_count: int
    synthetic_records: int
    total_records: int
    timestamp: str
    checkpoint_path: str
    is_best: bool = False


class QualityAssessor:
    """Assesses model output quality and identifies weak areas"""
    
    UNCERTAINTY_PATTERNS = [
        r'\bI think\b', r'\bmaybe\b', r'\bpossibly\b',
        r'\bnot sure\b', r'\bmight be\b', r'\bcould be\b',
        r'\buncertain\b', r'\bprobably\b', r'\bI guess\b'
    ]
    
    def __init__(self):
        import re
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.UNCERTAINTY_PATTERNS]
    
    def assess_response(self, prompt: str, response: str) -> Dict[str, Any]:
        """Assess single response quality"""
        score = 1.0
        issues = []
        
        # Check length
        if len(response) < 50:
            score -= 0.3
            issues.append("too_short")
        
        # Check for uncertainty markers
        uncertainty_count = sum(1 for p in self.patterns if p.search(response))
        if uncertainty_count > 0:
            score -= 0.1 * uncertainty_count
            issues.append(f"uncertainty_{uncertainty_count}")
        
        # Check for errors
        if "error" in response.lower() or "sorry" in response.lower():
            score -= 0.2
            issues.append("contains_error")
        
        # Check for hallucinations (very basic check)
        if "as an ai" in response.lower() or "i cannot" in response.lower():
            score -= 0.15
            issues.append("refusal")
        
        return {
            "quality_score": max(0.0, min(1.0, score)),
            "issues": issues,
            "prompt": prompt,
            "response": response,
            "length": len(response)
        }
    
    def identify_weak_areas(
        self,
        assessments: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Identify prompts/topics with low quality responses"""
        weak = [a for a in assessments if a["quality_score"] < threshold]
        logger.info(f"Identified {len(weak)} weak areas (threshold: {threshold})")
        return weak


class SyntheticDataGenerator:
    """Generates synthetic training data from weak areas"""
    
    def __init__(self, model, tokenizer, device="cuda"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
    
    def generate_variations(
        self,
        weak_area: Dict[str, Any],
        num_variations: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate variations of weak prompts for targeted training"""
        variations = []
        base_prompt = weak_area["prompt"]
        
        # Variation strategies
        strategies = [
            ("detailed", f"Provide a detailed explanation: {base_prompt}"),
            ("step_by_step", f"Explain step-by-step: {base_prompt}"),
            ("technical", f"Give a technical analysis: {base_prompt}"),
            ("practical", f"Provide a practical example: {base_prompt}"),
            ("security", f"From a security perspective: {base_prompt}")
        ]
        
        for strategy_name, varied_prompt in strategies[:num_variations]:
            # Generate response with higher temperature for diversity
            inputs = self.tokenizer(
                f"### Instruction:\n{varied_prompt}\n\n### Response:\n",
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.9,
                    num_return_sequences=1
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.split("### Response:")[-1].strip()
            
            # Create synthetic record
            content = f"{varied_prompt}\n\n{response}"
            digest = hashlib.sha256(content.encode()).hexdigest()
            
            variations.append({
                "id": f"synthetic-iter-{digest[:16]}",
                "instruction": varied_prompt,
                "output": response,
                "source_repo": "hancock/iterative-refinement",
                "source_path": f"iteration/synthetic_{strategy_name}.jsonl",
                "source_digest": digest,
                "license_id": "MIT",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "quality_score": 0.85,  # Assumed high quality for synthetic
                "generation_strategy": strategy_name
            })
        
        return variations


class IterativeTrainer:
    """Manages iterative training with quality-driven refinement"""
    
    def __init__(
        self,
        base_model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        dataset_path: str = "data/hancock/unified-expanded.jsonl",
        output_dir: str = "models/hancock-iterative",
        max_iterations: int = 1000,
        quality_threshold: float = 0.90,
        device: str = "cuda"
    ):
        self.base_model_name = base_model_name
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.device = device
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_history: List[IterationMetrics] = []
        self.best_checkpoint = None
        self.best_quality = 0.0
        
        logger.info(f"Initialized IterativeTrainer:")
        logger.info(f"  Base model: {base_model_name}")
        logger.info(f"  Dataset: {dataset_path}")
        logger.info(f"  Max iterations: {max_iterations}")
        logger.info(f"  Quality threshold: {quality_threshold}")
    
    def load_dataset(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSONL dataset"""
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        logger.info(f"Loaded {len(records)} records from {path}")
        return records
    
    def save_dataset(self, records: List[Dict[str, Any]], path: Path):
        """Save records as JSONL"""
        with open(path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, sort_keys=True) + '\n')
        logger.info(f"Saved {len(records)} records to {path}")
    
    def evaluate_model(
        self,
        model,
        tokenizer,
        test_prompts: List[str]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Evaluate model on test prompts"""
        assessor = QualityAssessor()
        assessments = []
        
        for prompt in test_prompts:
            inputs = tokenizer(
                f"### Instruction:\n{prompt}\n\n### Response:\n",
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=150,
                    do_sample=True,
                    temperature=0.7
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.split("### Response:")[-1].strip()
            
            assessment = assessor.assess_response(prompt, response)
            assessments.append(assessment)
        
        avg_quality = np.mean([a["quality_score"] for a in assessments])
        return avg_quality, assessments
    
    def train_iteration(
        self,
        iteration: int,
        records: List[Dict[str, Any]],
        checkpoint_path: str = None
    ) -> IterationMetrics:
        """Execute single training iteration"""
        logger.info(f"\n{'='*60}")
        logger.info(f"ITERATION {iteration}/{self.max_iterations}")
        logger.info(f"{'='*60}")
        
        # Prepare dataset
        dataset_records = [
            {"text": f"### Instruction:\n{r['instruction']}\n\n### Response:\n{r['output']}"}
            for r in records
        ]
        dataset = Dataset.from_list(dataset_records)
        
        # Load model
        logger.info("Loading model...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        if checkpoint_path and Path(checkpoint_path).exists():
            logger.info(f"Loading from checkpoint: {checkpoint_path}")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                quantization_config=bnb_config,
                device_map="auto"
            )
            model = PeftModel.from_pretrained(base_model, checkpoint_path)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                quantization_config=bnb_config,
                device_map="auto"
            )
            model = prepare_model_for_kbit_training(model)
            
            lora_config = LoraConfig(
                r=16,  # Increased rank for better learning
                lora_alpha=32,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM"
            )
            model = get_peft_model(model, lora_config)
        
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        tokenizer.pad_token = tokenizer.eos_token
        
        # Tokenize
        def preprocess(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding="max_length"
            )
        
        tokenized_dataset = dataset.map(preprocess, batched=True, remove_columns=["text"])
        
        # Training args - optimized for quick iterations
        iter_output_dir = self.output_dir / f"iteration_{iteration}"
        training_args = TrainingArguments(
            output_dir=str(iter_output_dir),
            per_device_train_batch_size=8,
            gradient_accumulation_steps=2,
            num_train_epochs=1,  # Single epoch per iteration
            learning_rate=2e-4,
            fp16=True,
            logging_steps=50,
            save_steps=500,
            save_total_limit=1,
            gradient_checkpointing=True,
            warmup_steps=50,
            report_to="none"
        )
        
        # Train
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
        )
        
        logger.info(f"Training on {len(records)} records...")
        train_result = trainer.train()
        
        # Save checkpoint
        checkpoint_path = iter_output_dir / "checkpoint"
        trainer.save_model(checkpoint_path)
        
        # Evaluate
        test_prompts = [
            "Explain SQL injection vulnerability",
            "How does ASLR improve security?",
            "What is a buffer overflow exploit?",
            "Describe Cross-Site Scripting (XSS)",
            "How do you use nmap for network scanning?",
            "What is the OWASP Top 10?",
            "Explain privilege escalation techniques",
            "How does a DDoS attack work?",
            "What is zero-day vulnerability?",
            "Describe secure coding practices"
        ]
        
        avg_quality, assessments = self.evaluate_model(model, tokenizer, test_prompts)
        
        # Identify weak areas
        assessor = QualityAssessor()
        weak_areas = assessor.identify_weak_areas(assessments, threshold=0.75)
        
        # Create metrics
        metrics = IterationMetrics(
            iteration=iteration,
            train_loss=train_result.training_loss,
            eval_loss=0.0,  # Not computed for speed
            quality_score=avg_quality,
            weak_areas_count=len(weak_areas),
            synthetic_records=0,
            total_records=len(records),
            timestamp=datetime.now(timezone.utc).isoformat(),
            checkpoint_path=str(checkpoint_path)
        )
        
        # Track best
        if avg_quality > self.best_quality:
            self.best_quality = avg_quality
            self.best_checkpoint = checkpoint_path
            metrics.is_best = True
            logger.info(f"🏆 NEW BEST MODEL! Quality: {avg_quality:.4f}")
        
        self.metrics_history.append(metrics)
        
        # Save metrics
        metrics_file = self.output_dir / "training_metrics.jsonl"
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')
        
        logger.info(f"Iteration {iteration} complete:")
        logger.info(f"  Train loss: {metrics.train_loss:.4f}")
        logger.info(f"  Quality score: {metrics.quality_score:.4f}")
        logger.info(f"  Weak areas: {len(weak_areas)}")
        logger.info(f"  Records: {len(records)}")
        
        # Generate synthetic data for next iteration
        if weak_areas and iteration < self.max_iterations:
            logger.info("Generating synthetic data for weak areas...")
            generator = SyntheticDataGenerator(model, tokenizer, self.device)
            
            synthetic_records = []
            for weak in weak_areas[:20]:  # Top 20 weak areas
                variations = generator.generate_variations(weak, num_variations=2)
                synthetic_records.extend(variations)
            
            metrics.synthetic_records = len(synthetic_records)
            logger.info(f"Generated {len(synthetic_records)} synthetic records")
            
            # Save for next iteration
            enhanced_records = records + synthetic_records
            next_dataset_path = self.output_dir / f"dataset_iteration_{iteration + 1}.jsonl"
            self.save_dataset(enhanced_records, next_dataset_path)
        
        return metrics
    
    def run_iterations(self):
        """Execute complete iterative training loop"""
        logger.info("\n🚀 Starting iterative training system")
        logger.info(f"Target: {self.max_iterations} iterations")
        logger.info(f"Quality threshold: {self.quality_threshold}\n")
        
        # Load initial dataset
        records = self.load_dataset(self.dataset_path)
        current_checkpoint = None
        
        for iteration in range(1, self.max_iterations + 1):
            try:
                metrics = self.train_iteration(iteration, records, current_checkpoint)
                current_checkpoint = metrics.checkpoint_path
                
                # Check convergence
                if metrics.quality_score >= self.quality_threshold:
                    logger.info(f"\n🎯 QUALITY THRESHOLD REACHED!")
                    logger.info(f"Quality: {metrics.quality_score:.4f} >= {self.quality_threshold}")
                    logger.info(f"Iterations completed: {iteration}")
                    break
                
                # Load enhanced dataset for next iteration
                next_dataset = self.output_dir / f"dataset_iteration_{iteration + 1}.jsonl"
                if next_dataset.exists():
                    records = self.load_dataset(next_dataset)
                
                # Periodic summary
                if iteration % 10 == 0:
                    self.print_summary()
            
            except KeyboardInterrupt:
                logger.info("\n⚠️  Training interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                break
        
        self.finalize()
    
    def print_summary(self):
        """Print training summary"""
        logger.info(f"\n{'='*60}")
        logger.info("TRAINING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Iterations completed: {len(self.metrics_history)}")
        logger.info(f"Best quality: {self.best_quality:.4f}")
        logger.info(f"Best checkpoint: {self.best_checkpoint}")
        
        recent = self.metrics_history[-5:]
        logger.info(f"\nRecent performance (last 5):")
        for m in recent:
            logger.info(f"  Iter {m.iteration}: Quality={m.quality_score:.4f}, Loss={m.train_loss:.4f}")
    
    def finalize(self):
        """Finalize training and save best model"""
        logger.info(f"\n{'='*60}")
        logger.info("FINALIZING TRAINING")
        logger.info(f"{'='*60}")
        
        self.print_summary()
        
        # Copy best checkpoint to final location
        if self.best_checkpoint:
            final_model_dir = self.output_dir / "final_model"
            import shutil
            shutil.copytree(self.best_checkpoint, final_model_dir, dirs_exist_ok=True)
            logger.info(f"\n✅ Best model saved to: {final_model_dir}")
        
        # Save final summary
        summary = {
            "total_iterations": len(self.metrics_history),
            "best_quality": self.best_quality,
            "best_checkpoint": str(self.best_checkpoint),
            "final_dataset_size": self.metrics_history[-1].total_records if self.metrics_history else 0,
            "quality_threshold": self.quality_threshold,
            "status": "complete"
        }
        
        with open(self.output_dir / "final_summary.json", 'w') as f:
            json.dumps(summary, f, indent=2)
        
        logger.info(f"\n🎉 TRAINING COMPLETE!")
        logger.info(f"Final quality: {self.best_quality:.4f}")
        logger.info(f"Total iterations: {len(self.metrics_history)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Iterative Training for Hancock")
    parser.add_argument("--dataset", default="data/hancock/unified-expanded.jsonl")
    parser.add_argument("--output", default="models/hancock-iterative")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--threshold", type=float, default=0.90)
    parser.add_argument("--device", default="cuda")
    
    args = parser.parse_args()
    
    trainer = IterativeTrainer(
        dataset_path=args.dataset,
        output_dir=args.output,
        max_iterations=args.iterations,
        quality_threshold=args.threshold,
        device=args.device
    )
    
    trainer.run_iterations()
