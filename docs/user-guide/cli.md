# CLI Commands Reference

PeachTree provides a comprehensive CLI with 28+ commands for dataset management, safety checking, and release workflows.

## Global Options

All commands support:

```bash
--help                # Show command help
--verbose            # Enable verbose logging
--quiet              # Suppress non-error output
--config FILE        # Use custom config file
```

## Planning & Collection

### `peachtree plan`

Create a learning objective and collection strategy.

```bash
peachtree plan \
  --repositories src/ docs/ \
  --objective "Build Python security dataset" \
  --output plan.json
```

**Options:**
- `--repositories PATHS`: Paths to analyze
- `--objective TEXT`: Learning goal description
- `--output FILE`: Save plan to JSON
- `--depth N`: Exploration depth (default: 3)

### `peachtree ingest-local`

Collect source documents from local repositories.

```bash
peachtree ingest-local src/ \
  --output sources.jsonl \
  --name "MyProject" \
  --version "1.0.0"
```

**Options:**
- `--output FILE`: JSONL output path
- `--name TEXT`: Dataset name
- `--version TEXT`: Version identifier
- `--file-types TYPES`: Limit file types (default: all)
- `--exclude PATTERNS`: Exclude paths

## Building & Processing

### `peachtree build`

Build training dataset from source documents.

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-secrets \
  --allowed-licenses MIT,Apache-2.0
```

**Options:**
- `--output FILE`: JSONL output path
- `--filter-secrets`: Remove hardcoded secrets
- `--allowed-licenses LICENSES`: License allowlist
- `--min-quality N`: Minimum quality score (0-1)
- `--policy-pack PACK`: Apply policy pack

### `peachtree audit`

Comprehensive dataset validation.

```bash
peachtree audit dataset.jsonl \
  --output report.json \
  --markdown report.md
```

**Output includes:**
- Record count and statistics
- License compliance report
- Quality score distribution
- Duplicate detection
- Security findings

### `peachtree quality`

Score records by quality metrics.

```bash
peachtree quality dataset.jsonl \
  --output scored.jsonl \
  --model "default" \
  --min-score 0.7
```

**Options:**
- `--model MODEL`: Quality model (default, strict)
- `--min-score N`: Filter by minimum score
- `--include-scores`: Add scores to output

### `peachtree dedup`

Remove duplicates and similar records.

```bash
peachtree dedup dataset.jsonl \
  --output dedup.jsonl \
  --similarity-threshold 0.95 \
  --method "content-hash"
```

**Methods:**
- `content-hash`: Exact SHA-256 matching
- `semantic`: Similarity-based (slower)
- `fuzzy`: Fuzzy string matching

## Analysis & Review

### `peachtree graph`

Visualize source repository dependency graph.

```bash
peachtree graph \
  --repositories src/ \
  --output graph.json \
  --format mermaid
```

### `peachtree lineage`

Trace dataset record provenance.

```bash
peachtree lineage dataset.jsonl \
  --record-id <sha256-hash> \
  --format tree
```

**Output shows:**
- Source repository and path
- Collection timestamp
- Processing steps applied
- Policy decisions

### `peachtree diff`

Compare dataset versions.

```bash
peachtree diff current.jsonl \
  --previous previous.jsonl \
  --output diff-report.md \
  --include-details
```

### `peachtree export`

Export dataset in alternative formats.

```bash
peachtree export dataset.jsonl \
  --format parquet \
  --output dataset.parquet
```

**Formats:**
- `jsonl` (default)
- `parquet` (columnar)
- `csv` (tabular)
- `huggingface` (HF dataset)

## Validation & Compliance

### `peachtree readiness`

Check dataset training readiness.

```bash
peachtree readiness dataset.jsonl \
  --policy-pack commercial-ready \
  --output readiness.json
```

**Policy Packs:**
- `commercial-ready`: Enterprise compliance
- `open-safe`: Public license compatible
- `internal-review`: Requires approval
- `custom-pack`: User-defined

### `peachtree policy-pack`

Evaluate against policy pack.

```bash
peachtree policy-pack dataset.jsonl \
  --pack commercial-ready \
  --output policy-report.json
```

### `peachtree license-gate`

Check license compatibility.

```bash
peachtree license-gate dataset.jsonl \
  --allowed-licenses MIT,Apache-2.0,BSD-3-Clause \
  --output license-report.json
```

## Metadata & Documentation

### `peachtree model-card`

Generate model card for dataset.

```bash
peachtree model-card dataset.jsonl \
  --name "MyProject" \
  --version "1.0.0" \
  --description "Security-focused training dataset" \
  --output model-card.md
```

**Generated sections:**
- Dataset overview
- Data collection methodology
- Intended use
- Training recommendations
- Limitations and biases
- License and attribution

### `peachtree registry`

Build artifact registry/index.

```bash
peachtree registry \
  data/datasets/ \
  reports/ \
  --name "MyProject" \
  --version "1.0.0" \
  --output registry.json
```

## Release & Distribution

### `peachtree sign`

Add cryptographic signatures.

```bash
peachtree sign dataset.jsonl \
  --key-id production \
  --output dataset-signed.jsonl
```

### `peachtree sbom`

Generate SBOM (Software Bill of Materials).

```bash
peachtree sbom \
  --registry registry.json \
  --name "MyProject" \
  --output sbom.json \
  --markdown sbom.md
```

**Includes:**
- Dataset artifacts with hashes
- Source repository lineage
- Builder version and timestamp
- License metadata

### `peachtree bundle`

Create release bundle.

```bash
peachtree bundle dataset.jsonl \
  --output release/ \
  --sign \
  --include-sbom \
  --model-card model-card.md
```

**Package includes:**
- `dataset.jsonl` - Training data
- `manifest.json` - Metadata
- `sbom.json` - Supply chain
- `signatures.json` - Verification
- `model-card.md` - Documentation

## Training Workflows

### `peachtree handoff`

Prepare trainer handoff manifest.

```bash
peachtree handoff dataset.jsonl \
  --workflow hancock \
  --output trainer-handoff.json \
  --training-config training.yaml
```

### `peachtree train-plan`

Generate training plan and job specs.

```bash
peachtree train-plan dataset.jsonl \
  --framework huggingface \
  --output train-plan.json \
  --model-size large
```

### `peachtree lora-card`

Generate LoRA fine-tuning card.

```bash
peachtree lora-card dataset.jsonl \
  --base-model model-id \
  --output lora-card.json
```

## GitHub Integration

### `peachtree github-owned`

Collect from GitHub-owned repositories.

```bash
peachtree github-owned \
  --org "0ai-Cyberviser" \
  --output github-sources.jsonl \
  --allow-list repos.txt
```

**Requires:**
- GitHub token (via `GITHUB_TOKEN` env var)
- Allow-list file with repository names
- License policy configuration

## Examples

### Complete Workflow

```bash
# 1. Plan
peachtree plan --repositories src/ --objective "API security dataset"

# 2. Ingest
peachtree ingest-local src/ --output sources.jsonl

# 3. Build
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-secrets

# 4. Validate
peachtree audit dataset.jsonl
peachtree quality dataset.jsonl --min-score 0.8

# 5. Prepare Release
peachtree model-card dataset.jsonl --output model-card.md
peachtree sbom --registry reports/registry.json --output sbom.json

# 6. Create Bundle
peachtree bundle dataset.jsonl --output release/ --sign

# 7. Hand Off
peachtree handoff dataset.jsonl --workflow hancock
```

### Policy-Driven Build

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --policy-pack commercial-ready \
  --allowed-licenses MIT,Apache-2.0
```

### Deduplication

```bash
# Remove exact duplicates
peachtree dedup dataset.jsonl \
  --method content-hash \
  --output exact-dedup.jsonl

# Remove semantic duplicates
peachtree dedup exact-dedup.jsonl \
  --method semantic \
  --similarity-threshold 0.95 \
  --output final.jsonl
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: File not found
- `4`: Policy violation
- `5`: Security issue detected

## Getting Help

```bash
# Show all commands
peachtree --help

# Command-specific help
peachtree build --help

# Version information
peachtree --version
```

## See Also

- [User Guide](../user-guide/building.md)
- [Safety Gates](../user-guide/safety.md)
- [Policy Packs](../user-guide/policy-packs.md)
- [Architecture](../architecture/design.md)
