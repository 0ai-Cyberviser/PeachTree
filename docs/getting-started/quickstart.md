# Quick Start

Get your first PeachTree dataset running in 5 minutes.

## 1. Install PeachTree

```bash
pip install peachtree-ai
```

## 2. Prepare Your Data

Create a test directory with some Python files:

```bash
mkdir -p test-repo/src
cat > test-repo/src/hello.py << 'EOF'
"""Hello world module."""

def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("PeachTree"))
EOF
```

## 3. Ingest Source Files

```bash
peachtree ingest-local test-repo/src \
  --output test-sources.jsonl \
  --name "MyProject" \
  --version "1.0.0"
```

This creates a JSONL file with source documents and full provenance.

## 4. Build Training Dataset

```bash
peachtree build test-sources.jsonl \
  --output test-dataset.jsonl \
  --filter-secrets
```

This applies safety gates and creates training-ready JSONL records.

## 5. Audit Dataset

```bash
peachtree audit test-dataset.jsonl
```

Output shows:
- Record count
- License compliance
- Quality scores
- Deduplication stats

## 6. Generate Model Card

```bash
peachtree model-card test-dataset.jsonl \
  --output model-card.md \
  --name "MyProject" \
  --version "1.0.0"
```

## 7. Create Release Bundle

```bash
peachtree bundle test-dataset.jsonl \
  --output release/ \
  --sign
```

This creates:
- `release/dataset.jsonl` - Training JSONL
- `release/manifest.json` - Dataset metadata
- `release/sbom.json` - Supply chain info
- `release/signatures.json` - Cryptographic signatures

## 8. Inspect Results

```bash
# View dataset statistics
head -5 test-dataset.jsonl | python -m json.tool

# Check manifest
cat release/manifest.json | python -m json.tool

# View model card
cat model-card.md
```

## Next Steps

- Learn about [Safety Gates](../user-guide/safety.md)
- Explore [Policy Packs](../user-guide/policy-packs.md)
- Read [CLI Reference](../user-guide/cli.md)
- Check [Architecture](../architecture/design.md)

## Common Tasks

### Filter by License

```bash
peachtree build sources.jsonl \
  --output dataset.jsonl \
  --allowed-licenses MIT,Apache-2.0
```

### Enable Quality Scoring

```bash
peachtree quality sources.jsonl \
  --output scored.jsonl \
  --model "default"
```

### Deduplicate Dataset

```bash
peachtree dedup scored.jsonl \
  --output dedup.jsonl \
  --similarity-threshold 0.95
```

### Check Readiness for Training

```bash
peachtree readiness dataset.jsonl \
  --policy-pack commercial-ready
```

## Tips

- Always run `audit` before using datasets for training
- Use `--filter-secrets` to ensure no sensitive data
- Generate model cards for transparency and governance
- Sign release bundles for provenance verification
- Check the [FAQ](../resources/faq.md) for common questions
