---
description: "Run complete safety validation on a PeachTree dataset (secrets, licenses, provenance, quality)"
argument-hint: "path/to/dataset.jsonl"
agent: "agent"
---

# Validate Dataset

Run comprehensive safety and quality validation on a PeachTree dataset file.

## Validation Pipeline

1. **Audit Dataset Records**
   ```bash
   peachtree audit --input {{DATASET_PATH}} --output audit-report.json
   ```

2. **Check Policy Compliance**
   ```bash
   peachtree policy --input {{DATASET_PATH}} --policy-pack config/policy-packs/safety.yaml
   ```

3. **Verify Provenance**
   - Ensure all records have: source_repo, source_path, digest (SHA256)
   - Check for missing or invalid provenance fields

4. **Quality Scoring**
   ```bash
   peachtree quality --input {{DATASET_PATH}} --output quality-report.json
   ```

5. **Duplicate Detection**
   ```bash
   peachtree dedup --input {{DATASET_PATH}} --output {{DATASET_PATH}}.dedup-check.jsonl --dry-run
   ```

6. **Safety Gate Verification**
   - ✅ No secrets (API keys, tokens, private keys)
   - ✅ License compliance (MIT, Apache-2.0, BSD-3-Clause only)
   - ✅ No unsafe content patterns

## Output

Provide a summary report:
- ✅/❌ Safety gates passed
- Quality score (target: ≥0.70 open-safe, ≥0.80 commercial)
- Duplicate count (target: 0 for production)
- Provenance coverage (target: 100%)
- Policy compliance status
- Recommended next steps

If any checks fail, explain the issue and suggest remediation.
