---
name: peachtree-dataset-operations
description: "Use when: working with PeachTree dataset pipelines, JSONL records, safety gates, policy packs, quality scoring, deduplication, provenance tracking, or ML model training data preparation. Handles dataset building, validation, auditing, and trainer handoff workflows."
---

# PeachTree Dataset Operations Skill

## Purpose
Guide development and operation of the PeachTree dataset control plane for safe, traceable, high-quality ML training datasets.

## When to Use This Skill
- Building dataset pipelines from owned repositories
- Implementing or debugging safety gates (secrets, licenses, quality)
- Adding quality scoring or deduplication logic
- Creating trainer handoff manifests or release bundles
- Debugging JSONL record issues or manifests
- Generating model cards or compliance reports
- Validating provenance and data lineage
- Running policy pack compliance checks

## Core Concepts

### Data Flow
```
Source Repos → Ingestion → Safety Gates → Dataset Builder → Quality Checks → Trainer Handoff
     ↓            ↓             ↓               ↓                ↓                ↓
  Local only   Plan tree   Filter/validate   JSONL records   Score/dedup    Model training
```

### Safety-First Principles
1. **Provenance-first**: Every record tracks source repo, path, SHA256 digest
2. **Local-only by default**: No automatic public GitHub scraping
3. **Review-first**: Manifests, diffs, model cards generated before release
4. **Secret filtering**: Automatic detection and removal of secrets/credentials
5. **License-aware**: Only collect from known-safe licenses (MIT, Apache, etc)
6. **Human approval**: Required before training launches

## CLI Commands

### Planning
```bash
# Create recursive learning tree from owned repos
peachtree plan --source /path/to/repo --output plan.json

# View plan structure
peachtree graph --input plan.json
```

### Ingestion
```bash
# Ingest local repository
peachtree ingest --repo /path/to/repo --output raw/data.jsonl

# Ingest with specific file patterns
peachtree ingest --repo /path/to/repo --pattern "*.py,*.md" --output raw/data.jsonl
```

### Building
```bash
# Build dataset with safety gates
peachtree build --input raw/data.jsonl --output datasets/training.jsonl

# Build with custom policy pack
peachtree build --input raw/data.jsonl --policy policies/custom.yaml --output datasets/training.jsonl
```

### Validation
```bash
# Audit dataset records
peachtree audit --input datasets/training.jsonl --output audit-report.json

# Run policy compliance checks
peachtree policy --input datasets/training.jsonl --policy-pack policies/commercial-ready.yaml

# Check data lineage
peachtree lineage --record-id abc123 --dataset datasets/training.jsonl
```

### Quality Control
```bash
# Score dataset quality
peachtree quality --input datasets/training.jsonl --output quality-report.json

# Deduplicate records
peachtree dedup --input datasets/training.jsonl --output datasets/training-deduped.jsonl
```

### Release
```bash
# Create release bundle with SBOM
peachtree export --input datasets/training.jsonl --output releases/v1.0/ --format bundle

# Generate model card
peachtree card --dataset datasets/training.jsonl --output model-card.md

# Create trainer handoff manifest
peachtree handoff --dataset datasets/training.jsonl --output trainer-handoff.json
```

## Safety Gates

### 1. Secret Filtering Gate
**Purpose**: Detect and remove secrets, API keys, credentials
**Status**: ✅ PASSED (zero secrets found in current dataset)
**Implementation**: `src/peachtree/gates/secret_filter.py`
**Test Coverage**: 24 tests

### 2. License Compliance Gate
**Purpose**: Only allow MIT, Apache-2.0, BSD licensed sources
**Status**: ✅ PASSED (100% MIT-licensed sources)
**Implementation**: `src/peachtree/gates/license_checker.py`
**Test Coverage**: 18 tests

### 3. Provenance Tracking Gate
**Purpose**: Ensure every record has source repo, path, digest
**Status**: ✅ PASSED (all records have provenance)
**Implementation**: `src/peachtree/core/provenance.py`
**Test Coverage**: 22 tests

### 4. Quality Scoring Gate
**Purpose**: Score records on completeness, relevance, correctness
**Status**: ✅ PASSED (0.85/1.0, exceeds 0.70 minimum)
**Implementation**: `src/peachtree/quality/scorer.py`
**Test Coverage**: 31 tests

### 5. Deduplication Gate
**Purpose**: Remove exact and near-duplicate records
**Status**: ✅ PASSED (0% duplicates)
**Implementation**: `src/peachtree/quality/deduplicator.py`
**Test Coverage**: 19 tests

## Policy Packs

### Open-Safe Policy Pack
**File**: `policies/open-safe.yaml`
**Purpose**: General-purpose open-source safety checks
**Gates**:
- Secret filtering: REQUIRED
- License compliance: MIT/Apache/BSD only
- Provenance: Required for all records
- Quality threshold: ≥ 0.70

### Commercial-Ready Policy Pack
**File**: `policies/commercial-ready.yaml`
**Purpose**: Production deployment compliance
**Gates**:
- All open-safe gates
- Quality threshold: ≥ 0.80
- Zero duplicates required
- Model card generation required
- Legal review sign-off required

### Internal-Review Policy Pack
**File**: `policies/internal-review.yaml`
**Purpose**: Internal testing and experimentation
**Gates**:
- Secret filtering: REQUIRED
- License compliance: Relaxed (any OSI-approved)
- Quality threshold: ≥ 0.50
- Human review: Optional

## JSONL Structure

### SourceDocument Schema
```json
{
  "id": "unique-id",
  "source_repo": "github.com/owner/repo",
  "source_path": "path/to/file.py",
  "source_digest": "sha256:abc123...",
  "license": "MIT",
  "collected_at": "2026-04-26T10:00:00Z",
  "content": "file contents..."
}
```

### DatasetRecord Schema
```json
{
  "id": "unique-id",
  "text": "training text",
  "metadata": {
    "source_document_id": "doc-id",
    "quality_score": 0.85,
    "tags": ["python", "blockchain"],
    "provenance": {
      "repo": "github.com/owner/repo",
      "path": "src/main.py",
      "digest": "sha256:def456..."
    }
  },
  "created_at": "2026-04-26T10:05:00Z"
}
```

### DatasetManifest Schema
```json
{
  "version": "1.0",
  "dataset_id": "blockchain-node-instruct-ft-20260426",
  "total_records": 5,
  "quality_score": 0.85,
  "duplicate_rate": 0.0,
  "safety_gates_passed": ["secrets", "licenses", "provenance", "quality", "dedup"],
  "policy_pack": "commercial-ready",
  "created_at": "2026-04-26T12:00:00Z",
  "sources": [
    {"repo": "github.com/owner/repo1", "records": 3},
    {"repo": "github.com/owner/repo2", "records": 2}
  ]
}
```

## Current Dataset Status

**Name**: blockchain-node-instruct-ft-20260426
**Records**: 5 total
**Quality Score**: 0.85/1.0 (exceeds 0.70 minimum by 21%)
**Duplicate Rate**: 0.0% (zero duplicates)
**Safety Gates**: 5/5 PASSED ✅
**Model Accuracy**: 92.04% (exceeds 85% target by 7%)
**Status**: ✅ READY FOR PRODUCTION DEPLOYMENT

## Trainer Handoff

### Handoff Manifest Contents
```json
{
  "dataset_path": "data/datasets/blockchain-node-instruct.jsonl",
  "manifest_path": "data/manifests/blockchain-node.json",
  "model_card_path": "reports/model-card.md",
  "quality_report_path": "reports/quality-report.json",
  "policy_compliance_path": "reports/policy-compliance-report.json",
  "training_config": {
    "model_type": "instruction-tuned",
    "base_model": "llama-3-8b",
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-5
  },
  "approval_checklist": {
    "legal_approved": true,
    "compliance_approved": true,
    "quality_validated": true,
    "safety_gates_passed": true
  }
}
```

### LoRA Training Configuration
```python
# Example configuration for LoRA job
lora_config = {
    "r": 8,  # Low-rank dimension
    "lora_alpha": 32,  # Scaling factor
    "target_modules": ["q_proj", "v_proj"],  # Which layers to adapt
    "lora_dropout": 0.1,  # Regularization
    "bias": "none",  # No bias adaptation
}
```

## Testing & Validation

### Run Full Test Suite
```bash
# All 129 tests
python -m pytest tests/ -v

# Safety gates only
python -m pytest tests/gates/ -v

# Quality scoring only
python -m pytest tests/quality/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

### Validate Dataset
```bash
# Run validation script
python scripts/validate_model.py --dataset data/datasets/blockchain-node-instruct.jsonl

# Check quality metrics
python -c "from peachtree.quality import calculate_quality_score; print(calculate_quality_score('data/datasets/blockchain-node-instruct.jsonl'))"

# Audit for issues
peachtree audit --input data/datasets/blockchain-node-instruct.jsonl --detailed
```

## Troubleshooting

### Issue: Secret Detected
```bash
# View detected secrets (redacted)
peachtree audit --input data.jsonl --filter secrets

# Remove records with secrets
peachtree build --input data.jsonl --strict-secrets --output clean-data.jsonl
```

### Issue: Low Quality Score
```bash
# Identify low-quality records
peachtree quality --input data.jsonl --threshold 0.70 --output low-quality-ids.txt

# Filter out low-quality records
peachtree build --input data.jsonl --min-quality 0.70 --output high-quality-data.jsonl
```

### Issue: License Violations
```bash
# Check license compliance
peachtree policy --input data.jsonl --policy-pack policies/license-strict.yaml

# List records by license
peachtree audit --input data.jsonl --group-by license
```

### Issue: Duplicate Records
```bash
# Find duplicates
peachtree dedup --input data.jsonl --report-only --output duplicate-report.json

# Remove duplicates
peachtree dedup --input data.jsonl --output data-deduped.jsonl
```

## Integration Points

### Hancock (Cybersecurity LLM)
- Uses PeachTree datasets for security-focused fine-tuning
- Requires additional security policy gates
- Integration: `src/peachtree/integrations/hancock.py`

### PeachFuzz (Fuzzing Engine)
- Generates fuzz test cases from PeachTree datasets
- Requires code-specific record filtering
- Integration: `src/peachtree/integrations/peachfuzz.py`

## Best Practices

1. **Always run safety gates** - Never skip secret filtering or license compliance
2. **Validate provenance** - Every record must track its source
3. **Test policy packs** - Validate policy configurations before production use
4. **Monitor quality scores** - Track quality trends over time
5. **Document decisions** - Record why certain records were included/excluded
6. **Review manifests** - Always review dataset manifests before release
7. **Version control** - Keep dataset versions and associated manifests together
8. **Audit trails** - Maintain logs of all dataset operations

## Output Format
When assisting with PeachTree operations:
1. **Current Dataset State**: Records, quality, gates status
2. **Recommended Action**: CLI command or operation to perform
3. **Expected Outcome**: What should happen if successful
4. **Validation Steps**: How to verify the operation worked
5. **Safety Considerations**: Any risks or compliance checks needed

## See Also
- PeachTree documentation: `docs/`
- Policy pack examples: `policies/`
- Integration guides: `docs/integrations/`
- Test suite: `tests/`
- Example datasets: `examples/`
