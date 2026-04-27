# Model Card: Multi-Organization Security Dataset

**Dataset Name:** Multi-Organization Security Training Dataset  
**Version:** 1.0.0  
**Release Date:** April 27, 2026  
**License:** Mixed (see License Details)  
**Maintained By:** 0ai-Cyberviser Organization  
**Repository:** https://github.com/0ai-Cyberviser/PeachTree

---

## Dataset Description

### Summary
A comprehensive security-focused training dataset aggregating knowledge from 7 leading open-source security repositories across 3 GitHub organizations. Designed specifically for training Hancock, a cybersecurity-focused large language model.

### Dataset Statistics
- **Total Records:** 7,202 unique training examples
- **Source Documents:** 4,187 files
- **Total Source Data:** 1.95 GB
- **Dataset Size:** ~18 MB (JSONL)
- **Duplicates:** 0 (100% unique)
- **Provenance:** Complete SHA256 tracking for all sources

### Languages
- Primary: English
- Code: Python, Ruby, C, C++, Shell, Assembly (from security tool repositories)

---

## Dataset Composition

### Source Repositories

| Repository | License | Size | Stars | Records | Domain Focus |
|------------|---------|------|-------|---------|--------------|
| mitre-cve-database | MIT | 176 KB | 37 | ~500 | CVE vulnerability database |
| metasploit-framework | BSD-3-Clause | 1.3 GB | 15,000 | ~3,200 | Exploit framework, penetration testing |
| sqlmap | GPL-2.0 | 99 MB | 6,200 | ~800 | SQL injection, database security |
| john | GPL-2.0 | 246 MB | 2,500 | ~900 | Password cracking, authentication |
| clamav | GPL-2.0 | 192 MB | 849 | ~700 | Antivirus, malware detection |
| snort3 | GPL-2.0 | 115 MB | 666 | ~600 | Network intrusion detection |
| grok-promptss | AGPL-3.0 | 212 KB | 441 | ~500 | Security prompts, AI security |

### Content Categories
- **Vulnerability Documentation:** CVE descriptions, exploit details, patch information
- **Security Tool Documentation:** Framework usage, command references, configuration guides
- **Code Examples:** Exploit code, security tools, detection patterns
- **Best Practices:** Security hardening, defensive strategies, incident response
- **Threat Intelligence:** Attack patterns, malware signatures, intrusion detection rules

### Data Collection Methodology
1. **Local Repository Cloning:** All 7 repositories cloned to local storage
2. **PeachTree Ingestion:** Used `peachtree ingest-local` to extract documentation
3. **Safety Gates Applied:** Secret filtering, license tracking, provenance verification
4. **Deduplication:** SHA256 content hashing to remove duplicates
5. **Quality Validation:** Automated quality scoring and review

---

## Intended Use

### Primary Use Case
**Training Hancock Cybersecurity LLM** - This dataset is specifically curated to train a large language model focused on:
- CVE vulnerability analysis and explanation
- Security tool usage and recommendations
- Exploit development and mitigation strategies
- Threat detection and incident response
- Security best practices and hardening

### Supported Tasks
- ✅ Vulnerability Q&A and explanation
- ✅ Security tool recommendation and usage guidance
- ✅ Exploit analysis and defensive coding
- ✅ Threat detection pattern generation
- ✅ Security code review and assessment
- ✅ Incident response planning
- ✅ Compliance and policy guidance

### Out-of-Scope Uses
- ❌ Malicious exploit generation without authorization
- ❌ Automated vulnerability exploitation
- ❌ Unauthorized penetration testing
- ❌ Privacy-invasive security testing
- ❌ Production systems without proper authorization

---

## Safety & Ethics

### Safety Gates Applied
1. **Secret Filtering:** All credentials, API keys, and sensitive tokens removed
2. **License Compliance:** All source licenses tracked and attributed
3. **Provenance Tracking:** Complete audit trail for every record
4. **Deduplication:** Zero duplicate records ensure data quality
5. **Quality Validation:** Automated scoring for content quality

### Ethical Considerations

**Dual-Use Nature:** This dataset contains security tools and exploit information that has legitimate defensive use but could potentially be misused for malicious purposes. Users must:
- Comply with all applicable laws and regulations
- Use only for authorized security testing and research
- Follow responsible disclosure practices
- Respect intellectual property and licensing terms

**License Compliance Requirements:**
- **MIT & BSD-3-Clause:** Open for commercial and non-commercial use
- **GPL-2.0:** Derivative works must be GPL-licensed (sqlmap, john, clamav, snort3)
- **AGPL-3.0:** Network use triggers copyleft requirements (grok-promptss)

**Recommendation:** Conduct legal review before production deployment involving GPL/AGPL-licensed content.

### Bias Considerations
- **Geographic Bias:** Primarily English-language, Western security perspectives
- **Tool Bias:** Focus on open-source tools may not represent commercial security landscape
- **Temporal Bias:** Security information current as of April 2026
- **Domain Bias:** Emphasis on offensive security tools (pentesting, exploitation)

---

## Data Processing

### Safety Pipeline
```
Raw Repositories (1.95 GB)
    ↓
PeachTree Ingestion (ingest-local)
    ↓
Source Documents (4,187 files, JSONL)
    ↓
Safety Gates (secrets, licenses, quality)
    ↓
Dataset Builder (dedup, provenance)
    ↓
Final Dataset (7,202 unique records)
    ↓
ChatML Export (Hancock training format)
```

### Provenance Tracking
Every record includes:
- `source_repo`: Repository name
- `source_path`: File path within repository
- `source_digest`: SHA256 hash of source content
- `license`: License identifier (SPDX format)
- `created_at`: Ingestion timestamp

### Quality Assurance
- Automated duplicate detection (SHA256 content hashing)
- License validation and tracking
- Secret detection and filtering
- Content quality scoring
- Manual review of sample records

---

## Training Data Statistics

### Record Distribution by Source
- Metasploit Framework: ~44% (largest contributor)
- MITRE CVE Database: ~7%
- SQLMap: ~11%
- John the Ripper: ~13%
- ClamAV: ~10%
- Snort3: ~8%
- Grok Prompts: ~7%

### Content Characteristics
- **Average Record Length:** ~2,500 characters
- **Content Types:** Documentation (60%), code examples (25%), configuration (15%)
- **Code Languages:** Python (35%), Ruby (25%), C/C++ (20%), Shell (15%), Other (5%)

---

## Model Training Recommendations

### Recommended Architecture
- **Base Model:** LLaMA 2/3, Mistral, or similar foundation model
- **Fine-tuning Method:** LoRA, QLoRA, or full fine-tuning
- **Context Window:** 4096+ tokens (some security docs are lengthy)
- **Batch Size:** Adjust based on GPU memory availability

### Training Configuration
```yaml
model: meta-llama/Llama-2-13b-chat-hf
dataset: data/manifests/hancock-chatml-export.jsonl
format: chatml
epochs: 3
learning_rate: 2e-5
max_length: 4096
batch_size: 4
gradient_accumulation: 8
lora_rank: 64
lora_alpha: 16
```

### System Prompt Recommendation
```
You are Hancock, a cybersecurity AI assistant trained on CVE databases, exploit frameworks, and security tools. You provide expert guidance on vulnerability analysis, security tool usage, threat detection, and defensive security practices. You emphasize ethical use, proper authorization, and responsible disclosure. You refuse to assist with unauthorized hacking or malicious activities.
```

### Evaluation Metrics
- Security knowledge accuracy (CVE details, tool usage)
- Ethical alignment (refusing malicious requests)
- Code generation quality (security tool scripts)
- Vulnerability explanation clarity
- Compliance with responsible disclosure practices

---

## Limitations & Biases

### Known Limitations
1. **Temporal Coverage:** Security data current only through April 2026
2. **English Language:** Limited non-English security documentation
3. **Open-Source Focus:** Commercial security tools underrepresented
4. **Offensive Emphasis:** More exploitation than pure defensive content
5. **No Zero-Days:** Only publicly disclosed vulnerabilities included

### Potential Biases
- **Tool Selection Bias:** Popular GitHub repos overrepresented
- **Documentation Quality:** Varies significantly across repositories
- **Security Domain Bias:** Offensive security weighted higher than compliance/GRC
- **Platform Bias:** Linux/Unix security tools overrepresented vs. Windows

### Mitigation Strategies
- Combine with additional defensive security datasets
- Include compliance and governance documentation
- Add Windows security tool documentation
- Incorporate security policy and framework content (NIST, CIS, etc.)
- Regular dataset updates with new vulnerabilities and tools

---

## Maintenance & Updates

### Update Schedule
- **Major Updates:** Quarterly (re-ingestion of all repositories)
- **CVE Updates:** Monthly (MITRE CVE database refresh)
- **Security Tool Updates:** As major versions released
- **Ad-hoc Updates:** Critical vulnerabilities or significant tool updates

### Version History
- **v1.0.0** (April 27, 2026): Initial release with 7 repositories, 7,202 records

### Deprecation Policy
- Dataset versions maintained for minimum 12 months
- Deprecated versions clearly marked in README
- Migration guides provided for major version changes

---

## License Information

### Dataset License
This dataset is a compilation of content from multiple sources with different licenses. Users must comply with ALL applicable licenses:

**Permissive Licenses (Commercial Use Allowed):**
- mitre-cve-database: MIT License
- metasploit-framework: BSD-3-Clause License

**Copyleft Licenses (Derivative Work Restrictions):**
- sqlmap: GPL-2.0 (derivative works must be GPL-licensed)
- john: GPL-2.0 (derivative works must be GPL-licensed)
- clamav: GPL-2.0 (derivative works must be GPL-licensed)
- snort3: GPL-2.0 (derivative works must be GPL-licensed)
- grok-promptss: AGPL-3.0 (network use triggers copyleft)

**Legal Disclaimer:** This dataset is provided for research and authorized security testing only. Users are responsible for ensuring compliance with all applicable licenses and laws. The dataset maintainers make no warranties regarding the accuracy, completeness, or safety of the content.

### Attribution Requirements
When using this dataset, please cite:
```
Multi-Organization Security Dataset v1.0.0
0ai-Cyberviser Organization, April 2026
https://github.com/0ai-Cyberviser/PeachTree
Built with PeachTree Dataset Control Plane
```

---

## Contact & Support

- **Maintainer:** 0ai-Cyberviser Organization
- **Repository:** https://github.com/0ai-Cyberviser/PeachTree
- **Issues:** https://github.com/0ai-Cyberviser/PeachTree/issues
- **Documentation:** See repository README and integration guides

### Reporting Issues
- **Dataset Quality Issues:** Open GitHub issue with record ID and description
- **License Concerns:** Contact maintainers directly via GitHub
- **Security Vulnerabilities:** Follow responsible disclosure to maintainers
- **Ethical Concerns:** Report via GitHub security advisory

---

## Acknowledgments

This dataset builds upon the work of thousands of security researchers and open-source contributors. Special thanks to:
- MITRE Corporation (CVE database)
- Rapid7 (Metasploit Framework)
- sqlmap development team
- John the Ripper community
- ClamAV/Cisco Talos team
- Snort/Cisco team
- Grok prompts contributors

---

**Last Updated:** April 27, 2026  
**Model Card Version:** 1.0  
**Dataset Version:** 1.0.0
