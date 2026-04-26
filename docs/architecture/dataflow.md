# Data Flow

## From Source to Training

```
Owned Repositories
        ↓
Ingest Local (repo_ingest.py)
  ├─ Discover files
  ├─ Extract content
  └─ Create SourceDocuments
        ↓
Recursive Learning Tree (planner.py)
  ├─ Plan collection strategy
  ├─ Explore learning branches
  └─ Analyze coverage
        ↓
Safety Gate (safety.py, license_gate.py)
  ├─ Filter secrets
  ├─ Check licenses
  ├─ Content validation
  └─ Pattern detection
        ↓
Dataset Builder (builder.py)
  ├─ Create DatasetRecords
  ├─ Calculate quality scores
  ├─ Add provenance metadata
  └─ Generate deterministic IDs
        ↓
Quality Processing (quality.py)
  ├─ Score by metrics
  ├─ Filter low-quality
  └─ Calculate statistics
        ↓
Deduplication (dedup.py)
  ├─ Detect duplicates
  ├─ Remove similar records
  └─ Optimize dataset size
        ↓
Policy Validation (policy_packs.py)
  ├─ Evaluate policies
  ├─ Check compliance
  └─ Generate reports
        ↓
Release Preparation
  ├─ Registry (registry.py)
  ├─ SBOM (sbom.py)
  ├─ Model Card (model_card.py)
  ├─ Signing (signing.py)
  └─ Bundle (release_bundle.py)
        ↓
Training Handoff
  ├─ Trainer Manifest (trainer_handoff.py)
  ├─ Training Plan (training_plan.py)
  ├─ LoRA Card (lora_job.py)
  └─ Verification
        ↓
Downstream Workflows
  ├─ Hancock LLM Training
  ├─ PeachFuzz Infrastructure
  └─ CyberViser AI Hub
```

## Key Transformation Points

### Ingestion → SourceDocument
- File discovery and enumeration
- Content extraction
- Metadata collection

### SourceDocument → DatasetRecord
- Deterministic ID generation (SHA-256)
- Provenance attachment
- Quality scoring

### DatasetRecord → Released Bundle
- SBOM generation
- Cryptographic signing
- Package creation

## See Also

- [Architecture](design.md)
- [Component Details](components.md)
