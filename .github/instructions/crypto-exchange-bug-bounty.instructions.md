---
applyTo:
  - "**/bug-bounty/**/*.md"
  - "**/vulnerability-reports/**/*.md"
  - "**/security-research/**/*.md"
  - "**/*crypto-exchange*/**"
  - "**/*web3*/**"
description: "Guidance for cryptocurrency exchange bug bounty research and Web3 vulnerability documentation. Use when working with crypto exchange security reports, wallet vulnerabilities, or blockchain-specific security issues. Applies to HackerOne/Bugcrowd submissions for exchanges like Crypto.com, OKX, Coinbase, Binance."
---

# Cryptocurrency Exchange Bug Bounty Research

## Platform-Specific Guidance

### Multi-Platform Vulnerability Assessment

When researching cryptocurrency exchange vulnerabilities, assess across **4 platform types**:

#### 1. Web2 (Traditional Web)
**Focus**: Web applications (exchange platforms, trading dashboards)

**Critical Vulnerabilities**:
- Remote Code Execution (RCE) on servers
- SQL Injection affecting core production database
- Admin backend takeover
- Mass account takeover (>50% of users)
- System command execution

**High Vulnerabilities**:
- Stored XSS worms (self-replicating)
- CSRF leading to account compromise or fund transfers
- Account access at scale
- SQL Injection (limited data extraction)
- Source code leakage
- SSRF with internal service access

**Testing Approach**:
```bash
# Authenticated testing (with permission)
# 1. Create test account
# 2. Identify critical endpoints (withdrawal, transfer, trading)
# 3. Test authorization on fund-related actions
# 4. Check for IDOR in user/account APIs
# 5. Verify CSRF protection on state-changing operations
```

#### 2. Web3 (Wallet & Blockchain)
**Focus**: Crypto wallets, smart contracts, blockchain infrastructure

**Critical Vulnerabilities**:
- Remote exploits on validators/contracts
- Fund theft or mass data exfiltration
- Complete authentication bypass
- Admin takeover affecting majority of users

**High Vulnerabilities**:
- Unauthorized access to user funds (limited scope)
- Account takeover requiring specific user interaction
- Smart contract exploits with financial impact

**Medium Vulnerabilities**:
- Wallet address manipulation (front-end display only)
- Replay of signed messages (complex setup required)
- Incorrect chainID/nonce/gas calculations
- DApp permission misuse requiring user acceptance

**Testing Approach**:
```bash
# Web3 wallet testing
# 1. Test signature request flows
# 2. Verify transaction display vs actual payload
# 3. Check for replay attack protections
# 4. Test permission scoping (DApp approvals)
# 5. Validate chainID enforcement
```

#### 3. Mobile (iOS/Android)
**Focus**: Official mobile apps

**Critical Vulnerabilities**:
- Remote app compromise or code execution
- Mass data breach through app flaws
- SQL/NoSQL injection via mobile APIs
- Admin privilege takeover via mobile vectors

**High Vulnerabilities**:
- CSRF on critical actions (account takeover, fund transfers)
- SSRF accessing internal systems
- Sensitive data exposure (keys, credentials)
- Logic flaws affecting fund balances
- Unauthorized transaction operations

**Cross-Platform Rule**: Report **once per vulnerability type** across iOS/Android

**Testing Approach**:
```bash
# Mobile security testing
# 1. Inspect app traffic (proxy through Burp/mitmproxy)
# 2. Analyze local storage (SQLite, SharedPreferences, Keychain)
# 3. Test exported components (Android activities, iOS URL schemes)
# 4. Check for hardcoded secrets in binaries
# 5. Verify certificate pinning on non-rooted devices
```

#### 4. Desktop (Windows/MacOS)
**Focus**: Desktop clients and executables

**Critical Vulnerabilities**:
- Remote code execution on client or server
- Admin privilege takeover via client exploit
- System command execution

**High Vulnerabilities**:
- CSRF (account takeover or fund transfers)
- SSRF from app to internal services
- Sensitive data exposure (encrypted seeds, local credentials)
- Transaction disruption bugs
- Logic flaws affecting fund operations

**Testing Approach**:
```bash
# Desktop client testing
# 1. Analyze binary for hardcoded secrets
# 2. Test local storage security
# 3. Inspect network traffic
# 4. Test deep link/URI handlers
# 5. Check update mechanism security
```

## Severity Classification

### Extreme Tier ($30K-$1M+)
**Criteria** (at OKG discretion):
- Rapid unauthorized loss of funds >$1M
- Zero-interaction compromise of wallets/admin systems
- Massive KYC/PII breach with regulatory impact
- Systemic risk to platform availability or market stability

**Example Scenarios**:
- Exploit drains multiple wallets without user interaction
- Bypass fund protections leading to mass theft
- Exposure of customer financial data at scale
- Mass account takeover via authentication flaw

### Business Risk Scoring

**Web2 Multipliers**:
```
Static pages: 1.0×
Login/register flows: 1.1×
Authenticated dashboard: 1.2×
Pages with PII/order history: 1.3×
Session compromise: 1.3×
Fund action pages (withdrawal, trading): 1.4×
Admin panel: 1.5×
```

**Web3 Multipliers**:
```
Wallet connect (no impact): 1.0×
dApp UI issues: 1.1×
Balance/history leak: 1.2×
Spoofed signature prompts: 1.3×
Smart contract dashboards: 1.4×
XSS with signature hijack: 1.5×
```

**Mobile Multipliers**:
```
UI bugs, clipboard access: 1.0×
Non-sensitive info exposure: 1.1×
General account data: 1.2×
Sensitive data in logs/memory: 1.3×
WebView auth/transaction issues: 1.4×
Fund transfer or key exposure: 1.5×
```

**Desktop Multipliers**:
```
UI bugs, crash logs: 1.0×
Auth interface: 1.1×
Sensitive data exposure: 1.2×
Full compromise: 1.3×
```

### Quality & Context Modifiers

**Exploit Reliability**: 0.5-1.0×
- Consistently reproducible? Higher payout
- Device-specific or unstable? Lower payout

**User Interaction**: 0.5-1.0×
- No interaction needed? Higher payout
- Multiple clicks/context switches? Lower payout

**Exposure**: 0.3-1.0×
- Affects most users? Higher payout
- Narrow edge case? Lower payout

**Mitigation Proximity**: 0.5-1.0×
- Existing controls limit risk? Lower payout

## Common Vulnerability Patterns

### 1. IDOR (Insecure Direct Object Reference)
**Requirement**: Must demonstrate **ID discovery path**, not just brute force

**Example**:
```http
GET /api/users/{user_id}/balance
Authorization: Bearer USER_A_TOKEN

# ❌ NOT ACCEPTED: Tried random IDs 1-1000000
# ✅ ACCEPTED: Found user ID via /api/friends endpoint, then accessed
```

**Testing**:
1. Identify object references (user IDs, account IDs, order IDs)
2. Find legitimate discovery method (API response, public profile, etc.)
3. Test authorization across different users
4. Document the discovery path clearly

### 2. CSRF on Fund Transfers
**Critical**: State-changing operations affecting funds

**Test**:
```html
<!-- PoC for CSRF on withdrawal -->
<form action="https://exchange.example.com/api/withdraw" method="POST">
  <input name="amount" value="1000">
  <input name="address" value="attacker_wallet">
  <input name="currency" value="BTC">
</form>
<script>document.forms[0].submit()</script>
```

**Verify**:
- No CSRF token validation
- Cookie-based auth without SameSite protection
- State change occurs on GET request

### 3. Signature Hijack (Web3)
**High Impact**: XSS leading to wallet signature manipulation

**Scenario**:
```javascript
// Stored XSS in username field
<script>
window.ethereum.request({
  method: 'eth_sendTransaction',
  params: [{
    from: window.ethereum.selectedAddress,
    to: 'attacker_address',
    value: '0x1000000000000000' // 0.1 ETH
  }]
});
</script>
```

**Impact**: User unknowingly signs transaction to attacker

### 4. SQL Injection via Mobile API
**Critical**: Mobile app API endpoint vulnerable to SQLi

**Example**:
```http
POST /api/v1/search HTTP/1.1
Host: api.exchange.com
Authorization: Bearer TOKEN

{"query": "' OR 1=1--", "type": "user"}
```

**Verify**:
- Extract database structure
- Demonstrate data exfiltration
- Show impact (user data, financial records)

### 5. Local Storage Leaks (Mobile)
**Medium/High**: Sensitive data in app storage

**Check**:
```bash
# Android
adb shell
run-as com.exchange.app
cat shared_prefs/user_data.xml

# iOS (jailbroken for testing only)
plutil -p /var/mobile/Containers/Data/Application/<UUID>/Library/Preferences/com.exchange.app.plist
```

**Look For**:
- Session tokens
- API keys
- Encrypted seeds (even encrypted = finding if predictable)
- Private keys

## Reporting Requirements

### Mandatory Elements

1. **Clear Reproduction Steps** (numbered, specific)
2. **Video PoC** (required if requested by program)
3. **Business Impact** (not just technical description)
4. **CVSS Score** (for programs using CVSS 3.1)
5. **Platform Specification** (Web2/Web3/Mobile/Desktop)

### Cross-Platform Reporting

**Rule**: Report **once** per vulnerability, even if it affects multiple platforms

**Example**:
```
Vulnerability: Insufficient session timeout
Affects: iOS app, Android app, Web platform
Report: 1 submission documenting all platforms
```

### AI Usage Disclosure

**Required**: Disclose any AI tool usage in:
- Vulnerability discovery
- Testing automation
- Report writing

**Example**:
```markdown
## AI Tool Usage
- ChatGPT: Used to draft initial report structure
- GitHub Copilot: Assisted with PoC code generation
- Human verification: All findings manually validated and reproduced
```

**Not Acceptable**:
- Auto-generated reports without human validation
- Templated submissions without contextual analysis
- Unverified AI-discovered vulnerabilities

## Out of Scope (Common Rejections)

### Always Out of Scope
- ❌ Automated scanner reports (Burp, Acunetix, etc.)
- ❌ Self-XSS (requires victim to paste malicious code)
- ❌ Known vulnerable libraries **without working PoC**
- ❌ DoS/DDoS attacks
- ❌ Attacks requiring root/jailbreak
- ❌ Physical access to user's device
- ❌ Social engineering
- ❌ Rate limiting on non-auth endpoints

### Crypto-Specific Out of Scope
- ❌ Address bar spoofing in in-app browsers (WebView)
- ❌ Binary analysis without PoC affecting business logic
- ❌ Lack of obfuscation or jailbreak detection
- ❌ Certificate pinning bypass on rooted devices
- ❌ Hardcoded API keys **without demonstrated impact**
- ❌ Sensitive data in private app directory (expected behavior)
- ❌ Clients not downloaded from official sources

### Edge Cases (Case-by-Case)
- ⚠️ Compliance-related reports
- ⚠️ Public 0-days with patches <1 month old
- ⚠️ Third-party component vulnerabilities (context-dependent)

## Testing Checklist

### Pre-Testing
- [ ] Verify authorization (bug bounty program participation)
- [ ] Read safe harbor terms
- [ ] Check in-scope vs out-of-scope assets
- [ ] Set up test accounts (do not use real funds)
- [ ] Configure proxy (Burp Suite, mitmproxy)
- [ ] Limit requests to 5/second (common rate limit)

### During Testing
- [ ] Document all steps with timestamps
- [ ] Take screenshots/screen recordings
- [ ] Save request/response examples
- [ ] Note any unusual behavior immediately
- [ ] Stop if you access production user data

### Pre-Submission
- [ ] Verify not a duplicate (search HackerOne)
- [ ] Verify not internally known
- [ ] Calculate CVSS score (if required)
- [ ] Sanitize all sensitive data
- [ ] Remove live exploit code
- [ ] Prepare video PoC (if complex)
- [ ] Write clear business impact statement

## Response Timeline Expectations

### Fast Programs
**Crypto.com**:
- First response: 11 hours avg
- Triage: 13 hours avg
- Bounty: 6 days avg
- Payment guarantee: 1 month

**OKX**:
- First response: 5 hours avg
- Bounty: 5 days, 14 hours avg

### Standard Programs
- Initial triage: 1-7 days
- Validation: 7-30 days
- Bounty: 30-90 days
- Public disclosure: 90+ days post-fix

## Dataset Creation (Post-Disclosure)

### Requirements
- ✅ Vulnerability publicly disclosed OR 90+ days post-fix
- ✅ Sanitized (no live exploit code)
- ✅ Complete provenance (CVE/report ID, disclosure date)
- ✅ Ethical use metadata

### Example Workflow
```bash
# Create vulnerability report
cat > reports/okx-idor-withdrawal-2026.md <<'EOF'
# OKX IDOR on Withdrawal Endpoint (Disclosed)

**Program**: OKX HackerOne
**Disclosed**: 2026-01-15
**Bounty**: $15,000 (High)
**CVSS**: 8.1

## Vulnerability
IDOR on /api/v1/withdrawals/{id} allowed authenticated users to view/modify other users' pending withdrawals...

## Discovery Path
1. Initiated withdrawal (ID: 12345)
2. Noticed withdrawal ID in API response
3. Modified ID to 12346 (different user)
4. Successfully retrieved other user's withdrawal details
EOF

# Ingest into PeachTree (after 90+ days)
peachtree ingest \
  --repo /tmp/disclosed-crypto-vulns \
  --pattern "**/*.md" \
  --output data/raw/crypto-exchange-vulns.jsonl

# Build with bug bounty policy
peachtree build \
  --input data/raw/crypto-exchange-vulns.jsonl \
  --policy config/policy-packs/bug-bounty-ethical-use.yaml \
  --output data/datasets/crypto-security-training.jsonl
```

## Quick Reference

**Severity**: Extreme (>$30K) | Critical ($5-30K) | High ($2-5K) | Medium ($600-2K) | Low ($50-600)

**Platforms**: Web2 (traditional), Web3 (wallet/blockchain), Mobile (iOS/Android), Desktop (Win/Mac)

**Report Once**: Same vuln across platforms = 1 report

**Must Include**: Reproduction steps, video PoC (if requested), business impact, CVSS score

**Out of Scope**: Scanners, self-XSS, known libs, DoS, root/jailbreak, social engineering

**Tools**: BugBountyAgent, bug-bounty-workflows skill, generate-dataset-card prompt

## Related Resources

- [BugBountyAgent](../../.github/agents/BugBountyAgent.agent.md)
- [bug-bounty-workflows skill](../../.github/skills/bug-bounty-workflows/SKILL.md)
- [security-dataset-integration skill](../../.github/skills/security-dataset-integration/SKILL.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CVSS Calculator](https://www.first.org/cvss/calculator/3.1)
- [HackerOne Disclosure Guidelines](https://www.hackerone.com/disclosure-guidelines)
