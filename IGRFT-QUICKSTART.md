# Inference-Guided Recursive Fine-Tuning (IGRFT)

## Revolutionary CPU-Optimized AI Training Method

IGRFT is a novel approach to fine-tuning AI models that:
- **Learns from its own inferences** through recursive feedback loops
- **Works efficiently on CPU** using QLoRA 4-bit quantization
- **Automatically identifies weak areas** and generates targeted training data
- **Integrates with PeachTree's dataset pipeline** for provenance tracking

## How It Works

### The Recursive Learning Cycle

```
1. INFERENCE
   ↓
   Generate responses to test prompts
   ↓
2. ANALYSIS
   ↓
   Identify uncertainty, weak areas, low-quality outputs
   ↓
3. AUGMENTATION
   ↓
   Create synthetic training data targeting weaknesses
   ↓
4. TRAINING
   ↓
   Fine-tune with LoRA adapters using augmented dataset
   ↓
5. REPEAT → Next cycle uses improved model
```

### Key Innovations

**1. Self-Supervised Improvement**
- Model evaluates its own outputs
- Identifies areas of uncertainty
- Generates better training examples

**2. CPU-Optimized Training**
```python
# Techniques used:
- 4-bit quantization (QLoRA)
- LoRA adapters (r=8, alpha=16)
- Gradient checkpointing
- Batch size 1 + gradient accumulation
- BFloat16 precision
- Optimized for 4-8 CPU cores
```

**3. Iterative Refinement**
- Each cycle builds on previous improvements
- Weak areas from cycle N are targeted in cycle N+1
- Progressive quality improvement

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install transformers peft bitsandbytes accelerate datasets

# Optional but recommended
pip install sentencepiece protobuf torch
```

### 2. Run IGRFT Pipeline

```bash
# Basic usage
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/unified-expanded.jsonl \
    --cycles 5

# With custom settings
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/unified-expanded.jsonl \
    --cycles 10 \
    --output-dir data/hancock/igrft \
    --verbose
```

### 3. Execute Training Cycles

The pipeline generates training scripts for each cycle:

```bash
# Train cycle 1
python models/igrft-cycles/train_cycle_1.py

# Train cycle 2 (uses cycle 1's model)
python models/igrft-cycles/train_cycle_2.py

# ... and so on
```

### 4. Monitor Progress

```bash
# View summary
cat data/hancock/igrft/igrft_summary.json | jq .

# Check cycle metadata
cat data/hancock/igrft/cycle_1_metadata.json | jq .

# View training logs
tail -f models/igrft-cycles/cycle-1/training.log
```

## VS Code Integration

Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on Mac) to access build tasks:

- **IGRFT: Quick Start (5 cycles)** - Run complete pipeline
- **IGRFT: Train Cycle 1** - Execute training for cycle 1
- **IGRFT: Analyze Results** - View summary JSON
- **IGRFT: Install Dependencies** - Set up Python packages

## Architecture

### Main Components

**1. InferenceAnalyzer**
- Analyzes model outputs for quality
- Identifies uncertainty patterns
- Scores responses (0.0-1.0)
- Extracts topics/weak areas

**2. SyntheticDataGenerator**
- Creates training records from inferences
- Enhances weak responses
- Generates variations for augmentation
- Maintains PeachTree provenance format

**3. CPUOptimizedTrainer**
- Generates QLoRA training scripts
- Configures 4-bit quantization
- Sets CPU-optimal hyperparameters
- Manages LoRA adapters per cycle

**4. InferenceRecursiveLearning (Orchestrator)**
- Coordinates the full pipeline
- Manages cycle execution
- Tracks improvements
- Generates reports

### Data Flow

```
Base Dataset (JSONL)
    ↓
Inference Batch → InferenceResults[]
    ↓
Analysis → weak_areas[], quality_scores[]
    ↓
Augmentation → synthetic_records[]
    ↓
Merge → cycle_training_dataset.jsonl
    ↓
Training → LoRA adapter
    ↓
Next Cycle (uses new adapter)
```

## CPU Training Optimizations

### Memory Efficiency

**4-bit Quantization (QLoRA)**:
- Reduces model size from 14GB to ~4GB
- Uses NF4 quantization type
- Double quantization for extra compression

**LoRA Adapters**:
- Only trains small adapters (~8MB)
- Rank 8 = minimal parameters
- Targets query/key/value/output projections only

### Speed Optimizations

**Gradient Checkpointing**:
- Trades computation for memory
- Enables larger models on CPU

**Gradient Accumulation**:
- Effective batch size 8 (1 × 8 accumulation)
- Simulates larger batches without memory cost

**BFloat16**:
- Better than FP16 for CPU
- Maintains numerical stability

### Hardware Requirements

**Minimum**:
- 16GB RAM
- 4 CPU cores
- 10GB disk space

**Recommended**:
- 32GB RAM
- 8+ CPU cores
- 50GB disk space (for multiple cycles)

**Expected Performance**:
- ~100 steps per cycle
- ~10-20 minutes per cycle (CPU-dependent)
- ~50-100 minutes for full 5-cycle pipeline

## Example Workflow

### Scenario: Bug Bounty Training

```bash
# 1. Start with your bug bounty dataset
ls data/hancock/unified-expanded.jsonl
# 15 records (HackerOne, Bugcrowd, enterprise programs)

# 2. Run IGRFT pipeline
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/unified-expanded.jsonl \
    --cycles 5 \
    --verbose

# Output:
# - 5 augmented training datasets
# - 5 training scripts
# - Cycle metadata files
# - Final summary report

# 3. Execute first cycle training
python models/igrft-cycles/train_cycle_1.py

# 4. Continue with subsequent cycles
python models/igrft-cycles/train_cycle_2.py
python models/igrft-cycles/train_cycle_3.py
# ...

# 5. Use the final adapter
# models/igrft-cycles/cycle-5/adapter/
```

### Expected Results

**Cycle 1**:
- Base dataset: 15 records
- Augmented: +10 synthetic records
- Training: 25 records total

**Cycle 2**:
- Uses cycle 1 adapter
- Identifies remaining weak areas
- Augmented: +8 records
- Training: 33 records total

**Cycle 3-5**:
- Progressive refinement
- Fewer weak areas each cycle
- Higher quality synthetic data
- Improved model performance

## Advanced Usage

### Custom Inference Function

```python
from peachtree.inference_recursive_learning import InferenceRecursiveLearning

# Implement custom inference
def my_inference_fn(prompts, model_path):
    # Your inference logic here
    # Return List[InferenceResult]
    pass

igrft = InferenceRecursiveLearning(
    base_dataset_path=Path("data/hancock/unified-expanded.jsonl"),
    max_cycles=5
)

# Override inference method
igrft.run_inference_batch = my_inference_fn

# Run pipeline
summary = igrft.run_full_pipeline()
```

### Custom Analysis Rules

```python
from peachtree.inference_recursive_learning import InferenceAnalyzer

analyzer = InferenceAnalyzer()

# Add custom uncertainty patterns
analyzer.UNCERTAINTY_PATTERNS.extend([
    r"approximately",
    r"roughly",
    r"estimate"
])

# Use in pipeline
igrft.analyzer = analyzer
```

### Integration with PeachTree CLI

```bash
# Generate base dataset with PeachTree
peachtree hancock-workflow \
    --hancock-dir ~/Hancock/data \
    --output-dir data/hancock \
    --min-quality-score 0.70

# Run IGRFT on result
python -m peachtree.inference_recursive_learning \
    --dataset data/hancock/training.jsonl \
    --cycles 5

# Score final augmented dataset
peachtree security-score \
    --dataset data/hancock/igrft/cycle_5_training.jsonl \
    --format json

# Create trainer handoff
peachtree handoff \
    --dataset data/hancock/igrft/cycle_5_training.jsonl \
    --output trainer-handoff-igrft.json
```

## Troubleshooting

### Out of Memory

```bash
# Reduce batch size (already at 1)
# Increase gradient accumulation
# Use smaller model
# Close other applications
```

### Slow Training

```bash
# Expected: 10-20 min per cycle on CPU
# Reduce max_steps in training config
# Use fewer cycles initially
# Verify CPU core usage (should use 4-8 cores)
```

### Import Errors

```bash
# Install all dependencies
pip install transformers peft bitsandbytes accelerate datasets

# Verify installation
python -c "import transformers; print(transformers.__version__)"
python -c "import peft; print(peft.__version__)"
```

## Comparison with Traditional Fine-Tuning

| Aspect | Traditional | IGRFT |
|--------|------------|-------|
| Hardware | GPU required | CPU works |
| Memory | 24GB+ VRAM | 16GB RAM |
| Dataset | Static | Dynamically augmented |
| Improvement | Single pass | Recursive refinement |
| Weak Areas | Manual identification | Automatic |
| Cost | High (GPU rental) | Low (local CPU) |
| Time per cycle | ~30 min | ~10-20 min |

## Next Steps

1. **Run the pipeline**: Start with 3-5 cycles
2. **Evaluate results**: Check cycle metadata
3. **Fine-tune config**: Adjust learning rate, steps
4. **Scale up**: Increase cycles for better results
5. **Deploy adapter**: Use with base model for inference

## Research & Development

This is an experimental approach. Key areas for improvement:

- **Better inference analysis**: More sophisticated quality metrics
- **Smarter augmentation**: Advanced synthetic data generation
- **Parallel cycles**: Train multiple cycles simultaneously
- **Online learning**: Continuous inference→training loops
- **Meta-learning**: Learn optimal augmentation strategies

## Resources

- **Code**: `src/peachtree/inference_recursive_learning.py`
- **VS Code Tasks**: `.vscode/tasks.json`
- **Output**: `data/hancock/igrft/`
- **Models**: `models/igrft-cycles/`

## Support

For questions or issues:
- Check `TROUBLESHOOTING.md`
- Review cycle metadata files
- Enable `--verbose` flag for detailed logs
- Examine training script outputs

---

**Created**: April 28, 2026
**Status**: ✅ Experimental - Ready for testing
**License**: MIT

