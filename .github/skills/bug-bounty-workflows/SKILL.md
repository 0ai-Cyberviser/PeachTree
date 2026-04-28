---
name: bug-bounty-workflows
description: "Use when: researching vulnerabilities for bug bounty programs, documenting security findings for HackerOne/Bugcrowd, creating ethical hacking training datasets, building vulnerability disclosure workflows, or generating security research documentation. Provides responsible disclosure patterns, PoC templates, and dataset safety controls."
---

# Bug Bounty Workflow Skill

## Purpose
Automate bug bounty vulnerability research workflows, responsible disclosure documentation, and ethical hacking dataset creation with built-in safety controls.

## When to Use This Skill
- Researching security vulnerabilities for bug bounty programs
- Documenting findings for HackerOne, Bugcrowd, or other platforms
- Creating training datasets from disclosed vulnerabilities
- Building ethical hacking instruction data for security LLMs
- Managing vulnerability disclosure timelines
- Generating PoC documentation with proper safety restrictions

## Supported Bug Bounty Platforms

### 1. HackerOne
- Crypto.com (rewards: $10-$2M)
- Coinbase, GitHub, GitLab, Shopify
- Average response: 11 hours (Crypto.com)
- Fast payment guarantee: 1 month

### 2. Bugcrowd
- Tesla, OpenAI, Mastercard
- Vulnerability Disclosure Program (VDP) support

### 3. Synack
- Private bug bounty marketplace
- Pre-vetted researchers

### 4. YesWeHack
- European bug bounty platform

## Core Workflows

### Workflow 1: Program Research & Scoping

**Input**: Bug bounty program URL or policy document

**Steps**:
1. Extract scope (in-scope assets, out-of-scope exclusions)
2. Identify safe harbor provisions
3. Document reward ranges by severity
4. Create research authorization checklist
5. Generate research plan

**Output**: Research plan with clear boundaries

**Example**:
```bash
# Parse Crypto.com bug bounty program
cat > research-plan.md <<EOF
# Crypto.com Bug Bounty Research

## Program Details
- Platform: HackerOne
- Rewards: $10 (Low) to $2M (Extreme)
- Response: 11h avg first response
- Safe Harbor: Gold Standard compliance

## In-Scope Assets
- app.mona.co (Critical: $200-$2M)
- crypto.com/exchange (Critical: $200-$2M)
- web.crypto.com (Critical: $200-$2M)
- Mobile app APIs (Critical)
- com.monaco.mobile (High: $50-$40K)

## Out-of-Scope
- Publicly available credentials
- Internally known issues
- Social engineering
- DDoS attacks

## Testing Authorization
✅ Bug bounty program participation authorized
✅ Safe harbor: Gold Standard (legal protection)
✅ Testing approach: Authenticated, black-box
❌ NO unauthorized access
❌ NO data exfiltration
❌ NO service disruption
EOF
```

### Workflow 2: Vulnerability Documentation

**Input**: Security finding details

**Steps**:
1. Classify vulnerability type (OWASP Top 10, CWE)
2. Calculate CVSS 3.1 score
3. Create reproduction steps (sanitized)
4. Assess business impact
5. Recommend remediation
6. Generate report template

**Output**: Structured vulnerability report

**Template**:
```markdown
# [VULN-001] Insecure Direct Object Reference in User API

## Severity
**CVSS 3.1**: 8.1 (High)  
**Vector**: CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N  
**Program Impact**: Critical ($5,000-$40,000)

## Vulnerability Type
- OWASP A01:2021 - Broken Access Control
- CWE-639: Authorization Bypass Through User-Controlled Key

## Description
The `/api/users/{id}` endpoint returns user profile data without verifying the authenticated user has permission to access user `{id}`. An attacker can enumerate user IDs and access arbitrary user profiles.

## Reproduction Steps
1. Authenticate as user A (user_id: 12345)
2. Request: `GET /api/users/67890` (user B's ID)
3. Observe: Full user B profile returned without authorization check
4. Repeat for any user ID

## Proof of Concept
[SANITIZED - NO LIVE EXPLOITATION]

Request:
```http
GET /api/users/67890 HTTP/1.1
Host: api.crypto.com
Authorization: Bearer [USER_A_TOKEN]
```

Response:
```json
{
  "user_id": 67890,
  "email": "victim@example.com",
  "full_name": "Victim User",
  "account_balance": "$50,000",
  "kyc_status": "verified"
}
```

## Impact
**Business Impact**: High

- Unauthorized access to sensitive user data (PII, financial info)
- Account enumeration enables targeted attacks
- Regulatory compliance violation (GDPR, KYC data exposure)
- Potential for account takeover via combined attack vectors

**Affected Users**: All registered users (~100M+)

## Remediation
1. **Immediate**: Implement authorization check in `/api/users/{id}` endpoint
2. **Code Fix**:
```python
def get_user(user_id, authenticated_user_id):
    if user_id != authenticated_user_id:
        raise AuthorizationError("Cannot access other users' data")
    return db.get_user(user_id)
```
3. **Long-term**: Audit all API endpoints for missing authorization checks

## Authorization
- Tested under: Crypto.com HackerOne Bug Bounty Program
- Safe Harbor: Gold Standard compliance
- Date: 2026-04-27
- Researcher: [Name]
```

### Workflow 3: Responsible Disclosure Submission

**Input**: Completed vulnerability report

**Steps**:
1. Pre-submission checklist validation
2. Sanitize sensitive data (remove live exploit code)
3. Format for target platform (HackerOne, Bugcrowd)
4. Submit via official channel
5. Track disclosure timeline
6. Monitor for triaging and bounty

**Output**: Submitted report + tracking metadata

**Pre-Submission Checklist**:
```markdown
# Disclosure Checklist: VULN-001

## Verification
- [x] Finding is in-scope (verified against program policy)
- [x] Not a duplicate (searched existing reports)
- [x] Not an internally known issue
- [x] Severity correctly assessed (CVSS 3.1)

## Content Quality
- [x] Clear reproduction steps provided
- [x] Business impact explained
- [x] Remediation suggestions included
- [x] Screenshots/evidence attached

## Safety
- [x] All sensitive data sanitized
- [x] No live exploit code included
- [x] Testing was authorized
- [x] No service disruption caused
- [x] No data exfiltration performed

## Disclosure
- [x] Ready to submit via HackerOne
- [ ] Will NOT publicly disclose until authorized
- [ ] Will cooperate with security team
- [ ] Will follow responsible disclosure timeline

## Expected Timeline
- Day 0: Submit to HackerOne
- Day 1-7: Initial triage (11h avg for Crypto.com)
- Day 7-30: Validation and fix development
- Day 30-90: Bounty payment (Crypto.com guarantees 1 month)
- Day 90+: Potential public disclosure (WITH PERMISSION)
```

### Workflow 4: Dataset Creation (Post-Disclosure)

**Input**: Publicly disclosed vulnerability reports

**Steps**:
1. Verify vulnerability is publicly disclosed/patched
2. Extract educational content
3. Remove weaponizable exploit code
4. Create instruction-tuning records
5. Apply PeachTree safety gates
6. Add ethical use metadata
7. Build JSONL dataset

**Output**: Training dataset with safety controls

**Safety Requirements**:
- ONLY publicly disclosed vulnerabilities (90+ days post-fix OR officially disclosed)
- NO live exploit code (documentation only)
- COMPLETE provenance (CVE ID, disclosure date, source)
- ETHICAL USE metadata enforced

**Example**:
```bash
# Step 1: Collect disclosed reports
mkdir -p /tmp/disclosed-vulns/2026

# Download public reports from HackerOne disclosed reports
# https://hackerone.com/hacktivity (filter: Disclosed)

# Step 2: Ingest into PeachTree
peachtree ingest \
  --repo /tmp/disclosed-vulns \
  --pattern "**/*.md,**/*.json" \
  --output data/raw/bug-bounty-disclosed.jsonl \
  --metadata '{
    "source": "hackerone-disclosed",
    "type": "responsible-disclosure",
    "ethical_use": "defensive-only",
    "authorization": "publicly-disclosed"
  }'

# Step 3: Build dataset with safety policy
peachtree build \
  --input data/raw/bug-bounty-disclosed.jsonl \
  --policy config/policy-packs/bug-bounty-ethical-use.yaml \
  --output data/datasets/bug-bounty-training.jsonl

# Step 4: Audit for safety compliance
peachtree audit \
  --dataset data/datasets/bug-bounty-training.jsonl \
  --output reports/bug-bounty-audit.json \
  --detailed

# Step 5: Verify safety gates passed
jq '.safety_gate_results' reports/bug-bounty-audit.json

# Step 6: Export for security LLM training
peachtree export \
  --source data/datasets/bug-bounty-training.jsonl \
  --output data/manifests/security-llm-chatml.jsonl \
  --format chatml \
  --system-prompt "You are an ethical security researcher focused on vulnerability discovery and responsible disclosure."

# Step 7: Generate model card
peachtree card \
  --dataset data/datasets/bug-bounty-training.jsonl \
  --output MODEL-CARD-BUG-BOUNTY.md \
  --template security-research
```

### Workflow 5: Vulnerability Knowledge Base

**Input**: Categorized vulnerability collection

**Steps**:
1. Categorize by vulnerability type (OWASP, CWE)
2. Extract common patterns and testing techniques
3. Create instruction-tuning pairs
4. Document defensive mitigations
5. Build searchable knowledge base

**Output**: Structured security knowledge base

**Example**:
```bash
# Create knowledge base structure
mkdir -p knowledge-base/{access-control,injection,crypto,auth,misc}

# Create instruction-tuning pairs by category
cat > knowledge-base/access-control/idor-detection.jsonl <<'EOF'
{"instruction": "How do you test for IDOR vulnerabilities in APIs?", "output": "1. Identify object references (user IDs, account IDs, file IDs) in API endpoints. 2. Authenticate as User A and note your object IDs. 3. Create User B account and note their object IDs. 4. As User A, attempt to access User B's objects by modifying IDs in requests. 5. Check if authorization is enforced. 6. Test different HTTP methods (GET, PUT, DELETE). Example: /api/users/{id} → try accessing other user IDs. If successful without authorization check, IDOR exists.", "metadata": {"vulnerability_type": "IDOR", "owasp": "A01:2021", "cwe": "CWE-639", "severity": "high", "ethical_use": true}}
{"instruction": "What is the difference between IDOR and horizontal privilege escalation?", "output": "IDOR (Insecure Direct Object Reference) is the technical vulnerability where object references are exposed without authorization checks. Horizontal privilege escalation is the security impact where one user accesses another user's resources at the same privilege level. IDOR often enables horizontal privilege escalation. Example: User A (customer) accessing User B's (customer) invoice via /invoices/456 is both IDOR (technical flaw) and horizontal privilege escalation (impact).", "metadata": {"vulnerability_type": "access-control", "owasp": "A01:2021", "cwe": "CWE-639", "ethical_use": true}}
EOF

cat > knowledge-base/injection/sql-injection-detection.jsonl <<'EOF'
{"instruction": "What are the common SQL injection detection techniques?", "output": "1. **Error-based**: Inject SQL syntax errors (e.g., ' or 1=1--) and check for database error messages. 2. **Boolean-based blind**: Inject conditions that change response (e.g., ' AND 1=1-- vs ' AND 1=2--). 3. **Time-based blind**: Inject delays (e.g., '; WAITFOR DELAY '00:00:05'--) and measure response time. 4. **Union-based**: Use UNION to extract data (e.g., ' UNION SELECT username, password FROM users--). 5. **Out-of-band**: Trigger DNS/HTTP requests to external server. Always test on authorized targets only.", "metadata": {"vulnerability_type": "SQLi", "owasp": "A03:2021", "cwe": "CWE-89", "severity": "critical", "ethical_use": true, "authorization_required": true}}
EOF

# Build knowledge base dataset
peachtree build \
  --input knowledge-base/**/*.jsonl \
  --policy config/policy-packs/educational-security-data.yaml \
  --output data/datasets/security-knowledge-base.jsonl

# Verify quality
peachtree quality \
  --input data/datasets/security-knowledge-base.jsonl \
  --output reports/knowledge-base-quality.json
```

## Policy Packs

### Bug Bounty Ethical Use Policy

**File**: `config/policy-packs/bug-bounty-ethical-use.yaml`

```yaml
name: "bug-bounty-ethical-use"
version: "1.0"
description: "Ethical use policy for bug bounty and vulnerability research datasets"

gates:
  # Critical: Secret filtering
  - name: "secret-filter"
    required: true
    config:
      strict: true
      patterns:
        - "API_KEY"
        - "ACCESS_TOKEN"
        - "SESSION_ID"
        - "CSRF_TOKEN"
        - "password\\s*="
        - "credential"
        - "private.*key"

  # Critical: Weaponization prevention
  - name: "weaponization-filter"
    required: true
    config:
      block_patterns:
        - "\\$\\(.*exec.*\\)"  # Command execution
        - "eval\\(.*\\)"        # Code evaluation
        - "system\\(.*\\)"      # System calls
        - "shell_exec"
        - "reverse.*shell"
        - "meterpreter"
        - "payload.*execution"
      allow_documentation: true  # Descriptions OK, code NOT OK
      require_sanitization: true

  # Critical: Responsible disclosure check
  - name: "responsible-disclosure-check"
    required: true
    config:
      require_disclosure_date: true
      require_cve_or_report_id: true
      block_zero_day: true  # No undisclosed vulnerabilities
      minimum_disclosure_age_days: 90  # Must be 90+ days since patch

  # Critical: Ethical use metadata
  - name: "ethical-use-metadata"
    required: true
    config:
      require_fields:
        - "ethical_use_only"
        - "defensive_security"
        - "no_offensive_use"
        - "authorization_status"
        - "disclosure_status"

  # License and provenance
  - name: "provenance-tracker"
    required: true
    config:
      require_source_repo: true
      require_source_path: true
      require_digest: true
      require_disclosure_date: true

  # Quality scoring
  - name: "quality-scorer"
    required: true
    config:
      minimum_score: 0.80  # Higher standard
      scoring_criteria:
        - technical_accuracy
        - reproduction_clarity
        - impact_assessment
        - remediation_quality

compliance:
  legal_review: true
  security_review: true
  ethics_review: true
  responsible_disclosure: true
  authorization_verified: true

thresholds:
  quality_score: 0.80
  duplicate_rate: 0.0  # No duplicates

security_metadata:
  authorized_programs_only: true
  defensive_use_only: true
  educational_purpose: true
  no_weaponization: true
  public_disclosure_required: true
```

## CVSS 3.1 Scoring Reference

### Base Metrics

**Attack Vector (AV)**:
- Network (N): 0.85
- Adjacent (A): 0.62
- Local (L): 0.55
- Physical (P): 0.20

**Attack Complexity (AC)**:
- Low (L): 0.77
- High (H): 0.44

**Privileges Required (PR)**:
- None (N): 0.85
- Low (L): 0.62 (0.68 if Scope Changed)
- High (H): 0.27 (0.50 if Scope Changed)

**User Interaction (UI)**:
- None (N): 0.85
- Required (R): 0.62

**Scope (S)**:
- Unchanged (U)
- Changed (C)

**Confidentiality/Integrity/Availability (C/I/A)**:
- None (N): 0.0
- Low (L): 0.22
- High (H): 0.56

### Severity Ranges

- **Critical**: 9.0-10.0
- **High**: 7.0-8.9
- **Medium**: 4.0-6.9
- **Low**: 0.1-3.9
- **None**: 0.0

### Example Calculations

**IDOR in User API**:
```
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N
Score: 8.1 (High)

Explanation:
- AV:N (Network) - exploitable remotely
- AC:L (Low) - no special conditions
- PR:L (Low) - requires authentication
- UI:N (None) - no user interaction
- S:U (Unchanged) - doesn't affect other components
- C:H (High) - full user data disclosure
- I:H (High) - can modify other users' data
- A:N (None) - no availability impact
```

## Common Vulnerability Patterns

### 1. Broken Access Control (OWASP A01)
- IDOR
- Missing function-level access control
- Path traversal
- Privilege escalation

### 2. Cryptographic Failures (OWASP A02)
- Weak encryption algorithms
- Hard-coded secrets
- Insecure random number generation
- Missing encryption in transit

### 3. Injection (OWASP A03)
- SQL injection
- XSS (Reflected, Stored, DOM)
- Command injection
- LDAP injection

### 4. Authentication Failures (OWASP A07)
- Weak password policy
- Session fixation
- Missing MFA
- Credential stuffing

### 5. SSRF (OWASP A10)
- Server-Side Request Forgery
- Open redirects
- Internal service access

## Automation Scripts

### Generate Vulnerability Report

```bash
#!/bin/bash
# generate-vuln-report.sh

VULN_ID=$1
TITLE=$2
CVSS=$3

cat > reports/${VULN_ID}.md <<EOF
# [${VULN_ID}] ${TITLE}

## Severity
**CVSS 3.1**: ${CVSS}

## Description
[TODO: Add description]

## Reproduction Steps
1. [TODO: Step 1]
2. [TODO: Step 2]

## Impact
[TODO: Business impact]

## Remediation
[TODO: Suggested fix]

## Authorization
- Program: [TODO]
- Date: $(date -I)
- Safe Harbor: [TODO]
EOF

echo "✅ Report template created: reports/${VULN_ID}.md"
```

### Build Bug Bounty Dataset

```bash
#!/bin/bash
# build-bug-bounty-dataset.sh

set -e

echo "🔍 Building bug bounty training dataset..."

# Ingest disclosed reports
peachtree ingest \
  --repo /tmp/disclosed-vulns \
  --pattern "**/*.md,**/*.json" \
  --output data/raw/bug-bounty-disclosed.jsonl

# Build with safety policy
peachtree build \
  --input data/raw/bug-bounty-disclosed.jsonl \
  --policy config/policy-packs/bug-bounty-ethical-use.yaml \
  --output data/datasets/bug-bounty-training.jsonl

# Audit
peachtree audit \
  --dataset data/datasets/bug-bounty-training.jsonl \
  --output reports/bug-bounty-audit.json

# Check safety gates
if jq -e '.safety_gate_results | all' reports/bug-bounty-audit.json; then
  echo "✅ All safety gates passed"
else
  echo "❌ Safety gates failed"
  exit 1
fi

# Export for training
peachtree export \
  --source data/datasets/bug-bounty-training.jsonl \
  --output data/manifests/security-llm-chatml.jsonl \
  --format chatml

echo "✅ Dataset build complete!"
echo "Records: $(wc -l < data/datasets/bug-bounty-training.jsonl)"
```

## Decision Framework: Include in Dataset?

```
Is vulnerability publicly disclosed? ───NO──> ❌ STOP - Do not include
  │
 YES (90+ days OR officially disclosed)
  │
Contains live exploit code? ────────────YES──> ⚠️ SANITIZE - Remove code, keep description
  │
 NO
  │
Was testing authorized? ────────────────NO──> ❌ STOP - Do not include
  │
 YES (bug bounty program or permission)
  │
Has educational value? ─────────────────NO──> ⚠️ RECONSIDER - Low priority
  │
 YES
  │
Can be used defensively? ───────────────NO──> ⚠️ ADD RESTRICTIONS - Limit use case
  │
 YES
  │
Passes all safety gates? ───────────────NO──> ❌ STOP - Fix issues first
  │
 YES
  │
✅ INCLUDE with provenance & ethical use metadata
```

## Related Resources

- [BugBountyAgent](.github/agents/BugBountyAgent.agent.md)
- [Security Dataset Integration](../.github/skills/security-dataset-integration/SKILL.md)
- [Frozen Dataclass Patterns](../.github/skills/frozen-dataclass-patterns/SKILL.md)
- [JSONL Operations](../.github/skills/jsonl-operations/SKILL.md)
- [HackerOne Disclosure Guidelines](https://www.hackerone.com/disclosure-guidelines)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CVSS 3.1 Calculator](https://www.first.org/cvss/calculator/3.1)

## Ethical Reminders

1. **NEVER bypass responsible disclosure**
2. **ALWAYS verify authorization before testing**
3. **NEVER include live exploit code in datasets**
4. **ALWAYS apply safety gates and metadata**
5. **NEVER publicly disclose without permission**
6. **ONLY use disclosed vulnerabilities for training**
7. **ALWAYS prioritize defensive security education**

---

**Vulnerability research is about making systems safer, not exploiting them.**
