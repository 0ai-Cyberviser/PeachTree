# PeachTree Quick Start: Security Dataset

**Get started with the multi-org security dataset in 5 minutes**

## Prerequisites

```bash
# Python 3.10+ required
python --version

# Install PeachTree
pip install peachtree-ai
# OR install from source
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree
pip install -e ".[dev]"
```

## Option 1: Use Pre-Built Dataset (Fastest)

The security dataset is ready to use immediately:

```bash
# Clone the repository
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree

# The dataset is already built!
ls -lh data/datasets/multi-org-security-training.jsonl  # 7,202 records
ls -lh data/manifests/hancock-chatml-export.jsonl      # Ready for training
```

### Inspect the Dataset

```bash
# Show dataset statistics
peachtree audit --dataset data/datasets/multi-org-security-training.jsonl

# View first record
head -1 data/datasets/multi-org-security-training.jsonl | python -m json.tool

# Count records
wc -l data/datasets/multi-org-security-training.jsonl

# View build manifest (provenance)
cat data/manifests/multi-org-build-manifest.json | python -m json.tool | head -50
```

### Use with Hancock LLM

```bash
# The ChatML export is ready for training
hancock train \
  --dataset data/manifests/hancock-chatml-export.jsonl \
  --model meta-llama/Llama-2-13b-chat-hf \
  --output models/hancock-security-v1

# Or use the integration example
python examples/hancock_integration.py
```

## Option 2: Rebuild from Source

Rebuild the dataset from the 7 security repositories:

```bash
cd PeachTree

# Run the automated build script
bash scripts/build-multi-org-dataset.sh

# This will:
# 1. Clone all 7 security repositories (~2 GB)
# 2. Ingest documentation and code
# 3. Apply safety gates
# 4. Build unified dataset
# 5. Export to ChatML format
```

## Option 3: Build Custom Dataset

Use PeachTree to build your own security dataset:

### Step 1: Ingest Your Repositories

```bash
# Ingest a local repository
peachtree ingest-local \
  --repo /path/to/your-security-repo \
  --repo-name "your-repo-name" \
  --license MIT \
  --output data/raw/your-repo.jsonl
```

### Step 2: Build Dataset

```bash
# Build from multiple sources
peachtree build \
  --source data/raw/your-repo.jsonl \
  --source data/raw/another-repo.jsonl \
  --dataset data/datasets/custom-security.jsonl \
  --manifest data/manifests/custom-manifest.json \
  --domain security
```

### Step 3: Apply Policy Pack

```bash
# Check compliance with security policies
peachtree policy-pack \
  --dataset data/datasets/custom-security.jsonl \
  --policy config/policy-packs/security-domain-compliance.json \
  --output reports/policy-compliance.json
```

### Step 4: Audit Quality

```bash
# Run quality checks
peachtree audit --dataset data/datasets/custom-security.jsonl

# Check for duplicates
peachtree dedup --dataset data/datasets/custom-security.jsonl

# Generate quality score
peachtree score --dataset data/datasets/custom-security.jsonl
```

### Step 5: Export for Training

```bash
# Export to ChatML format
peachtree export \
  --source data/datasets/custom-security.jsonl \
  --output data/manifests/custom-chatml.jsonl \
  --format chatml

# Or export to Alpaca format
peachtree export \
  --source data/datasets/custom-security.jsonl \
  --output data/manifests/custom-alpaca.jsonl \
  --format alpaca
```

## Common Tasks

### View Dataset Statistics

```bash
# Audit report
peachtree audit --dataset data/datasets/multi-org-security-training.jsonl

# Output:
# {
#   "dataset": "data/datasets/multi-org-security-training.jsonl",
#   "records": 7202,
#   "unique_ids": 7202,
#   "duplicates": 0,
#   "has_provenance": true,
#   "min_quality_score": 0.85
# }
```

### Check Data Lineage

```bash
# View source attribution
peachtree lineage \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --manifest data/manifests/multi-org-build-manifest.json

# View dependency graph
peachtree graph \
  --dataset-dir data/datasets \
  --manifest-dir data/manifests \
  --format mermaid
```

### Generate Model Card

```bash
# Auto-generate model card
peachtree model-card \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --manifest data/manifests/multi-org-build-manifest.json \
  --output MODEL-CARD.md
```

### Create Release Bundle

```bash
# Package dataset for distribution
peachtree bundle \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --manifest data/manifests/multi-org-build-manifest.json \
  --output releases/security-dataset-v1.0.tar.gz \
  --sign

# Generate SBOM
peachtree sbom \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --output reports/sbom.json
```

## Troubleshooting

### Issue: "IsADirectoryError" during build

**Problem:** Passing directories instead of JSONL files to `--source`

**Solution:** Use `ingest-local` first to create JSONL files:

```bash
# WRONG: Don't pass directories
peachtree build --source /tmp/datasets/repo-name

# RIGHT: Use JSONL files from ingest step
peachtree ingest-local --repo /tmp/datasets/repo-name --output data/raw/repo.jsonl
peachtree build --source data/raw/repo.jsonl
```

### Issue: "Missing instruction" error on export

**Problem:** Dataset records don't have required fields for ChatML format

**Solution:** Ensure records have proper structure:

```bash
# Check record structure
head -1 data/datasets/your-dataset.jsonl | python -m json.tool

# Required fields for ChatML:
# - "instruction" or "user_query"
# - "content" or "response"
# - "source_repo" (for provenance)
```

### Issue: Duplicate records detected

**Problem:** Dataset contains duplicate content

**Solution:** Run deduplication:

```bash
# Remove duplicates
peachtree dedup \
  --dataset data/datasets/your-dataset.jsonl \
  --output data/datasets/your-dataset-deduped.jsonl
```

### Issue: Safety gate failures

**Problem:** Secrets or sensitive data detected

**Solution:** Review and fix:

```bash
# Run audit to see failures
peachtree audit --dataset data/datasets/your-dataset.jsonl

# View specific failures in manifest
cat data/manifests/your-manifest.json | jq '.safety_gate_results'
```

## Next Steps

### 1. Train Hancock LLM

```bash
# Use the pre-built dataset
python examples/hancock_integration.py

# Or use your custom dataset
hancock train \
  --dataset data/manifests/your-chatml-export.jsonl \
  --model meta-llama/Llama-2-13b-chat-hf
```

### 2. Set Up Automated Updates

```bash
# The dataset rebuilds monthly via GitHub Actions
# Manually trigger: gh workflow run rebuild-security-dataset.yml
```

### 3. Integrate with Your Workflow

```bash
# Add PeachTree to your CI/CD
# See: .github/workflows/rebuild-security-dataset.yml

# Use as a library in Python
from peachtree import DatasetBuilder, SafetyGate
from peachtree.models import SourceDocument

builder = DatasetBuilder(domain="security", safety_gate=SafetyGate())
# ... your code
```

### 4. Contribute Back

```bash
# Add your security repositories to the multi-org dataset
# Edit: config/multi-org-security-datasets.yaml
# Submit PR with new repositories
```

## Resources

- **Documentation:** https://0ai-cyberviser.github.io/PeachTree/
- **Model Card:** `MODEL-CARD-SECURITY-DATASET.md`
- **User Guide:** `MULTI-ORG-DATASET-README.md`
- **Policy Pack:** `config/policy-packs/security-domain-compliance.json`
- **Examples:** `examples/hancock_integration.py`
- **GitHub:** https://github.com/0ai-Cyberviser/PeachTree

## Support

- **Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues
- **Discussions:** https://github.com/0ai-Cyberviser/PeachTree/discussions

---

**🎉 You're ready to use the PeachTree security dataset!**

Start training Hancock or build your own custom security datasets with full provenance tracking and safety validation.
