# PeachTree - Recursive Learning-Tree Dataset Engine

**PeachTree** is a production-ready dataset control plane that transforms owned repositories, documentation, tests, fuzz reports, and telemetry into traceable, safe, deduplicated JSONL datasets for machine learning and security workflows.

## Key Features

- **Traceable**: Every dataset record includes source repository, path, and cryptographic digest
- **Safe**: Built-in secret filtering, license gates, and content safety checks
- **Deduplicated**: Deterministic deduplication reduces training data redundancy
- **Reviewable**: Automatic generation of manifests, diffs, and model cards before publication
- **Local-First**: No broad public scraping; owned repositories ingested by default

## Data Flow

```
Owned Repositories
       ↓
Recursive Learning Tree (Planning)
       ↓
Source Document Collection
       ↓
Safety Gate (Secrets, Licenses, Content)
       ↓
Dataset Builder
       ↓
┌─────────────────────────────────────┐
│ JSONL Training Dataset (Traceable)  │
│ Manifest + Provenance               │
│ Policy Compliance Reports           │
│ Model Cards                         │
│ Release Bundles + SBOM              │
└─────────────────────────────────────┘
```

## Quick Start

```bash
# Install PeachTree
pip install peachtree-ai

# Plan a dataset from owned repositories
peachtree plan --repositories src/ --objective "build training dataset"

# Ingest local source files
peachtree ingest-local src/ \
  --output data/sources.jsonl \
  --name "MyProject"

# Build JSONL dataset with safety gates
peachtree build data/sources.jsonl \
  --output data/training.jsonl \
  --filter-secrets \
  --allowed-licenses MIT,Apache-2.0

# Audit and validate
peachtree audit data/training.jsonl

# Score quality and detect duplicates
peachtree quality data/training.jsonl
peachtree dedup data/training.jsonl

# Generate release bundle
peachtree bundle data/training.jsonl \
  --output release/ \
  --sign
```

## Core Concepts

### RecursiveLearningTree
Hierarchical planning model that explores learning objectives through branching strategies to identify optimal data collection approaches.

### SafetyGate
Multi-layer filtering system that removes:
- Hardcoded secrets and API keys
- Unknown or incompatible licenses
- Unsafe content patterns
- Duplicate or low-quality records

### DatasetBuilder
Converts source documents into deterministic JSONL records with full provenance metadata:
```json
{
  "id": "sha256-digest",
  "text": "content",
  "source_repo": "owner/repo",
  "source_path": "path/to/file.py",
  "source_digest": "commit-hash",
  "license": "MIT",
  "quality_score": 0.92,
  "metadata": {}
}
```

### Policy Packs
Composable safety and quality gates:
- **License gates**: Ensure training data compatibility
- **Quality gates**: Filter by content metrics
- **Duplicate gates**: Prevent redundant training samples
- **Review gates**: Require human approval

## Ecosystem Integration

- **[Hancock](https://github.com/0ai-Cyberviser/Hancock)**: Cybersecurity LLM agent training
- **[PeachFuzz](https://github.com/0ai-Cyberviser/peachfuzz)**: Fuzzing corpus and regression testing
- **[CyberViser AI](https://cyberviserai.com/)**: Public documentation hub
- **[0AI Ecosystem](https://0ai-cyberviser.github.io/0ai/)**: Broader coordination platform

## Documentation

- [Installation & Setup](getting-started/installation.md)
- [CLI Reference](user-guide/cli.md)
- [Architecture & Design](architecture/design.md)
- [API Reference](api/builder.md)
- [Contributing Guide](contributing/development.md)

## Project Status

- **Version**: 0.9.0
- **Python**: 3.10+
- **Test Coverage**: 91%
- **Status**: Production Ready ✅

## License

PeachTree is licensed under the MIT License. See [LICENSE](https://github.com/0ai-Cyberviser/PeachTree/blob/main/LICENSE) for details.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Development setup
- Testing standards
- Code quality requirements
- Commit and PR workflows

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/0ai-Cyberviser/PeachTree/issues)
- **Discussions**: [Join community discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for vulnerability reporting

---

**Built with ❤️ by the CyberViser / 0AI team**
