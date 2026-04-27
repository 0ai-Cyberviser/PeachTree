# PeachTree Troubleshooting Guide

Common issues and solutions for PeachTree dataset operations.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Ingestion Errors](#ingestion-errors)
3. [Build Failures](#build-failures)
4. [Safety Gate Failures](#safety-gate-failures)
5. [Quality Issues](#quality-issues)
6. [Export Problems](#export-problems)
7. [Performance Issues](#performance-issues)
8. [License Compliance](#license-compliance)

---

## Installation Issues

### Error: "ModuleNotFoundError: No module named 'peachtree'"

**Cause:** PeachTree not installed or not in Python path

**Solution:**
```bash
# Install from PyPI
pip install peachtree-ai

# OR install from source
cd /tmp/peachtree
pip install -e .
```

**Verification:**
```bash
python -c "import peachtree; print(peachtree.__version__)"
```

---

### Error: "ImportError: cannot import name 'DatasetBuilder'"

**Cause:** Outdated PeachTree version or partial installation

**Solution:**
```bash
pip uninstall peachtree-ai
pip install --no-cache-dir peachtree-ai
```

---

## Ingestion Errors

### Error: "IsADirectoryError: [Errno 21] Is a directory"

**Cause:** Passing directory path instead of JSONL file to `build` command

**Wrong:**
```bash
peachtree build --source data/raw/  # ❌ Directory
```

**Correct:**
```bash
# First: ingest repository
peachtree ingest-local \
  --repo /tmp/datasets/mitre-cve \
  --repo-name cve \
  --license MIT \
  --output data/raw/cve.jsonl

# Then: build from JSONL
peachtree build --source data/raw/cve.jsonl  # ✅ JSONL file
```

---

### Error: "FileNotFoundError: Repository not found"

**Cause:** Invalid repository path

**Solution:**
```bash
# Verify path exists
ls -la /tmp/datasets/repository-name

# Use absolute paths
peachtree ingest-local --repo /tmp/datasets/mitre-cve
```

---

### Error: "No files matched include patterns"

**Cause:** Include patterns don't match any files

**Solution:**
```bash
# List files first
find /tmp/datasets/repo -type f

# Adjust patterns
peachtree ingest-local \
  --repo /tmp/datasets/repo \
  --include "*.md,*.py,*.rb"  # Add more extensions
```

---

## Build Failures

### Error: "ValueError: No source documents provided"

**Cause:** Empty or invalid source JSONL files

**Solution:**
```bash
# Check source files exist
ls -lh data/raw/*.jsonl

# Verify JSONL format
head -1 data/raw/source.jsonl | python -m json.tool

# Check file has content
wc -l data/raw/source.jsonl
```

---

### Error: "KeyError: 'content' or 'source_path'"

**Cause:** Malformed JSONL records missing required fields

**Solution:**
```bash
# Validate source JSONL structure
python -c "
import json
with open('data/raw/source.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            record = json.loads(line)
            assert 'content' in record, f'Missing content at line {i}'
            assert 'source_path' in record, f'Missing source_path at line {i}'
        except Exception as e:
            print(f'Line {i}: {e}')
"
```

**Required JSONL fields:**
```json
{
  "id": "unique-id",
  "content": "text content",
  "source_path": "/path/to/file",
  "source_repo": "repo-name",
  "license": "MIT"
}
```

---

### Error: "AttributeError: 'NoneType' object has no attribute 'instruction'"

**Cause:** DatasetBuilder received invalid input

**Solution:**
```bash
# Rebuild from scratch
rm -rf data/datasets/*.jsonl
rm -rf data/manifests/*.json

# Re-run ingest and build
peachtree ingest-local --repo /path/to/repo --output data/raw/source.jsonl
peachtree build --source data/raw/source.jsonl --dataset data/datasets/output.jsonl
```

---

## Safety Gate Failures

### Error: "Safety gate failed: secret_detection"

**Cause:** Secrets or credentials detected in content

**Solution:**
```bash
# View safety gate report
peachtree audit --dataset data/datasets/training.jsonl

# Find affected records
grep -i "api_key\|password\|secret" data/datasets/training.jsonl

# Re-ingest with filtering
peachtree ingest-local \
  --repo /path/to/repo \
  --exclude "*secret*,*credentials*" \
  --output data/raw/filtered.jsonl
```

**Common secret patterns:**
- API keys: `api_key`, `apikey`, `API_KEY`
- Passwords: `password`, `passwd`, `pwd`
- Private keys: `-----BEGIN PRIVATE KEY-----`
- Tokens: `token`, `auth_token`, `bearer`

---

### Error: "Safety gate failed: license_validation"

**Cause:** Unknown or problematic license detected

**Solution:**
```bash
# Allow unknown licenses (use carefully)
peachtree build \
  --source data/raw/source.jsonl \
  --allow-unknown-license

# OR specify license during ingestion
peachtree ingest-local \
  --repo /path/to/repo \
  --license MIT \
  --output data/raw/source.jsonl
```

**License compliance matrix:**
- ✅ **Safe for training:** MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause
- ⚠️ **Review required:** GPL-2.0, GPL-3.0, AGPL-3.0, LGPL-2.1
- ❌ **Avoid:** Proprietary, unknown licenses

---

### Error: "Safety gate failed: provenance_check"

**Cause:** Records missing source attribution

**Solution:**
```bash
# Verify all records have provenance
python -c "
import json
with open('data/datasets/training.jsonl') as f:
    for i, line in enumerate(f, 1):
        record = json.loads(line)
        if 'provenance' not in record:
            print(f'Line {i}: Missing provenance')
"

# Rebuild with proper provenance
peachtree build \
  --source data/raw/source.jsonl \
  --dataset data/datasets/output.jsonl \
  --manifest data/manifests/manifest.json
```

---

## Quality Issues

### Error: "Quality score below threshold (0.65 < 0.70)"

**Cause:** Dataset quality metrics below acceptable level

**Solution:**
```bash
# Check quality scores
peachtree score --dataset data/datasets/training.jsonl

# Filter low-quality records
python -c "
import json
with open('data/datasets/training.jsonl') as f:
    high_quality = [json.loads(line) for line in f 
                   if json.loads(line).get('quality_score', 0) >= 0.70]
with open('data/datasets/filtered.jsonl', 'w') as f:
    for record in high_quality:
        f.write(json.dumps(record) + '\n')
"
```

**Quality improvement strategies:**
- Filter short content (< 50 characters)
- Remove duplicates
- Enhance source selection
- Add domain-specific content

---

### Error: "High duplicate rate detected (15%)"

**Cause:** Many duplicate records in dataset

**Solution:**
```bash
# Remove duplicates
peachtree dedup \
  --dataset data/datasets/training.jsonl \
  --output data/datasets/deduped.jsonl \
  --method content-hash

# Verify deduplication
peachtree audit --dataset data/datasets/deduped.jsonl
```

---

## Export Problems

### Error: "ValueError: Unknown export format 'custom'"

**Cause:** Unsupported export format specified

**Supported formats:**
- `chatml` - ChatML conversation format
- `alpaca` - Alpaca instruction format
- `sharegpt` - ShareGPT conversation format

**Solution:**
```bash
peachtree export \
  --source data/datasets/training.jsonl \
  --output data/exports/output.jsonl \
  --format chatml  # Use supported format
```

---

### Error: "Export validation failed: Invalid ChatML structure"

**Cause:** Dataset records don't match expected ChatML format

**Solution:**
```bash
# Validate export before use
peachtree validate-export \
  --source data/exports/training.jsonl \
  --format chatml

# Check first record
head -1 data/exports/training.jsonl | python -m json.tool
```

**Valid ChatML structure:**
```json
{
  "messages": [
    {"role": "system", "content": "You are..."},
    {"role": "user", "content": "Question"},
    {"role": "assistant", "content": "Answer"}
  ]
}
```

---

## Performance Issues

### Issue: "Dataset build taking > 10 minutes"

**Optimization strategies:**

1. **Reduce source size**
```bash
# Only include relevant files
peachtree ingest-local \
  --repo /path/to/repo \
  --include "*.md,*.py" \
  --exclude "tests/,vendor/,node_modules/"
```

2. **Use caching**
```bash
export PEACHTREE_CACHE_DIR=~/.cache/peachtree
```

3. **Parallelize ingestion**
```bash
# Process repos in parallel
for repo in repo1 repo2 repo3; do
  peachtree ingest-local --repo $repo --output data/raw/${repo}.jsonl &
done
wait
```

4. **Incremental builds**
```bash
# Only rebuild changed sources
peachtree build \
  --source data/raw/new-sources.jsonl \
  --dataset data/datasets/incremental.jsonl
```

---

### Issue: "High memory usage during build"

**Solutions:**

1. **Process in batches**
```bash
# Split large JSONL files
split -l 1000 data/raw/large.jsonl data/raw/batch-

# Build separately
for batch in data/raw/batch-*; do
  peachtree build --source $batch --dataset data/datasets/$(basename $batch).jsonl
done
```

2. **Increase swap space**
```bash
sudo swapon --show
sudo fallocate -l 8G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## License Compliance

### Issue: "GPL-licensed content in dataset"

**Implications:**
- GPL-2.0/GPL-3.0 require derivative works to be GPL
- AGPL-3.0 requires network disclosure
- May restrict commercial model deployment

**Solutions:**

1. **Exclude GPL content**
```bash
# Filter by license
python -c "
import json
with open('data/datasets/training.jsonl') as f:
    safe_records = [json.loads(line) for line in f 
                   if json.loads(line).get('license') not in ['GPL-2.0', 'GPL-3.0', 'AGPL-3.0']]
with open('data/datasets/commercial-safe.jsonl', 'w') as f:
    for record in safe_records:
        f.write(json.dumps(record) + '\n')
"
```

2. **Use policy pack**
```bash
peachtree policy-pack \
  --dataset data/datasets/training.jsonl \
  --policy config/policy-packs/commercial-ready.json
```

3. **Legal review**
- Consult legal counsel for commercial deployments
- Document all source licenses in model card
- Consider data usage agreements

---

## Debugging Tips

### Enable verbose logging

```bash
export PEACHTREE_LOG_LEVEL=DEBUG
peachtree build --source data/raw/source.jsonl --verbose
```

### Check dataset statistics

```bash
# Record count
wc -l data/datasets/training.jsonl

# File size
du -h data/datasets/training.jsonl

# Unique IDs
jq -r '.id' data/datasets/training.jsonl | sort | uniq | wc -l

# License distribution
jq -r '.license' data/datasets/training.jsonl | sort | uniq -c
```

### Validate JSONL format

```bash
# Check all lines are valid JSON
python -c "
import json
with open('data/datasets/training.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Invalid JSON at line {i}: {e}')
"
```

### Inspect manifest

```bash
# View build manifest
cat data/manifests/manifest.json | python -m json.tool

# Check source repositories
jq '.source_repositories' data/manifests/manifest.json

# Verify provenance
jq '.provenance' data/manifests/manifest.json
```

---

## Getting Help

### Community Support

- **GitHub Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues
- **Discussions:** https://github.com/0ai-Cyberviser/PeachTree/discussions
- **Discord:** (coming soon)

### Bug Reports

Include:
1. PeachTree version: `peachtree --version`
2. Python version: `python --version`
3. Full error traceback
4. Minimal reproducible example
5. Dataset statistics (record count, size)

### Feature Requests

Submit via GitHub Issues with:
- Use case description
- Expected behavior
- Current workaround (if any)

---

**Most issues can be resolved by following PeachTree best practices and safety gates!**
