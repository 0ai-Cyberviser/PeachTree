# Quick Reference Card

One-page reference for PeachTree commands and workflows.

## Installation

```bash
# From PyPI
pip install peachtree-ai

# From source
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree && pip install -e .

# Verify
peachtree --version
```

## Core Commands

### Planning

```bash
# Plan dataset structure from goal
peachtree plan --source /repo/path --goal "Security training data"

# Show all available planning options
peachtree plan --help
```

### Ingestion

```bash
# Ingest local repository
peachtree ingest --repo /repo/path --output data/ingested/

# Ingest specific file types
peachtree ingest --repo /repo/path --pattern "*.py" --output data/

# Show ingestion options
peachtree ingest --help
```

### Building

```bash
# Build JSONL dataset
peachtree build --input data/ --output dataset.jsonl

# Build with specific policy pack
peachtree build --input data/ --output dataset.jsonl --policy safety

# Build with verbose output
peachtree build --input data/ --output dataset.jsonl --verbose
```

### Auditing

```bash
# Audit dataset quality
peachtree audit --dataset dataset.jsonl

# Detailed audit report
peachtree audit --dataset dataset.jsonl --verbose

# Export audit results
peachtree audit --dataset dataset.jsonl --output audit.json
```

### Policy Evaluation

```bash
# Check policy compliance
peachtree policy --dataset dataset.jsonl --pack safety

# List available policy packs
peachtree policy --list-packs

# Create custom policy pack
peachtree policy --dataset dataset.jsonl --config policy.yaml
```

### Deduplication

```bash
# Deduplicate dataset (content-hash)
peachtree dedup --input dataset.jsonl --output dedup.jsonl

# Use semantic deduplication
peachtree dedup --input dataset.jsonl --output dedup.jsonl --method semantic

# Use fuzzy matching
peachtree dedup --input dataset.jsonl --output dedup.jsonl --method fuzzy
```

### Quality Scoring

```bash
# Score dataset quality
peachtree score --dataset dataset.jsonl

# Export scores
peachtree score --dataset dataset.jsonl --output scores.json

# Filter by score threshold
peachtree score --dataset dataset.jsonl --threshold 0.8 --output high-quality.jsonl
```

### Release & Export

```bash
# Create release bundle
peachtree release --dataset dataset.jsonl --output release/

# Generate SBOM (Software Bill of Materials)
peachtree sbom --dataset dataset.jsonl --output sbom.json

# Create model card
peachtree model-card --dataset dataset.jsonl --output model-card.md

# Generate trainer handoff manifest
peachtree trainer-handoff --dataset dataset.jsonl --output trainer-manifest.json
```

## Configuration Files

### .peachtree.yaml

```yaml
# Basic configuration
source:
  path: /path/to/repo
  type: git

dataset:
  name: my-dataset
  version: 0.1.0
  description: My training dataset

safety_gates:
  secret_filter: true
  license_gate: true
  content_filter: true

deduplication:
  method: content_hash  # or: fuzzy, semantic
  similarity_threshold: 0.95

quality:
  min_score: 0.7
  metrics:
    - completeness
    - coherence
    - diversity

policies:
  - name: safety
    rules:
      - type: license_compatible
        licenses: [MIT, Apache-2.0, GPL-3.0]
      - type: no_secrets
      - type: no_malware
```

## Workflows

### Quick Start Workflow

```bash
# 1. Initialize
mkdir my-dataset && cd my-dataset

# 2. Create config
cat > .peachtree.yaml << 'EOF'
source:
  path: /path/to/repo
  type: git
dataset:
  name: my-dataset
EOF

# 3. Ingest data
peachtree ingest --repo /path/to/repo --output data/

# 4. Build dataset
peachtree build --input data/ --output dataset.jsonl

# 5. Audit and validate
peachtree audit --dataset dataset.jsonl

# 6. Release
peachtree release --dataset dataset.jsonl --output release/
```

### Production Workflow

```bash
# 1. Plan structure
peachtree plan --source /repo --goal "Production training data"

# 2. Configure policies
cat > policies.yaml << 'EOF'
# Policy definitions
EOF

# 3. Ingest with filters
peachtree ingest --repo /repo --pattern "*.py|*.md" --output data/

# 4. Build with strict policies
peachtree build --input data/ \
  --output dataset.jsonl \
  --policy production \
  --verbose

# 5. Comprehensive audit
peachtree audit --dataset dataset.jsonl --output audit-report.json

# 6. Deduplicate
peachtree dedup --input dataset.jsonl --output dedup.jsonl --method semantic

# 7. Quality check
peachtree score --dataset dedup.jsonl --threshold 0.8 --output final.jsonl

# 8. Create release bundle
peachtree release --dataset final.jsonl --output release/

# 9. Generate documentation
peachtree model-card --dataset final.jsonl --output model-card.md
peachtree trainer-handoff --dataset final.jsonl --output manifest.json
```

### Incremental Update Workflow

```bash
# 1. Load existing dataset
existing_dataset="v1.0-dataset.jsonl"

# 2. Ingest new data
peachtree ingest --repo /repo --output new-data/

# 3. Build new records
peachtree build --input new-data/ --output new-records.jsonl

# 4. Merge datasets
cat $existing_dataset new-records.jsonl > combined.jsonl

# 5. Deduplicate merged dataset
peachtree dedup --input combined.jsonl --output v1.1-dataset.jsonl

# 6. Validate merged dataset
peachtree audit --dataset v1.1-dataset.jsonl
```

## JSONL Record Format

```json
{
  "id": "record-uuid",
  "source_repo": "https://github.com/project/repo",
  "source_path": "docs/architecture.md",
  "source_commit": "abc123def456...",
  "content": "Full text content here...",
  "metadata": {
    "type": "documentation",
    "language": "english",
    "timestamp": "2026-04-27T10:00:00Z"
  },
  "provenance": {
    "created_at": "2026-04-27T10:00:00Z",
    "pipeline_version": "0.9.0",
    "policies_applied": ["safety", "quality"]
  },
  "quality_score": 0.87,
  "safety_flags": []
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Policy violation |
| 5 | Safety check failed |

## Environment Variables

```bash
# Set logging level
export PEACHTREE_LOG_LEVEL=DEBUG

# Set default policy pack
export PEACHTREE_DEFAULT_POLICY=safety

# Set output format
export PEACHTREE_OUTPUT_FORMAT=json

# Disable color output
export PEACHTREE_NO_COLOR=1

# Set thread count
export PEACHTREE_THREADS=4
```

## Common Patterns

### Filter & Build

```bash
find /repo -name "*.py" -o -name "*.md" | peachtree build --input - --output dataset.jsonl
```

### Build & Deduplicate

```bash
peachtree build --input data/ --output raw.jsonl && \
peachtree dedup --input raw.jsonl --output dedup.jsonl
```

### Audit & Export

```bash
peachtree audit --dataset dataset.jsonl --output audit.json && \
cat audit.json | jq '.summary'
```

### Batch Processing

```bash
for repo in /repos/*; do
  peachtree ingest --repo "$repo" --output "data/$(basename $repo)/"
done
peachtree build --input data/ --output batch-dataset.jsonl
```

## Debugging

```bash
# Verbose output
peachtree build --input data/ --output dataset.jsonl --verbose

# Debug logging
peachtree build --input data/ --output dataset.jsonl --debug

# Dry run (no output)
peachtree build --input data/ --output /dev/null --dry-run

# Show configuration
peachtree config --show

# Validate configuration
peachtree config --validate .peachtree.yaml
```

## Help & Support

```bash
# General help
peachtree --help

# Command-specific help
peachtree build --help
peachtree policy --help

# Version info
peachtree --version

# System info
peachtree system-info

# Configuration info
peachtree config --info
```

## Links

- **Documentation:** https://0ai-cyberviser.github.io/PeachTree/
- **GitHub:** https://github.com/0ai-Cyberviser/PeachTree
- **Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues
- **Discussions:** https://github.com/0ai-Cyberviser/PeachTree/discussions

---

**Version:** 0.9.0 | **Updated:** 2026-04-27

Print this page for quick reference (2 pages)
