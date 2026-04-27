# PeachTree Multi-Organization Security Dataset

**New in v1.0:** Production-ready security dataset from 7 leading open-source security repositories

## 🎯 Production Dataset Now Available

PeachTree now includes a **production-ready multi-organization security dataset** specifically curated for training Hancock, our cybersecurity LLM.

### Quick Stats

- **7,202 training records** from 7 security repositories
- **4,187 source documents** (1.95 GB total)
- **Zero duplicates** (100% unique records)
- **Full provenance tracking** (SHA256 content hashing)
- **All safety gates passing** (secrets, licenses, quality)
- **ChatML export ready** for immediate LLM training

### Source Repositories

| Repository | License | Size | Stars | Focus Area |
|------------|---------|------|-------|-----------|
| mitre-cve-database | MIT | 176 KB | 37 | CVE vulnerability database |
| metasploit-framework | BSD-3-Clause | 1.3 GB | 15,000 | Exploit framework, pentesting |
| sqlmap | GPL-2.0 | 99 MB | 6,200 | SQL injection, database security |
| john | GPL-2.0 | 246 MB | 2,500 | Password cracking, authentication |
| clamav | GPL-2.0 | 192 MB | 849 | Antivirus, malware detection |
| snort3 | GPL-2.0 | 115 MB | 666 | Network intrusion detection |
| grok-promptss | AGPL-3.0 | 212 KB | 441 | Security prompts, AI security |

## 🚀 Quick Start: Use the Security Dataset

### Option 1: Use Pre-built Dataset

```bash
# Clone the repository
git clone https://github.com/0ai-Cyberviser/PeachTree.git
cd PeachTree

# The dataset is ready to use!
ls -lh data/datasets/multi-org-security-training.jsonl  # 7,202 records
ls -lh data/manifests/hancock-chatml-export.jsonl     # ChatML format
```

### Option 2: Rebuild from Source

```bash
# Run the automated build script
bash scripts/build-multi-org-dataset.sh

# This will:
# 1. Clone all 7 security repositories
# 2. Ingest documentation and code
# 3. Apply safety gates (secrets, licenses, quality)
# 4. Build unified dataset with provenance
# 5. Export to ChatML format for Hancock
```

### Option 3: Automated Monthly Updates

The dataset is automatically rebuilt monthly via GitHub Actions. See `.github/workflows/rebuild-security-dataset.yml` for the automation workflow.

## 📊 Dataset Details

### What's Included

- **CVE Vulnerability Documentation** - Detailed vulnerability descriptions from MITRE
- **Exploit Frameworks** - Metasploit modules and penetration testing techniques
- **Security Tools** - SQLMap, John the Ripper, ClamAV, Snort usage documentation
- **Security Prompts** - Grok security AI prompts and patterns
- **Code Examples** - Real-world security tool code and configurations
- **Best Practices** - Security hardening and defensive strategies

### Safety & Compliance

✅ **All Safety Gates Passing**
- Secret filtering enabled (no exposed credentials)
- License tracking (all sources properly attributed)
- Provenance verification (complete audit trail)
- Deduplication (zero duplicate records)
- Quality validation (automated scoring)

⚠️ **License Compliance Note**
- MIT/BSD-3-Clause: Safe for commercial use
- GPL-2.0/AGPL-3.0: Requires legal review for commercial deployment

See `MODEL-CARD-SECURITY-DATASET.md` for complete dataset documentation.

## 🔧 Integration with Hancock

### Train Hancock with the Dataset

```bash
# The dataset is export-ready in ChatML format
hancock train \
  --dataset data/manifests/hancock-chatml-export.jsonl \
  --model meta-llama/Llama-2-13b-chat-hf \
  --epochs 3 \
  --output models/hancock-security-v1

# Or use the training configuration
hancock train --config config/hancock-security-training.yaml
```

### System Prompt for Hancock

```
You are Hancock, a cybersecurity AI assistant trained on CVE databases, exploit frameworks, and security tools. You provide expert guidance on vulnerability analysis, security tool usage, threat detection, and defensive security practices. You emphasize ethical use, proper authorization, and responsible disclosure. You refuse to assist with unauthorized hacking or malicious activities.
```

## 📋 Files & Artifacts

### Dataset Files

```
data/
├── datasets/
│   └── multi-org-security-training.jsonl  # 7,202 records, 18 MB
├── manifests/
│   ├── multi-org-build-manifest.json      # Build metadata, provenance
│   └── hancock-chatml-export.jsonl        # ChatML format for training
└── raw/
    ├── cve-records.jsonl                   # CVE source documents
    ├── metasploit-modules.jsonl            # Metasploit documentation
    ├── sqlmap-docs.jsonl                   # SQLMap documentation
    ├── john-docs.jsonl                     # John the Ripper docs
    ├── clamav-docs.jsonl                   # ClamAV documentation
    ├── snort3-docs.jsonl                   # Snort3 documentation
    └── grok-prompts.jsonl                  # Grok security prompts
```

### Documentation

- `MODEL-CARD-SECURITY-DATASET.md` - Complete dataset documentation
- `MULTI-ORG-INTEGRATION.md` - Multi-organization integration guide
- `DATASET-BUILD-COMPLETE.md` - Build completion report
- `config/multi-org-security-datasets.yaml` - Repository inventory
- `config/policy-packs/security-domain-compliance.json` - Security policy pack

### Scripts

- `scripts/build-multi-org-dataset.sh` - Automated dataset build
- `.github/workflows/rebuild-security-dataset.yml` - Monthly automation

## 🏗️ Extending the Dataset

### Add More Repositories

Edit `config/multi-org-security-datasets.yaml` to add new repositories:

```yaml
repositories:
  - name: your-security-repo
    url: https://github.com/org/repo
    license: MIT
    priority: HIGH
    description: Your security tool
    use_case: What it trains on
```

Then rebuild:
```bash
bash scripts/build-multi-org-dataset.sh
```

### Customize Policy Packs

Create custom security policies in `config/policy-packs/`:

```bash
peachtree policy-pack \
  --dataset data/datasets/multi-org-security-training.jsonl \
  --policy config/policy-packs/security-domain-compliance.json \
  --output reports/custom-compliance.json
```

## 📈 Quality Metrics

- **Uniqueness:** 100% (0 duplicates detected)
- **Provenance:** Complete SHA256 tracking for all 4,187 sources
- **Safety:** All gates passing (secrets, licenses, quality)
- **Coverage:** 7 security domains (vulns, exploits, malware, network, auth, IDS, AI security)
- **Freshness:** Monthly automated updates

## 🔄 Continuous Updates

The dataset is rebuilt monthly via GitHub Actions:
- **Schedule:** 1st of each month at 00:00 UTC
- **Process:** Clone latest repos → Ingest → Build → Audit → Export
- **Output:** Pull request with updated dataset for review
- **Manual trigger:** `gh workflow run rebuild-security-dataset.yml`

## 🤝 Multi-Organization Collaboration

This dataset unifies security knowledge from 3 GitHub organizations:
1. **MITRE-Cyber-Security-CVE-Database** (19 repos, 7 members)
2. **Cybeviser** (Johnny Watters)
3. **0ai-cyberviserai** (19 repos, Johnny Watters)

See `MULTI-ORG-INTEGRATION.md` for the complete integration story.

## 📖 Learn More

- **Model Card:** `MODEL-CARD-SECURITY-DATASET.md` - Dataset specification
- **Integration Guide:** `MULTI-ORG-INTEGRATION.md` - Multi-org setup
- **Policy Pack:** `config/policy-packs/security-domain-compliance.json`
- **Build Script:** `scripts/build-multi-org-dataset.sh`
- **Automation:** `.github/workflows/rebuild-security-dataset.yml`

## 💡 Use Cases

### 1. Train Cybersecurity LLM (Hancock)
```bash
# Export is ready in ChatML format
hancock train --dataset data/manifests/hancock-chatml-export.jsonl
```

### 2. Security Q&A System
Train a model to answer questions about CVEs, exploits, and security tools.

### 3. Vulnerability Analysis
Use CVE data to build vulnerability assessment and prioritization models.

### 4. Security Tool Recommendations
Train models to recommend appropriate security tools for specific scenarios.

### 5. Code Security Review
Leverage security code examples for training code review models.

---

**🎉 The multi-org security dataset is production-ready and continuously updated!**

For questions or contributions, see our [GitHub repository](https://github.com/0ai-Cyberviser/PeachTree).
