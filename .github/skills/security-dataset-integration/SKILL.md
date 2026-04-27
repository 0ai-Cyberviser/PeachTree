---
name: security-dataset-integration
description: "Use when: ingesting security data from CVE databases, vulnerability reports, penetration testing datasets, or cybersecurity corpora into PeachTree. Handles MITRE CVE data, Metasploit modules, ClamAV signatures, and other security-focused training data sources."
---

# Security Dataset Integration Skill

## Purpose
Integrate security and vulnerability databases into PeachTree's dataset control plane for training security-focused ML models (e.g., Hancock cybersecurity LLM).

## When to Use This Skill
- Ingesting MITRE CVE database records
- Processing vulnerability reports and exploit databases
- Building security-focused training datasets
- Integrating penetration testing corpora (Metasploit, Cobalt Strike)
- Collecting malware signatures (ClamAV) for threat detection models
- Creating cybersecurity instruction-tuning datasets

## Security Data Sources

### 1. MITRE CVE Database
**Repository**: `mitre-cve-database` (Shell, 37 stars)
**Organization**: MITRE-Cyber-Security-CVE-Database / Cybeviser
**Data Type**: Common Vulnerabilities and Exposures (CVE) records
**License**: Public domain (verify before ingestion)

**Ingestion Workflow**:
```bash
# Clone repository
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/mitre-cve-database.git /tmp/cve-data

# Ingest CVE records
peachtree ingest \
    --repo /tmp/cve-data \
    --pattern "*.json,*.xml,*.txt" \
    --output data/raw/cve-records.jsonl \
    --metadata '{"source": "mitre-cve", "type": "vulnerability"}'

# Build dataset with security-specific policy pack
peachtree build \
    --input data/raw/cve-records.jsonl \
    --policy policies/security-dataset.yaml \
    --output data/datasets/cve-training.jsonl
```

### 2. Metasploit Framework
**Repository**: `metasploit-framework` (forked from rapid7/metasploit-framework)
**Data Type**: Exploit modules, payloads, auxiliary scripts
**Language**: Ruby
**License**: BSD 3-Clause (verify)

**Use Cases**:
- Exploit documentation for vulnerability understanding
- Penetration testing command examples
- Security tool instruction tuning

**Ingestion Workflow**:
```bash
# Clone Metasploit fork
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/metasploit-framework.git /tmp/metasploit

# Extract documentation and exploit descriptions
peachtree ingest \
    --repo /tmp/metasploit \
    --pattern "modules/**/*.rb,documentation/**/*.md" \
    --output data/raw/metasploit-modules.jsonl \
    --metadata '{"source": "metasploit", "type": "exploit-framework"}'
```

### 3. ClamAV Signatures
**Repository**: `clamav` (forked from Cisco-Talos/clamav)
**Data Type**: Antivirus signatures, malware detection rules
**Language**: C
**License**: GPL-2.0 (commercial use restricted)

**Use Cases**:
- Malware signature patterns
- Threat detection rule examples
- Security scanning logic

**Ingestion Workflow**:
```bash
# Clone ClamAV fork
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/clamav.git /tmp/clamav

# Extract signature documentation
peachtree ingest \
    --repo /tmp/clamav \
    --pattern "docs/**/*.md,*.cvd" \
    --output data/raw/clamav-signatures.jsonl \
    --metadata '{"source": "clamav", "type": "malware-signatures"}'
```

### 4. Cobalt Strike Community Kit
**Repository**: `cobalt-strike-community_kit` (forked from Cobalt-Strike/community_kit)
**Data Type**: Aggressor scripts, toolkit modules
**Language**: HTML
**License**: Verify before use

**Use Cases**:
- Red team operation documentation
- Attack simulation scenarios
- Security training examples

## Security Dataset Policy Pack

### Policy Pack: `security-dataset.yaml`
```yaml
name: "security-dataset"
version: "1.0"
description: "Policy pack for security-focused training data"

gates:
  # CRITICAL: Secret filtering is REQUIRED for security datasets
  - name: "secret-filter"
    required: true
    config:
      strict: true
      # Additional patterns for security data
      patterns:
        - "API_KEY"
        - "ACCESS_TOKEN"
        - "PRIVATE_KEY"
        - "password\\s*="
        - "exploit.*credential"
  
  # License compliance
  - name: "license-checker"
    required: true
    config:
      allowed_licenses:
        - "Public Domain"
        - "MIT"
        - "Apache-2.0"
        - "BSD-3-Clause"
      # WARNING: GPL may restrict commercial use
      warn_licenses:
        - "GPL-2.0"
        - "GPL-3.0"
  
  # Provenance tracking (CRITICAL for security data)
  - name: "provenance-tracker"
    required: true
    config:
      require_source_repo: true
      require_source_path: true
      require_digest: true
      require_timestamp: true
  
  # Quality scoring
  - name: "quality-scorer"
    required: true
    config:
      minimum_score: 0.70
      scoring_criteria:
        - completeness
        - technical_accuracy
        - exploit_validity
  
  # Deduplication (critical for CVE data)
  - name: "deduplicator"
    required: true
    config:
      max_duplicate_rate: 0.05
      similarity_threshold: 0.90

# Security-specific compliance
compliance:
  legal_review: true
  security_review: true  # REQUIRED for security datasets
  ethics_review: true    # Verify responsible use
  export_control: true   # Check export restrictions

# Thresholds
thresholds:
  quality_score: 0.70
  duplicate_rate: 0.05
  
# Security-specific metadata
security_metadata:
  requires_ethical_use_agreement: true
  restricted_to_defensive_use: true
  no_weaponization: true
```

## Safety Considerations

### CRITICAL Security Dataset Rules

1. **Ethical Use Only**
   - Security datasets MUST include ethical use agreements
   - Document intended use case (defensive security, education)
   - NO datasets for offensive hacking or malicious use
   - Obtain legal review before training on exploit data

2. **Secret Filtering**
   - Run strict secret filtering (even stricter than general datasets)
   - Remove actual credentials, API keys, tokens from CVE reports
   - Redact real IP addresses, domain names if sensitive
   - Filter live exploit code that could be weaponized

3. **License Compliance**
   - CVE data is typically public domain → SAFE
   - Metasploit is BSD-3-Clause → SAFE for commercial use
   - ClamAV is GPL-2.0 → RESTRICTED (verify commercial licensing)
   - Cobalt Strike → VERIFY LICENSE before use

4. **Export Control**
   - Some security tools have export restrictions
   - Verify ITAR/EAR compliance if deploying internationally
   - Document export control review in compliance report

5. **Provenance Tracking**
   - EVERY security record MUST have full provenance
   - Track CVE ID, publish date, source repository
   - Maintain audit trail for security compliance

## Hancock Integration

### Hancock Cybersecurity LLM
**Use Case**: Train Hancock on vulnerability data for security advisory generation

**Dataset Requirements**:
- CVE descriptions with mitigation strategies
- Exploit documentation with defensive countermeasures
- Security best practices and compliance guides
- Incident response playbooks

**Integration Workflow**:
```bash
# 1. Build combined security dataset
peachtree build \
    --input data/raw/cve-records.jsonl \
    --input data/raw/metasploit-modules.jsonl \
    --policy policies/security-dataset.yaml \
    --output data/datasets/hancock-security-training.jsonl

# 2. Audit for security compliance
peachtree audit \
    --input data/datasets/hancock-security-training.jsonl \
    --output reports/security-audit-report.json \
    --detailed

# 3. Generate security model card
peachtree card \
    --dataset data/datasets/hancock-security-training.jsonl \
    --output reports/hancock-model-card.md \
    --template security-model

# 4. Create Hancock trainer handoff
peachtree handoff \
    --dataset data/datasets/hancock-security-training.jsonl \
    --output data/manifests/hancock-trainer-handoff.json \
    --model hancock-cybersecurity-llm
```

## JSONL Schema for Security Data

### CVE Record Schema
```json
{
  "id": "CVE-2024-12345-record",
  "text": "CVE-2024-12345: Buffer overflow in XYZ library allows remote code execution...",
  "metadata": {
    "cve_id": "CVE-2024-12345",
    "cvss_score": 9.8,
    "severity": "CRITICAL",
    "affected_products": ["XYZ Library 1.0-2.5"],
    "published_date": "2024-03-15",
    "source_document_id": "cve-doc-12345",
    "provenance": {
      "repo": "github.com/MITRE-Cyber-Security-CVE-Database/mitre-cve-database",
      "path": "data/cve-2024/CVE-2024-12345.json",
      "digest": "sha256:abc123..."
    },
    "quality_score": 0.92,
    "tags": ["vulnerability", "buffer-overflow", "rce"]
  },
  "created_at": "2026-04-27T10:00:00Z"
}
```

### Exploit Record Schema
```json
{
  "id": "exploit-metasploit-1234",
  "text": "# Metasploit Module: windows/http/xyz_rce\n# Description: Exploits buffer overflow in XYZ HTTP server...",
  "metadata": {
    "exploit_type": "remote",
    "platform": "windows",
    "module_path": "modules/exploits/windows/http/xyz_rce.rb",
    "cve_references": ["CVE-2024-12345"],
    "source_document_id": "metasploit-doc-1234",
    "provenance": {
      "repo": "github.com/MITRE-Cyber-Security-CVE-Database/metasploit-framework",
      "path": "modules/exploits/windows/http/xyz_rce.rb",
      "digest": "sha256:def456..."
    },
    "quality_score": 0.88,
    "tags": ["exploit", "metasploit", "windows", "http"]
  },
  "created_at": "2026-04-27T10:05:00Z"
}
```

## Common Tasks

### Task: Ingest MITRE CVE Database
```bash
# 1. Clone repository
cd /tmp
git clone https://github.com/MITRE-Cyber-Security-CVE-Database/mitre-cve-database.git

# 2. Inspect data structure
ls -la mitre-cve-database/
find mitre-cve-database -name "*.json" | head -10

# 3. Ingest CVE records
peachtree ingest \
    --repo /tmp/mitre-cve-database \
    --pattern "**/*.json" \
    --output /tmp/peachtree/data/raw/cve-records.jsonl \
    --metadata '{"source": "mitre-cve", "ingestion_date": "2026-04-27"}'

# 4. Validate ingestion
wc -l /tmp/peachtree/data/raw/cve-records.jsonl
head -1 /tmp/peachtree/data/raw/cve-records.jsonl | jq .
```

### Task: Build Security Training Dataset
```bash
# 1. Create security policy pack (if not exists)
cat > policies/security-dataset.yaml << 'EOF'
name: "security-dataset"
version: "1.0"
# ... (see policy pack above)
EOF

# 2. Build dataset
peachtree build \
    --input data/raw/cve-records.jsonl \
    --policy policies/security-dataset.yaml \
    --output data/datasets/security-training.jsonl

# 3. Audit dataset
peachtree audit \
    --input data/datasets/security-training.jsonl \
    --output reports/security-audit.json \
    --detailed

# 4. Check quality metrics
python -c "from peachtree.quality import calculate_quality_score; print(f'Quality: {calculate_quality_score(\"data/datasets/security-training.jsonl\")}')"
```

### Task: Prepare Hancock Training Handoff
```bash
# 1. Generate model card
peachtree card \
    --dataset data/datasets/security-training.jsonl \
    --output reports/hancock-security-model-card.md \
    --model-name "Hancock Cybersecurity LLM" \
    --intended-use "Security advisory generation and vulnerability analysis"

# 2. Create trainer handoff manifest
peachtree handoff \
    --dataset data/datasets/security-training.jsonl \
    --output data/manifests/hancock-handoff.json \
    --training-config configs/hancock-training.yaml

# 3. Package release bundle
peachtree export \
    --input data/datasets/security-training.jsonl \
    --output releases/hancock-security-v1.0/ \
    --format bundle \
    --include-sbom \
    --sign
```

## Troubleshooting

### Issue: GPL License Detected
```bash
# Check which records have GPL license
peachtree audit --input data.jsonl --filter license | grep GPL

# Option 1: Exclude GPL-licensed data
peachtree build \
    --input data/raw/all-sources.jsonl \
    --exclude-license GPL-2.0,GPL-3.0 \
    --output data/datasets/clean.jsonl

# Option 2: Obtain commercial licensing
# Contact repository owners for commercial use agreement
```

### Issue: Live Exploit Code Detected
```bash
# Filter out potentially weaponizable exploit code
peachtree build \
    --input data/raw/exploits.jsonl \
    --filter-exploit-code \
    --documentation-only \
    --output data/datasets/safe-exploits.jsonl

# Or manually review and redact
python scripts/redact_exploit_code.py data/raw/exploits.jsonl
```

### Issue: Sensitive Credentials in CVE Reports
```bash
# Run strict secret filtering
peachtree build \
    --input data/raw/cve-records.jsonl \
    --strict-secrets \
    --redact-credentials \
    --output data/datasets/redacted-cves.jsonl

# Audit for remaining secrets
peachtree audit --input data/datasets/redacted-cves.jsonl --check secrets
```

## Best Practices

1. **Always run ethical use review** for security datasets
2. **Document intended defensive use** in model card
3. **Obtain legal approval** before training on exploit data
4. **Filter live exploit code** - keep documentation only
5. **Track CVE IDs** in provenance metadata
6. **Verify export compliance** if deploying internationally
7. **Include security disclaimers** in model cards
8. **Restrict dataset access** to authorized personnel
9. **Monitor for dataset misuse** post-deployment
10. **Update CVE data regularly** - new vulnerabilities daily

## Output Format
When assisting with security dataset integration:
1. **Data Source**: Which repository/database
2. **License Status**: Verified license for commercial use
3. **Ethical Review**: Intended use case documented
4. **Safety Gates**: Secret filtering, exploit code filtering applied
5. **Provenance**: Full source tracking maintained
6. **Next Steps**: Build, audit, or handoff workflow

## Related Repositories
- MITRE CVE Database: `mitre-cve-database`
- Metasploit Framework: `metasploit-framework`
- ClamAV: `clamav`
- Cobalt Strike Kit: `cobalt-strike-community_kit`
- Grok Prompts: `grok-promptss` (security prompt engineering)

## See Also
- Hancock integration: `docs/integrations/hancock.md`
- Security policy packs: `policies/security-dataset.yaml`
- Ethical use guidelines: `docs/ethics/security-datasets.md`
- Export control compliance: `docs/compliance/export-control.md`
