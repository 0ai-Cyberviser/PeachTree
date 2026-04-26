# FAQ - Frequently Asked Questions

## General Questions

### What is PeachTree?

PeachTree is a recursive learning-tree dataset engine that converts owned repositories, documentation, tests, and fuzz reports into traceable, safe, deduplicated JSONL datasets for machine learning and security workflows.

### Who should use PeachTree?

- Machine learning teams building training datasets
- Security researchers building security LLM datasets
- Fuzzing infrastructure teams managing regression corpora
- Organizations needing auditable dataset provenance

### Does PeachTree scrape public GitHub?

No. PeachTree is **local-first by default** and does **not** automatically scrape GitHub. Public collection requires explicit opt-in, policy configuration, and an allow-list.

## Workflow Questions

### How long does it take to build a dataset?

- Ingestion: ~1000 files/second
- Quality scoring: ~500 records/second  
- Deduplication: ~100 records/second (similarity-based)

For a typical 10,000-record dataset: 5-10 minutes.

### What formats can PeachTree output?

- JSONL (default)
- Parquet (columnar)
- CSV (tabular)
- HuggingFace datasets
- Pickle

### Can I use PeachTree for commercial models?

Yes, with the `commercial-ready` policy pack which enforces:
- Verified licenses (MIT, Apache-2.0, etc.)
- Quality score >= 0.85
- Security review requirement
- Full provenance tracking

## Safety Questions

### How does secret filtering work?

PeachTree uses regex patterns to detect:
- API keys (AWS, GCP, GitHub, etc.)
- SSH private keys
- Database passwords
- OAuth tokens
- Generic password patterns

### What happens if a secret is detected?

The record is **filtered out** by default. You can:
- Use `--filter-secrets` to enable filtering
- Review flagged records in audit reports
- Define custom secret patterns

### Are all licenses supported?

PeachTree supports major open-source licenses:
- MIT, Apache-2.0, BSD-3-Clause
- GPL-2.0, GPL-3.0, AGPL-3.0
- CC-BY-4.0

You can configure `allowed-licenses` per workflow.

## Technical Questions

### What Python version is required?

Python 3.10 or later.

### How large can datasets be?

No theoretical limit. Tested up to 10M+ records:
- Memory: Streaming processing keeps overhead low
- Disk: JSONL files scale linearly
- Performance: Optimization for large-scale ingestion

### How do I integrate with Hancock or PeachFuzz?

Use the `handoff` command:

```bash
peachtree handoff dataset.jsonl \
  --workflow hancock \
  --output trainer-handoff.json
```

This generates a manifest for downstream workflows.

### Can I version control datasets?

PeachTree generates deterministic record IDs (SHA-256), making datasets reproducible. Commit JSONL files + manifests to git:

```bash
git add dataset.jsonl manifest.json
git commit -m "Add security dataset v1.0"
```

## Policy & Compliance Questions

### What's a policy pack?

A composable set of safety and quality rules. Built-in packs:
- `commercial-ready` - Enterprise compliance
- `open-safe` - Public license compatible
- `internal-review` - Requires approval

### How do I audit compliance?

```bash
peachtree audit dataset.jsonl
peachtree policy-pack dataset.jsonl --pack commercial-ready
```

### What does the model card include?

- Dataset overview
- Data collection methodology
- Intended use cases
- Training recommendations
- Limitations and biases
- License and attribution

## Troubleshooting

### My dataset is too slow to process

- Use `dedup` with `content-hash` instead of `semantic`
- Stream process large files instead of loading all at once
- Run on a machine with more CPU cores

### Secrets are still being included

Ensure `--filter-secrets` is enabled:

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --filter-secrets
```

### License validation fails

Check allowed licenses:

```bash
peachtree audit dataset.jsonl  # Shows detected licenses
peachtree build sources.jsonl \
  --allowed-licenses <your-licenses>
```

### Tests are failing locally

Ensure dev dependencies are installed:

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## More Questions?

- **Documentation**: [Full Docs](../index.md)
- **Issues**: [GitHub Issues](https://github.com/0ai-Cyberviser/PeachTree/issues)
- **Discussions**: [GitHub Discussions](https://github.com/0ai-Cyberviser/PeachTree/discussions)
- **Security**: [SECURITY.md](../../SECURITY.md)
