# PeachTree CLI Reference

Complete command-line reference for PeachTree dataset control plane.

## Installation

```bash
pip install peachtree-ai
# OR
pip install -e ".[dev]"  # from source
```

## Global Options

All commands support these global flags:

```bash
--help, -h          Show help message
--verbose, -v       Enable verbose output
--quiet, -q         Suppress non-error output
--version           Show PeachTree version
```

---

## Core Commands

### `peachtree plan`

Generate a recursive learning tree for dataset structure.

**Usage:**
```bash
peachtree plan \
  --source /path/to/repo \
  --goal "Build security training dataset" \
  [--output plan.json] \
  [--depth 3]
```

**Options:**
- `--source` - Source repository or documentation
- `--goal` - Dataset objective description
- `--output` - Output file for plan (default: stdout)
- `--depth` - Maximum tree depth (default: 3)

**Example:**
```bash
peachtree plan \
  --source ~/projects/security-tools \
  --goal "Create CVE analysis training data" \
  --output data/plans/security-plan.json
```

---

### `peachtree ingest-local`

Ingest local repository into JSONL source documents.

**Usage:**
```bash
peachtree ingest-local \
  --repo /path/to/repository \
  --repo-name "repo-name" \
  --license MIT \
  --output data/raw/repo.jsonl \
  [--include "*.md,*.py"] \
  [--exclude "tests/,build/"]
```

**Options:**
- `--repo` - Path to local repository
- `--repo-name` - Repository identifier
- `--license` - SPDX license identifier
- `--output` - Output JSONL file
- `--include` - File patterns to include (comma-separated)
- `--exclude` - Paths to exclude (comma-separated)

**Example:**
```bash
peachtree ingest-local \
  --repo /tmp/datasets/metasploit-framework \
  --repo-name "metasploit-framework" \
  --license BSD-3-Clause \
  --output data/raw/metasploit.jsonl \
  --include "*.rb,*.md" \
  --exclude "test/,spec/"
```

---

### `peachtree build`

Build training dataset from source documents.

**Usage:**
```bash
peachtree build \
  --source data/raw/source1.jsonl \
  [--source data/raw/source2.jsonl] \
  --dataset data/datasets/output.jsonl \
  --manifest data/manifests/manifest.json \
  --domain security \
  [--allow-unknown-license]
```

**Options:**
- `--source` - Input JSONL file(s), can specify multiple
- `--dataset` - Output dataset path
- `--manifest` - Output manifest path
- `--domain` - Dataset domain (security, general, code, etc.)
- `--allow-unknown-license` - Allow unknown licenses (default: false)

**Example:**
```bash
peachtree build \
  --source data/raw/cve-records.jsonl \
  --source data/raw/metasploit.jsonl \
  --dataset data/datasets/security-training.jsonl \
  --manifest data/manifests/security-manifest.json \
  --domain security
```

---

### `peachtree audit`

Audit dataset for quality and compliance.

**Usage:**
```bash
peachtree audit \
  --dataset data/datasets/training.jsonl \
  [--output reports/audit.json]
```

**Output:**
```json
{
  "dataset": "data/datasets/training.jsonl",
  "records": 7202,
  "unique_ids": 7202,
  "duplicates": 0,
  "has_provenance": true,
  "min_quality_score": 0.85
}
```

**Example:**
```bash
peachtree audit \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --output reports/audit-report.json
```

---

### `peachtree export`

Export dataset to training formats.

**Usage:**
```bash
peachtree export \
  --source data/datasets/training.jsonl \
  --output data/exports/training.jsonl \
  --format chatml \
  [--system-prompt "You are..."]
```

**Formats:**
- `chatml` - ChatML conversation format
- `alpaca` - Alpaca instruction format
- `sharegpt` - ShareGPT conversation format

**Example:**
```bash
peachtree export \
  --source data/datasets/security-training.jsonl \
  --output data/exports/hancock-chatml.jsonl \
  --format chatml \
  --system-prompt "You are Hancock, a cybersecurity AI assistant."
```

---

## Advanced Commands

### `peachtree dedup`

Remove duplicate records from dataset.

**Usage:**
```bash
peachtree dedup \
  --dataset data/datasets/training.jsonl \
  --output data/datasets/training-deduped.jsonl \
  [--method content-hash] \
  [--threshold 0.95]
```

**Methods:**
- `content-hash` - SHA256 content hashing (exact duplicates)
- `semantic` - Semantic similarity (near-duplicates)
- `fuzzy` - Fuzzy string matching

**Example:**
```bash
peachtree dedup \
  --dataset data/datasets/security-training.jsonl \
  --output data/datasets/security-deduped.jsonl \
  --method content-hash
```

---

### `peachtree score`

Calculate quality scores for dataset records.

**Usage:**
```bash
peachtree score \
  --dataset data/datasets/training.jsonl \
  --output reports/quality-scores.json \
  [--metrics completeness,relevance,clarity]
```

**Metrics:**
- `completeness` - Record has all required fields
- `relevance` - Content relevance to domain
- `clarity` - Text clarity and readability
- `provenance` - Source attribution quality

**Example:**
```bash
peachtree score \
  --dataset data/datasets/security-training.jsonl \
  --output reports/quality-scores.json \
  --metrics completeness,relevance,provenance
```

---

### `peachtree policy-pack`

Evaluate dataset against policy pack.

**Usage:**
```bash
peachtree policy-pack \
  --dataset data/datasets/training.jsonl \
  --policy config/policy-packs/security-domain.json \
  --output reports/policy-compliance.json
```

**Example:**
```bash
peachtree policy-pack \
  --dataset data/datasets/security-training.jsonl \
  --policy config/policy-packs/security-domain-compliance.json \
  --output reports/compliance-report.json
```

---

### `peachtree lineage`

View dataset lineage and provenance.

**Usage:**
```bash
peachtree lineage \
  --dataset data/datasets/training.jsonl \
  --manifest data/manifests/manifest.json \
  [--format markdown] \
  [--output reports/lineage.md]
```

**Formats:**
- `json` - Structured JSON output
- `markdown` - Human-readable markdown
- `mermaid` - Mermaid diagram

**Example:**
```bash
peachtree lineage \
  --dataset data/datasets/security-training.jsonl \
  --manifest data/manifests/security-manifest.json \
  --format markdown \
  --output reports/dataset-lineage.md
```

---

### `peachtree graph`

Generate dependency graphs.

**Usage:**
```bash
peachtree graph \
  --dataset-dir data/datasets \
  --manifest-dir data/manifests \
  --format mermaid \
  [--output graphs/dependencies.mmd]
```

**Formats:**
- `json` - Structured graph data
- `dot` - Graphviz DOT format
- `mermaid` - Mermaid diagram

**Example:**
```bash
peachtree graph \
  --dataset-dir data/datasets \
  --manifest-dir data/manifests \
  --format mermaid \
  --output docs/dependency-graph.mmd
```

---

## Release & Distribution

### `peachtree model-card`

Generate ML model card for dataset.

**Usage:**
```bash
peachtree model-card \
  --dataset data/datasets/training.jsonl \
  --manifest data/manifests/manifest.json \
  --output MODEL-CARD.md \
  [--template templates/model-card.md]
```

**Example:**
```bash
peachtree model-card \
  --dataset data/datasets/security-training.jsonl \
  --manifest data/manifests/security-manifest.json \
  --output MODEL-CARD-SECURITY.md
```

---

### `peachtree sbom`

Generate Software Bill of Materials.

**Usage:**
```bash
peachtree sbom \
  --dataset data/datasets/training.jsonl \
  --output reports/sbom.json \
  [--format spdx]
```

**Formats:**
- `spdx` - SPDX SBOM format
- `cyclonedx` - CycloneDX format

**Example:**
```bash
peachtree sbom \
  --dataset data/datasets/security-training.jsonl \
  --output reports/security-sbom.json \
  --format spdx
```

---

### `peachtree sign`

Cryptographically sign dataset.

**Usage:**
```bash
peachtree sign \
  --dataset data/datasets/training.jsonl \
  --key-file ~/.ssh/signing-key \
  --output reports/signatures.json
```

**Example:**
```bash
peachtree sign \
  --dataset data/datasets/security-training.jsonl \
  --key-file ~/.ssh/peachtree-signing-key \
  --output reports/dataset-signatures.json
```

---

### `peachtree bundle`

Create release bundle with all artifacts.

**Usage:**
```bash
peachtree bundle \
  --dataset data/datasets/training.jsonl \
  --manifest data/manifests/manifest.json \
  --output releases/dataset-v1.0.tar.gz \
  [--sign] \
  [--include-sbom]
```

**Example:**
```bash
peachtree bundle \
  --dataset data/datasets/security-training.jsonl \
  --manifest data/manifests/security-manifest.json \
  --output releases/security-dataset-v1.0.tar.gz \
  --sign \
  --include-sbom
```

---

### `peachtree handoff`

Generate trainer handoff manifest.

**Usage:**
```bash
peachtree handoff \
  --dataset data/datasets/training.jsonl \
  --manifest data/manifests/manifest.json \
  --output data/handoff/trainer-handoff.json \
  [--model-type LoRA]
```

**Example:**
```bash
peachtree handoff \
  --dataset data/datasets/security-training.jsonl \
  --manifest data/manifests/security-manifest.json \
  --output data/handoff/hancock-handoff.json \
  --model-type LoRA
```

---

## Utility Commands

### `peachtree policy`

Show default policies and safety gates.

**Usage:**
```bash
peachtree policy
```

**Output:**
```json
{
  "public_github_default": "disabled",
  "owned_local_repos_default": "enabled",
  "license_allowlist_required_for_public": true,
  "secret_filtering": true,
  "provenance_required": true
}
```

---

### `peachtree validate-export`

Validate exported training data.

**Usage:**
```bash
peachtree validate-export \
  --source data/exports/training.jsonl \
  --format chatml
```

**Example:**
```bash
peachtree validate-export \
  --source data/exports/hancock-chatml.jsonl \
  --format chatml
```

---

## Common Workflows

### Build Security Dataset from Scratch

```bash
# 1. Ingest repositories
peachtree ingest-local --repo /data/cve-database --repo-name cve --license MIT --output data/raw/cve.jsonl
peachtree ingest-local --repo /data/metasploit --repo-name msf --license BSD-3-Clause --output data/raw/msf.jsonl

# 2. Build dataset
peachtree build \
  --source data/raw/cve.jsonl \
  --source data/raw/msf.jsonl \
  --dataset data/datasets/security.jsonl \
  --manifest data/manifests/security.json \
  --domain security

# 3. Audit quality
peachtree audit --dataset data/datasets/security.jsonl

# 4. Check compliance
peachtree policy-pack \
  --dataset data/datasets/security.jsonl \
  --policy config/policy-packs/security-domain-compliance.json

# 5. Export for training
peachtree export \
  --source data/datasets/security.jsonl \
  --output data/exports/hancock.jsonl \
  --format chatml

# 6. Generate model card
peachtree model-card \
  --dataset data/datasets/security.jsonl \
  --manifest data/manifests/security.json \
  --output MODEL-CARD.md

# 7. Create release
peachtree bundle \
  --dataset data/datasets/security.jsonl \
  --manifest data/manifests/security.json \
  --output releases/security-v1.0.tar.gz \
  --sign
```

---

## Environment Variables

```bash
PEACHTREE_DATA_DIR=/path/to/data     # Default data directory
PEACHTREE_CONFIG=/path/to/config.yml # Configuration file
PEACHTREE_LOG_LEVEL=INFO             # Logging level
PEACHTREE_CACHE_DIR=/path/to/cache   # Cache directory
```

---

## Configuration File

```yaml
# ~/.peachtree/config.yml
data_dir: ~/peachtree-data
cache_dir: ~/.cache/peachtree
log_level: INFO

safety_gates:
  secret_filtering: true
  license_validation: true
  provenance_required: true

defaults:
  domain: general
  allow_unknown_license: false
  dedup_method: content-hash
```

---

**Complete CLI reference for all PeachTree operations!**
