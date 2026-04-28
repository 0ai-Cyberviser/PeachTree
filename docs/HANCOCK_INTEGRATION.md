# Hancock Cybersecurity Dataset Integration

## Overview

The Hancock integration module enables seamless ingestion of cybersecurity data from the [Hancock cybersecurity LLM pipeline](https://github.com/0ai-Cyberviser/Hancock) into PeachTree's dataset control plane. This integration provides provenance-tracked, safety-gated datasets suitable for training security-focused ML models.

## Supported Data Sources

Hancock collects data from multiple authoritative cybersecurity sources:

1. **MITRE ATT&CK** - Adversary tactics, techniques, and procedures (TTPs)
2. **NVD CVE** - Common Vulnerabilities and Exposures from NIST
3. **CISA KEV** - Known Exploited Vulnerabilities catalog
4. **GitHub Security Advisory (GHSA)** - Software vulnerability advisories
5. **Atomic Red Team** - Attack simulation and testing procedures
6. **Pentest KB** - Penetration testing knowledge base
7. **SOC KB** - Security operations center knowledge base

## Architecture

```
Hancock Pipeline (~/Hancock/data/)
    ├── raw_mitre.json (691 techniques)
    ├── raw_cve.json (600 CVEs)
    ├── raw_kev.json (1,583 KEV entries)
    ├── raw_ghsa.json (1,159 advisories)
    ├── raw_atomic.json (486 tests)
    ├── raw_pentest_kb.json (40 Q&A pairs)
    ├── raw_soc_kb.json (35 Q&A pairs)
    └── hancock_v3.jsonl (5,740 consolidated samples)
           ↓
PeachTree Hancock Integration
    ├── Source Discovery
    ├── Format Conversion → SourceDocument
    ├── Safety Gates (secrets, licenses)
    ├── Dataset Building → JSONL
    ├── Quality Scoring
    ├── Deduplication
    └── Trainer Handoff Generation
           ↓
Training-Ready Security Dataset
    ├── hancock_security_dataset_deduped.jsonl
    ├── hancock_manifest.json
    └── hancock_trainer_handoff.json
```

## Installation

The Hancock integration is included with PeachTree. Ensure you have:

```bash
# Install PeachTree with dependencies
pip install -e ".[dev]"

# Clone and run Hancock pipeline
git clone https://github.com/0ai-Cyberviser/Hancock.git ~/Hancock
cd ~/Hancock
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python hancock_pipeline.py --phase 3
```

## Quick Start

### 1. Discover Available Sources

```bash
peachtree hancock-discover --hancock-dir ~/Hancock/data
```

**Output:**
```json
{
  "hancock_data_dir": "/home/user/Hancock/data",
  "sources_found": 8,
  "sources": [
    {
      "name": "mitre",
      "type": "mitre",
      "file_path": "/home/user/Hancock/data/raw_mitre.json",
      "record_count": 691,
      "metadata": {"ingestion_date": "2026-04-27T..."}
    },
    // ... more sources
  ]
}
```

### 2. Ingest Hancock Data

```bash
peachtree hancock-ingest \
  --hancock-dir ~/Hancock/data \
  --output-dir data/hancock \
  --min-quality-score 0.70
```

**Output:**
```json
{
  "status": "success",
  "sources_ingested": 8,
  "total_documents": 5740,
  "total_records": 5740,
  "dataset_path": "data/hancock/hancock_security_dataset.jsonl",
  "manifest_path": "data/hancock/hancock_manifest.json",
  "handoff_path": "data/hancock/hancock_trainer_handoff.json"
}
```

### 3. Run Complete Workflow

```bash
peachtree hancock-workflow \
  --hancock-dir ~/Hancock/data \
  --output-dir data/hancock \
  --min-quality-score 0.70 \
  --format markdown
```

**Output:**
```markdown
# Hancock Ingestion Workflow Complete

## Summary
- **Sources Ingested**: 8
- **Total Documents**: 5740
- **Total Records**: 5740
- **Quality Score**: 0.82
- **Ready for Training**: ✅ Yes

## Deduplication Statistics
- **Duplicates Removed**: 45
- **Records Kept**: 5695

## Output Files
- **Dataset**: `data/hancock/hancock_security_dataset_deduped.jsonl`
- **Manifest**: `data/hancock/hancock_manifest.json`
- **Trainer Handoff**: `data/hancock/hancock_trainer_handoff.json`
```

## Python API Usage

### Basic Ingestion

```python
from peachtree.hancock_integration import HancockDataIngester, HancockIngestionConfig
from pathlib import Path

# Configure ingestion
config = HancockIngestionConfig(
    hancock_data_dir=Path("~/Hancock/data").expanduser(),
    output_dir=Path("data/hancock"),
    min_quality_score=0.70,
    commercial_quality_score=0.80,
    include_sources=["mitre", "cve", "kev", "ghsa", "atomic"],
    filter_secrets=True,
    require_provenance=True
)

# Create ingester
ingester = HancockDataIngester(config)

# Discover sources
sources = ingester.discover_sources()
print(f"Found {len(sources)} data sources")

# Ingest all
documents, manifest = ingester.ingest_all()
print(f"Ingested {len(documents)} documents")

# Generate trainer handoff
handoff = ingester.generate_training_handoff(manifest)
print(f"Generated handoff with {handoff['total_records']} records")
```

### Complete Workflow

```python
from peachtree.hancock_integration import hancock_ingestion_workflow
from pathlib import Path

summary = hancock_ingestion_workflow(
    hancock_data_dir=Path("~/Hancock/data"),
    output_dir=Path("data/hancock"),
    min_quality_score=0.70,
    generate_handoff=True
)

if summary['ready_for_training']:
    print(f"✅ Dataset ready! Quality score: {summary['quality_score']:.2f}")
    print(f"📁 Dataset: {summary['dataset_path']}")
    print(f"📋 Handoff: {summary['handoff_path']}")
else:
    print(f"❌ Dataset quality below threshold")
```

### Selective Source Ingestion

```python
# Ingest only specific sources
config = HancockIngestionConfig(
    hancock_data_dir=Path("~/Hancock/data"),
    output_dir=Path("data/hancock_mitre"),
    include_sources=["mitre", "atomic"]  # Only MITRE ATT&CK and Atomic Red Team
)

ingester = HancockDataIngester(config)
documents, manifest = ingester.ingest_all()
```

## Configuration Options

### HancockIngestionConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hancock_data_dir` | `Path` | `~/Hancock/data` | Hancock data directory |
| `output_dir` | `Path` | `data/hancock` | Output directory for datasets |
| `min_quality_score` | `float` | `0.70` | Minimum quality threshold (open-safe) |
| `commercial_quality_score` | `float` | `0.80` | Commercial use quality threshold |
| `include_sources` | `list[str]` | All | Source types to include |
| `filter_secrets` | `bool` | `True` | Enable secret filtering |
| `require_provenance` | `bool` | `True` | Require provenance tracking |
| `allow_unknown_license` | `bool` | `False` | Allow unknown licenses |

### Source Types

Valid values for `include_sources`:
- `"mitre"` - MITRE ATT&CK techniques
- `"cve"` - NVD CVE records
- `"kev"` - CISA Known Exploited Vulnerabilities
- `"ghsa"` - GitHub Security Advisories
- `"atomic"` - Atomic Red Team tests
- `"kb"` - Penetration testing knowledge base
- `"soc-kb"` - SOC knowledge base

## Output Format

### Dataset Record Example

```json
{
  "content": "Technique: Phishing\nID: T1566\nTactic: initial-access\nDescription: Adversaries may send phishing messages...\nPlatforms: Windows, Linux\nDetection: Monitor for suspicious emails",
  "source_repo": "Hancock/mitre",
  "source_path": "mitre/mitre/0/T1566",
  "license_id": "MIT",
  "sha256_digest": "abc123def456...",
  "metadata": {
    "hancock_source": "mitre",
    "ingestion_date": "2026-04-27T12:00:00",
    "record_id": "",
    "source_type": "mitre",
    "technique_id": "T1566",
    "tactic": "initial-access",
    "platforms": "Windows,Linux"
  }
}
```

### Trainer Handoff Manifest

```json
{
  "model_type": "cybersecurity-llm",
  "base_model": "meta-llama/Llama-3.2-3B",
  "task_description": "Cybersecurity question answering and threat analysis",
  "dataset_path": "data/hancock/hancock_security_dataset_deduped.jsonl",
  "total_records": 5695,
  "recommended_epochs": 3,
  "notes": [
    "Dataset combines MITRE ATT&CK, CVE, CISA KEV, GHSA, and Atomic Red Team data",
    "Suitable for security operations and penetration testing use cases",
    "Contains real-world vulnerability and exploit documentation",
    "Recommend additional filtering for production deployment"
  ]
}
```

## Provenance Tracking

All Hancock-sourced records include complete provenance:

- **Source Repository**: `Hancock/{source_name}`
- **Source Path**: `{source_type}/{index}/{id}`
- **SHA256 Digest**: Content fingerprint
- **License**: MIT (Hancock project license)
- **Metadata**: Source-specific fields (CVE IDs, technique IDs, etc.)

Example provenance chain:
```
Hancock Pipeline → Raw JSON → PeachTree SourceDocument → Safety Gates → Dataset Record
```

## Safety Gates

The Hancock integration applies PeachTree's standard safety gates:

1. **Secret Filtering** - Removes API keys, tokens, passwords
2. **License Validation** - Verifies MIT license compatibility
3. **Provenance Verification** - Ensures complete source tracking
4. **Quality Scoring** - Evaluates record completeness and relevance

## Quality Thresholds

| Threshold | Score | Use Case |
|-----------|-------|----------|
| Minimum | 0.70 | Open-source, research |
| Commercial | 0.80 | Production systems |
| High-Quality | 0.90+ | Critical infrastructure |

## Integration with PeachTree Workflows

### Combined Dataset Building

```bash
# Ingest owned repos
peachtree ingest-local --repo ~/my-security-tools --output data/raw/my-tools.jsonl

# Ingest Hancock data
peachtree hancock-ingest --output-dir data/hancock

# Merge datasets
peachtree merge \
  --inputs data/raw/my-tools.jsonl,data/hancock/hancock_security_dataset_deduped.jsonl \
  --output data/datasets/combined-security.jsonl

# Score combined dataset
peachtree score --dataset data/datasets/combined-security.jsonl
```

### Incremental Updates

```bash
# Initial ingestion
peachtree hancock-workflow --output-dir data/hancock/v1

# Update Hancock data
cd ~/Hancock && python hancock_pipeline.py --phase 3

# Re-ingest with change tracking
peachtree hancock-workflow --output-dir data/hancock/v2

# Compare versions
peachtree diff \
  --baseline data/hancock/v1/hancock_security_dataset_deduped.jsonl \
  --candidate data/hancock/v2/hancock_security_dataset_deduped.jsonl
```

## Troubleshooting

### Missing Hancock Data

**Error**: `No Hancock data sources found`

**Solution**:
```bash
# Verify Hancock data directory
ls ~/Hancock/data/

# Run Hancock pipeline if empty
cd ~/Hancock
python hancock_pipeline.py --phase 3
```

### Quality Score Too Low

**Warning**: `Dataset quality below threshold (0.65 < 0.70)`

**Solutions**:
1. Lower threshold: `--min-quality-score 0.60`
2. Filter sources: `--include-sources mitre,cve,kev` (exclude lower-quality sources)
3. Enable commercial mode: `--min-quality-score 0.80` (higher bar, fewer records)

### Duplicate Records

**Issue**: High duplication rate

**Solution**:
```bash
# Run workflow with deduplication
peachtree hancock-workflow --output-dir data/hancock

# Manual deduplication
peachtree dedup \
  --source data/hancock/hancock_security_dataset.jsonl \
  --output data/hancock/hancock_security_dataset_deduped.jsonl
```

## Best Practices

### 1. Regular Updates

```bash
# Weekly cron job
0 0 * * 0 cd ~/Hancock && python hancock_pipeline.py --phase 3 && \
  peachtree hancock-workflow --output-dir data/hancock/$(date +%Y%m%d)
```

### 2. Selective Ingestion

```python
# High-priority sources only
config = HancockIngestionConfig(
    include_sources=["mitre", "kev"],  # Critical sources
    min_quality_score=0.80,
    commercial_quality_score=0.90
)
```

### 3. Provenance Validation

```bash
# Verify all records have provenance
peachtree audit --dataset data/hancock/hancock_security_dataset_deduped.jsonl
```

### 4. License Compliance

```bash
# Verify MIT license compatibility
peachtree policy --input data/hancock/hancock_security_dataset_deduped.jsonl
```

## Performance

| Operation | Dataset Size | Time | Memory |
|-----------|--------------|------|--------|
| Discovery | 8 sources | <1s | <10 MB |
| Ingestion | 5,740 records | 5-10s | 50-100 MB |
| Quality Scoring | 5,740 records | 10-15s | 100 MB |
| Deduplication | 5,740 records | 5-10s | 100 MB |
| **Total Workflow** | **5,740 records** | **~30s** | **~200 MB** |

## Advanced Usage

### Custom Content Extraction

```python
from peachtree.hancock_integration import HancockDataIngester

class CustomHancockIngester(HancockDataIngester):
    def _extract_content(self, record, source_type):
        if source_type == "mitre":
            # Custom MITRE content format
            return f"ATT&CK: {record.get('name')}\n{record.get('description')}"
        return super()._extract_content(record, source_type)

ingester = CustomHancockIngester(config)
```

### Filtered Metadata

```python
# Extract only specific metadata fields
def extract_mitre_metadata(record):
    return {
        "technique_id": record.get("external_references", [{}])[0].get("external_id"),
        "platforms": ",".join(record.get("x_mitre_platforms", [])),
    }
```

## Related Documentation

- [PeachTree Dataset Operations Skill](../.github/skills/peachtree-dataset-operations/SKILL.md)
- [Security Dataset Integration Skill](../.github/skills/security-dataset-integration/SKILL.md)
- [Hancock Project](https://github.com/0ai-Cyberviser/Hancock)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [CISA KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

## Support

For issues or questions:
- GitHub Issues: https://github.com/0ai-Cyberviser/peachtree/issues
- Hancock Issues: https://github.com/0ai-Cyberviser/Hancock/issues
- Email: hackinsacks@proton.me
