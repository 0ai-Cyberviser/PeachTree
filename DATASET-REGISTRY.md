# PeachTree Dataset Registry

Centralized registry of all PeachTree-built datasets for tracking, versioning, and discovery.

## Active Datasets

### Security Domain Datasets

#### Multi-Org Security Training Dataset v1.0

**Status:** ✅ Production Ready  
**Last Updated:** 2026-04-27  
**Records:** 7,202  
**Sources:** 4,187 documents from 7 repositories  
**Quality Score:** 0.85  
**License Mix:** MIT, BSD-3-Clause, GPL-2.0, AGPL-3.0  

**Source Repositories:**
- `mitre-cve-database` (176KB, MIT, 37★) - CRITICAL
- `metasploit-framework` (1.3GB, BSD-3-Clause, 15,000★) - HIGH
- `sqlmap` (99MB, GPL-2.0, 6,200★) - HIGH
- `john` (246MB, GPL-2.0, 2,500★) - HIGH
- `clamav` (192MB, GPL-2.0, 849★) - HIGH
- `snort3` (115MB, GPL-2.0, 666★) - HIGH
- `grok-promptss` (212KB, AGPL-3.0, 441★) - HIGH

**Files:**
- Dataset: `data/datasets/multi-org-security-training.jsonl` (~18 MB)
- Manifest: `data/manifests/multi-org-build-manifest.json` (295 KB)
- ChatML Export: `data/manifests/hancock-chatml-export.jsonl` (~19 MB)
- Model Card: `MODEL-CARD-SECURITY-DATASET.md`

**Target Model:** Hancock (cybersecurity LLM)

**Safety Gates:**
- ✅ Secret Detection: Passed (0 violations)
- ✅ License Validation: Passed (all licenses tracked)
- ✅ Provenance Check: Passed (100% coverage)
- ✅ Quality Threshold: Passed (0.85 > 0.70)
- ✅ Deduplication: Passed (0% duplicates)

**Policy Compliance:**
- Policy Pack: `config/policy-packs/security-domain-compliance.json`
- Compliance Status: ✅ All gates passed
- Commercial Use: ⚠️ Review required (GPL content present)

**Rebuild Schedule:** Monthly (1st of month, 00:00 UTC)

**Documentation:**
- [Quick Start Guide](QUICKSTART-SECURITY-DATASET.md)
- [Multi-Org README](MULTI-ORG-DATASET-README.md)
- [Hancock Integration](examples/hancock_integration.py)

**Maintainer:** PeachTree Core Team  
**Contact:** datasets@peachtree.ai

---

## Dataset Versioning

### Version Scheme

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes to dataset structure
MINOR: New sources added, significant updates
PATCH: Bug fixes, small updates, rebuilds
```

### Version History

| Version | Date | Changes | Records | Status |
|---------|------|---------|---------|--------|
| 1.0.0 | 2026-04-27 | Initial multi-org security dataset | 7,202 | ✅ Active |

---

## Dataset Discovery

### By Domain

- **Security:** Multi-Org Security Training v1.0
- **Code:** (Coming soon)
- **General:** (Coming soon)

### By License

- **MIT/Apache-2.0 Safe:** (Subset available)
- **BSD Safe:** (Subset available)
- **GPL/AGPL Mixed:** Multi-Org Security Training v1.0

### By Target Model

- **Hancock (Cybersecurity):** Multi-Org Security Training v1.0
- **General Code LLM:** (Coming soon)

### By Size

- **Small (< 1K records):** -
- **Medium (1K-10K records):** Multi-Org Security Training v1.0
- **Large (> 10K records):** (Coming soon)

---

## Dataset Metadata

### Standard Metadata Fields

Every dataset in registry includes:

```json
{
  "dataset_id": "multi-org-security-v1",
  "version": "1.0.0",
  "created": "2026-04-27T08:19:19Z",
  "updated": "2026-04-27T08:24:05Z",
  "domain": "security",
  "records": 7202,
  "sources": 4187,
  "quality_score": 0.85,
  "duplicate_rate": 0.00,
  "license_mix": ["MIT", "BSD-3-Clause", "GPL-2.0", "AGPL-3.0"],
  "safety_gates_passed": true,
  "policy_compliance": true,
  "target_models": ["Hancock"],
  "maintainer": "PeachTree Core Team",
  "contact": "datasets@peachtree.ai",
  "documentation": [
    "MODEL-CARD-SECURITY-DATASET.md",
    "QUICKSTART-SECURITY-DATASET.md"
  ],
  "files": {
    "dataset": "data/datasets/multi-org-security-training.jsonl",
    "manifest": "data/manifests/multi-org-build-manifest.json",
    "model_card": "MODEL-CARD-SECURITY-DATASET.md"
  },
  "download_url": "https://datasets.peachtree.ai/security/v1.0/bundle.tar.gz",
  "sha256": "abc123...",
  "size_bytes": 18874368
}
```

---

## Adding Datasets to Registry

### Submission Requirements

To add your dataset to the registry:

1. **Complete Dataset Package:**
   - Training dataset (JSONL)
   - Build manifest (JSON)
   - Model card (Markdown)
   - SBOM (JSON)
   - Signatures (JSON)

2. **Safety Requirements:**
   - All safety gates passed
   - Policy compliance verified
   - License compliance documented
   - Provenance complete (100%)

3. **Quality Requirements:**
   - Quality score ≥ 0.70
   - Duplicate rate < 5%
   - Source attribution complete
   - Test evaluation results

4. **Documentation:**
   - Quick start guide
   - Integration examples
   - Known limitations
   - Ethical considerations

### Submission Process

1. **Create dataset bundle:**
```bash
peachtree bundle \
  --dataset data/datasets/your-dataset.jsonl \
  --manifest data/manifests/your-manifest.json \
  --output releases/your-dataset-v1.0.tar.gz \
  --sign \
  --include-sbom
```

2. **Generate registry entry:**
```bash
python scripts/generate-registry-entry.py \
  --dataset releases/your-dataset-v1.0.tar.gz \
  --output registry/your-dataset.json
```

3. **Submit pull request:**
```bash
git checkout -b registry/add-your-dataset
git add registry/your-dataset.json
git commit -m "registry: add your-dataset v1.0"
git push origin registry/add-your-dataset
```

4. **Include in PR:**
- Registry metadata JSON
- Model card
- Safety gate results
- Policy compliance report
- Test evaluation results

---

## Dataset Access

### Public Datasets

Available for download:

```bash
# List available datasets
peachtree registry list --domain security

# Download dataset
peachtree registry download \
  --dataset multi-org-security-v1 \
  --output ~/datasets/
```

### Private Datasets

Organization-specific datasets:

```bash
# Authenticate
peachtree auth login

# List private datasets
peachtree registry list --private

# Download with auth
peachtree registry download \
  --dataset private-security-v1 \
  --token $PEACHTREE_TOKEN
```

---

## Dataset Deprecation

### Deprecation Process

When datasets become outdated:

1. Mark as **deprecated** in registry
2. Provide migration guide to newer version
3. Maintain for 90 days after deprecation
4. Archive and mark as **archived**

### Deprecated Datasets

| Dataset | Version | Deprecated | Replacement | Archive Date |
|---------|---------|------------|-------------|--------------|
| - | - | - | - | - |

---

## Dataset Statistics

### Overall Registry Stats

- **Total Datasets:** 1
- **Active Datasets:** 1
- **Deprecated Datasets:** 0
- **Total Records:** 7,202
- **Total Source Documents:** 4,187
- **Average Quality Score:** 0.85
- **Domains Covered:** Security (1)

### Growth Over Time

```
2026-04:  1 dataset,  7,202 records
2026-05: (planned) +2 datasets, +15,000 records
2026-06: (planned) +3 datasets, +25,000 records
```

---

## Automated Updates

### Continuous Integration

Datasets automatically rebuilt on:

- **Monthly schedule** (1st of month, 00:00 UTC)
- **Source repository updates** (webhook triggered)
- **Manual trigger** (workflow_dispatch)

### Quality Monitoring

- **Quality score tracking** via Prometheus/Grafana
- **Duplicate rate monitoring** with alerts
- **Safety gate validation** on every build
- **Policy compliance checks** automated

### Notification Channels

- GitHub Issues for build failures
- Email alerts for quality degradation
- Slack/Discord for successful rebuilds
- PagerDuty for critical failures

---

## Best Practices

### For Dataset Creators

1. **Start small** - Build focused, high-quality datasets
2. **Document thoroughly** - Complete model cards and guides
3. **Test extensively** - Validate safety and quality
4. **Version properly** - Follow semantic versioning
5. **Maintain actively** - Regular rebuilds and updates

### For Dataset Users

1. **Review model card** - Understand limitations and biases
2. **Check licenses** - Ensure compliance with your use case
3. **Validate quality** - Run your own evaluations
4. **Provide feedback** - Report issues and improvements
5. **Cite properly** - Attribution in model documentation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Adding new datasets
- Updating existing datasets
- Reporting dataset issues
- Improving documentation

---

## Support

- **Registry Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues
- **Dataset Requests:** datasets@peachtree.ai
- **General Questions:** https://github.com/0ai-Cyberviser/PeachTree/discussions

---

**Centralized registry ensures discoverability, quality, and traceability of all PeachTree datasets!**
