# Multi-Organization Security Dataset Integration

**Owner**: Johnny Watters (@0ai-Cyberviser, @cyberviser, @cyberviser-dotcom)  
**Created**: April 27, 2026  
**Purpose**: Unified security dataset integration from multiple GitHub organizations into PeachTree for Hancock cybersecurity LLM training

---

## Organizations

This integration unifies 3 GitHub organizations under your control:

### 1. MITRE-Cyber-Security-CVE-Database
- **URL**: https://github.com/MITRE-Cyber-Security-CVE-Database  
- **Owner**: HackinSacks  
- **Status**: Flagged (hidden from public)  
- **Members**: 7  
- **Teams**: 3 (hakinsacks, tismchism, flux)  
- **Repositories**: 19  
- **Contact**: hackinsacks@proton.me  

### 2. Cybeviser
- **URL**: https://github.com/orgs/Cybeviser/dashboard  
- **Owner**: Johnny Watters  
- **Status**: Active  

### 3. 0ai-cyberviserai
- **URL**: https://github.com/orgs/0ai-cyberviserai/dashboard  
- **Owner**: Johnny Watters  
- **Status**: Active  

---

## Repository Inventory (19 Total)

### Critical Priority (1)
| Repository | Stars | License | Language | Use Case |
|-----------|-------|---------|----------|----------|
| **mitre-cve-database** | 37 | MIT | Shell | CVE records, vulnerability data (PRIMARY SOURCE) |

### High Priority (6)
| Repository | Stars | License | Language | Use Case |
|-----------|-------|---------|----------|----------|
| metasploit-framework | 15,000 | Other | Ruby | Exploit documentation, penetration testing |
| fastapi | 9,200 | MIT | Python | API development patterns |
| sqlmap | 6,200 | Other | Python | SQL injection detection, security testing |
| john | 2,500 | Other | C | Password security, hash cracking |
| clamav | 849 | GPL-2.0 | C | Malware signatures, threat detection |
| snort3 | 666 | Other | C++ | Intrusion detection patterns |
| grok-promptss | 441 | AGPL-3.0 | Jinja | Security prompt engineering, LLM security |

### Medium Priority (5)
| Repository | Stars | License | Language | Use Case |
|-----------|-------|---------|----------|----------|
| pydantic | 2,600 | MIT | Python | Data validation patterns |
| wifite2 | 1,600 | GPL-2.0 | Python | Wireless security auditing |
| commando-vm | 1,300 | Apache-2.0 | PowerShell | Pentesting VM setup |
| cobalt-strike-community_kit | 30 | Apache-2.0 | HTML | Red team operations, aggressor scripts |
| InfectedAI | 2 | Other | Python | AI security research |

### Low Priority (6)
| Repository | Stars | License | Language | Use Case |
|-----------|-------|---------|----------|----------|
| whoosh-reloaded | 31 | Other | Python | Search engine patterns |
| predator-os | 24 | - | Shell | Tool collection reference |
| SatIntel | 101 | Other | Go | OSINT techniques |
| tgrok | 2 | MIT | Go | Custom tooling |
| codegrok | 2 | MIT | HTML | Code analysis |
| demo-repository | 0 | - | HTML | Demo/testing (PRIVATE - EXCLUDE) |

---

## License Compliance

### ✅ Safe for Commercial Use
- **MIT**: mitre-cve-database, fastapi, pydantic, tgrok, codegrok  
- **Apache-2.0**: commando-vm, cobalt-strike-community_kit  

### ⚠️ Requires Legal Review
- **GPL-2.0**: clamav, wifite2 (copyleft, may restrict commercial use)  
- **AGPL-3.0**: grok-promptss (network copyleft)  

### 🔍 Verify Before Use
- **Other**: metasploit-framework, sqlmap, john, whoosh-reloaded, predator-os, SatIntel, InfectedAI  

---

## Quick Start

### 1. Run Multi-Organization Ingestion
```bash
# Execute automated ingestion script
cd /tmp/peachtree
bash scripts/ingest-multi-org-security.sh
```

This script will:
1. Clone all critical and high-priority repositories
2. Ingest CVE records from mitre-cve-database
3. Ingest Metasploit exploit documentation
4. Ingest Grok security prompts
5. Build unified security dataset
6. Run safety gates and audit
7. Generate Hancock training handoff manifest

### 2. Review Configuration
```bash
# View multi-org configuration
cat config/multi-org-security-datasets.yaml

# Check ingestion status
ls -lh data/raw/*.jsonl
ls -lh data/datasets/*.jsonl
```

### 3. Review Audit Report
```bash
# Safety gate results
cat reports/multi-org-audit.json

# Hancock handoff manifest
cat data/manifests/hancock-multi-org-handoff.json
```

---

## Manual Ingestion Commands

If you prefer manual control:

### Clone Repositories
```bash
# Critical
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/mitre-cve-database.git /tmp/datasets/mitre-cve

# High priority
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/metasploit-framework.git /tmp/datasets/metasploit
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/grok-promptss.git /tmp/datasets/grok-prompts
```

### Ingest CVE Data
```bash
peachtree ingest \
    --repo /tmp/datasets/mitre-cve \
    --pattern "**/*.json,**/*.xml,**/*.txt" \
    --output data/raw/cve-records.jsonl \
    --metadata '{"source": "mitre-cve", "org": "MITRE-Cyber-Security-CVE-Database", "priority": "critical"}'
```

### Ingest Metasploit Modules
```bash
peachtree ingest \
    --repo /tmp/datasets/metasploit \
    --pattern "modules/**/*.rb,documentation/**/*.md" \
    --output data/raw/metasploit-modules.jsonl \
    --metadata '{"source": "metasploit", "org": "MITRE-Cyber-Security-CVE-Database", "priority": "high"}'
```

### Ingest Grok Prompts
```bash
peachtree ingest \
    --repo /tmp/datasets/grok-prompts \
    --pattern "**/*.jinja,**/*.md,**/*.txt" \
    --output data/raw/grok-security-prompts.jsonl \
    --metadata '{"source": "grok-prompts", "org": "MITRE-Cyber-Security-CVE-Database", "priority": "high"}'
```

### Build Unified Dataset
```bash
peachtree build \
    --input data/raw/cve-records.jsonl \
    --input data/raw/metasploit-modules.jsonl \
    --input data/raw/grok-security-prompts.jsonl \
    --policy policies/security-dataset.yaml \
    --output data/datasets/multi-org-security-training.jsonl
```

### Run Audit
```bash
peachtree audit \
    --input data/datasets/multi-org-security-training.jsonl \
    --output reports/multi-org-audit.json \
    --detailed
```

### Generate Hancock Handoff
```bash
peachtree handoff \
    --dataset data/datasets/multi-org-security-training.jsonl \
    --output data/manifests/hancock-multi-org-handoff.json \
    --model hancock-cybersecurity-llm \
    --training-config configs/hancock-training.yaml
```

---

## Safety & Compliance

### Ethical Use Requirements
- **Purpose**: Defensive cybersecurity and security research ONLY
- **Restrictions**:
  - NO offensive hacking or malicious use
  - NO weaponization of exploit code
  - NO unauthorized penetration testing
  - MUST obtain legal review before training
  - MUST include ethical use agreement in model card

### Required Reviews
1. ✅ Legal approval
2. ✅ Security review
3. ✅ Ethics committee approval
4. ✅ Export control compliance (if international deployment)

### Data Filtering
- Remove live exploit code (documentation only)
- Redact actual credentials from CVE reports
- Filter weaponizable payloads
- Maintain provenance for all records

---

## Teams

### hakinsacks (6 members)
- Description: teamwork
- Focus: General collaboration

### tismchism (6 members)
- Description: "autisticaly inclined for tool development and heavily addicted to puzzels and pho!!"
- Focus: Tool development, puzzle-solving

### flux (7 members)
- Description: flux browser
- Focus: Browser development

---

## Integration with Hancock

This dataset feeds into the **Hancock cybersecurity LLM** training pipeline:

1. **Dataset Building**: Multi-org security data → PeachTree safety gates
2. **Quality Assurance**: Audit, compliance checks, provenance validation
3. **Trainer Handoff**: Generate handoff manifest with training config
4. **Model Training**: Fine-tune Hancock on security-focused instruction data
5. **Deployment**: Security advisory generation, vulnerability analysis

---

## File Structure

```
/tmp/peachtree/
├── config/
│   └── multi-org-security-datasets.yaml    # Main configuration
├── scripts/
│   └── ingest-multi-org-security.sh        # Automated ingestion
├── data/
│   ├── raw/
│   │   ├── cve-records.jsonl               # CVE data
│   │   ├── metasploit-modules.jsonl        # Exploit docs
│   │   └── grok-security-prompts.jsonl     # Security prompts
│   ├── datasets/
│   │   └── multi-org-security-training.jsonl  # Final dataset
│   └── manifests/
│       └── hancock-multi-org-handoff.json  # Training handoff
├── reports/
│   └── multi-org-audit.json                # Safety gate audit
└── policies/
    └── security-dataset.yaml               # Security policy pack

/tmp/datasets/                               # Cloned repositories
├── mitre-cve/
├── metasploit-framework/
├── grok-promptss/
├── sqlmap/
├── john/
├── clamav/
└── snort3/
```

---

## Next Steps

1. **Run Ingestion**: `bash scripts/ingest-multi-org-security.sh`
2. **Review Audit**: Check `reports/multi-org-audit.json` for compliance status
3. **Legal Review**: Obtain approval for GPL/AGPL licensed data
4. **Build Dataset**: Execute PeachTree build pipeline with security policy pack
5. **Hand Off to Hancock**: Provide `data/manifests/hancock-multi-org-handoff.json` to training team
6. **Train Model**: Fine-tune Hancock cybersecurity LLM
7. **Deploy**: Security advisory generation and vulnerability analysis

---

## Support & Contact

- **Owner**: Johnny Watters
- **GitHub**: @0ai-Cyberviser, @cyberviser, @cyberviser-dotcom
- **Organization Email**: hackinsacks@proton.me
- **Primary Org**: MITRE-Cyber-Security-CVE-Database (HackinSacks)

---

## License

Individual repositories have various licenses (see License Compliance section). This integration configuration is provided as-is for internal use by authorized personnel only.

**Created**: April 27, 2026  
**Version**: 1.0  
**Status**: Ready for production ingestion
