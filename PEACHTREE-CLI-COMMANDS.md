# Multi-Organization Dataset Build Commands

After running the ingestion script successfully, here are the correct PeachTree CLI commands to build the actual dataset.

## Current Status

✅ **7 Repositories Cloned Successfully:**
- mitre-cve-database (CRITICAL)
- metasploit-framework (HIGH - 15k stars)
- sqlmap (HIGH - 6.2k stars)
- john (HIGH - 2.5k stars)
- clamav (HIGH - 849 stars)
- snort3 (HIGH - 666 stars)
- grok-promptss (HIGH - 441 stars)

⚠️ **Placeholder Files Created:**
- `/tmp/peachtree/data/raw/cve-records.jsonl` (77 bytes)
- `/tmp/peachtree/data/raw/metasploit-modules.jsonl` (85 bytes)
- `/tmp/peachtree/data/raw/grok-security-prompts.jsonl` (89 bytes)

---

## Step 1: Build Dataset from Sources

The PeachTree CLI requires `--source`, `--dataset`, and `--manifest` arguments:

```bash
cd /tmp/peachtree

# Build unified security dataset
peachtree build \
  --source /tmp/datasets/mitre-cve \
  --source /tmp/datasets/metasploit-framework \
  --source /tmp/datasets/sqlmap \
  --source /tmp/datasets/john \
  --source /tmp/datasets/clamav \
  --source /tmp/datasets/snort3 \
  --source /tmp/datasets/grok-promptss \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --manifest data/manifests/multi-org-build-manifest.json \
  --domain security
```

### Alternative: Build from Each Source Individually

If the multi-source approach doesn't work, build from each source:

```bash
# CVE Database (CRITICAL)
peachtree build \
  --source /tmp/datasets/mitre-cve \
  --dataset data/datasets/cve-records.jsonl \
  --manifest data/manifests/cve-manifest.json \
  --domain security

# Metasploit Framework
peachtree build \
  --source /tmp/datasets/metasploit-framework \
  --dataset data/datasets/metasploit-exploits.jsonl \
  --manifest data/manifests/metasploit-manifest.json \
  --domain security

# Grok Security Prompts
peachtree build \
  --source /tmp/datasets/grok-promptss \
  --dataset data/datasets/grok-prompts.jsonl \
  --manifest data/manifests/grok-manifest.json \
  --domain security
```

---

## Step 2: Run Safety Gates & Quality Checks

After building, audit the dataset:

```bash
# Run comprehensive audit
peachtree audit \
  --input data/datasets/multi-org-security-training.jsonl \
  --output reports/multi-org-audit.json \
  --detailed

# Check audit results
cat reports/multi-org-audit.json | python -m json.tool
```

---

## Step 3: Export for Hancock Training

The `export` command requires `--source`, `--output`, and `--format`:

```bash
# Export in ChatML format for Hancock
peachtree export \
  --source data/datasets/multi-org-security-training.jsonl \
  --output data/manifests/hancock-multi-org-handoff.json \
  --format chatml \
  --system-prompt "You are Hancock, a cybersecurity AI assistant trained on CVE databases, exploit frameworks, and security tools."

# Alternative: Alpaca format
peachtree export \
  --source data/datasets/multi-org-security-training.jsonl \
  --output data/manifests/hancock-alpaca-format.json \
  --format alpaca

# Alternative: ShareGPT format
peachtree export \
  --source data/datasets/multi-org-security-training.jsonl \
  --output data/manifests/hancock-sharegpt-format.json \
  --format sharegpt
```

---

## Step 4: Verify Output

Check the generated files:

```bash
# Check dataset size
wc -l data/datasets/multi-org-security-training.jsonl

# Check first few records
head -n 3 data/datasets/multi-org-security-training.jsonl | python -m json.tool

# Check manifest
cat data/manifests/multi-org-build-manifest.json | python -m json.tool

# Check audit report
cat reports/multi-org-audit.json | python -m json.tool

# Check Hancock handoff
cat data/manifests/hancock-multi-org-handoff.json | python -m json.tool
```

---

## Step 5: Quality Metrics

Expected outcomes after successful build:

- **Dataset Records**: 10,000+ JSONL records (depends on source content)
- **Provenance**: Every record traces back to source repo + file path
- **Safety Gates**: 5/5 passing (secrets, licenses, quality, dedup, provenance)
- **Quality Score**: ≥ 0.85
- **Duplicate Rate**: < 5%
- **License Compliance**: 
  - ✅ MIT, BSD-3-Clause, Apache-2.0 (safe for commercial use)
  - ⚠️ GPL-2.0 (clamav, sqlmap) - needs legal review
  - ⚠️ AGPL-3.0 (grok-promptss) - needs legal review

---

## Troubleshooting

### Error: "No valid records found"
- Check that repositories have actual data files (not just code)
- Verify file patterns match actual repository structure
- Use `--domain security` to filter for security-relevant content

### Error: "License gate failed"
- Review `reports/multi-org-audit.json` for license violations
- Exclude GPL/AGPL repos if commercial training not allowed
- Use `--allow-unknown-license` flag cautiously

### Error: "Quality score too low"
- Increase minimum quality threshold: `--min-quality 0.75`
- Review quality metrics in audit report
- Filter out low-quality sources

---

## Next Steps After Successful Build

1. **Review Audit Report** - Verify all safety gates passed
2. **Legal Approval** - Get sign-off for GPL/AGPL licensed repos
3. **Commit Results** - Add generated datasets to git
4. **Hancock Handoff** - Transfer handoff manifest to Hancock training pipeline
5. **Model Training** - Begin cybersecurity LLM fine-tuning

---

## Quick Reference

```bash
# Build
peachtree build --source <dir> --dataset <output.jsonl> --manifest <manifest.json> --domain security

# Audit  
peachtree audit --input <dataset.jsonl> --output <audit.json> --detailed

# Export
peachtree export --source <dataset.jsonl> --output <export.json> --format chatml

# Help
peachtree build --help
peachtree audit --help
peachtree export --help
```

---

**Status**: Ready to execute actual PeachTree build commands
**Next Action**: Run Step 1 build commands above
