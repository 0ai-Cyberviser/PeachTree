---
applyTo:
  - "**/bug-bounty/**/*.md"
  - "**/vulnerability-reports/**/*.md"
  - "**/security-research/**/*.md"
  - "**/*crypto-exchange*/**"
  - "**/*web3*/**"
description: "Guidance for cryptocurrency exchange bug bounty research and Web3 vulnerability documentation. Use when working with crypto exchange security reports, wallet vulnerabilities, or blockchain-specific security issues. Applies to HackerOne/Bugcrowd submissions for exchanges like Crypto.com, OKX, Robinhood, Bitstamp, Coinbase, Binance."
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

### Robinhood-Specific Out of Scope
- ❌ Subdomain takeover without actually taking over the subdomain
- ❌ Cache poisoning
- ❌ Email list or notification setting configuration issues
- ❌ Clickjacking without demonstrable impact
- ❌ Disclosure of publicly available information
- ❌ Lack of security flags in cookies (except session cookies)
- ❌ Lack of security headers unless exploitable
- ❌ Out-of-date browsers or browser add-ons
- ❌ Out-of-date Android/iOS versions (no longer maintained)
- ❌ Mobile root/jailbreak detection
- ❌ DNS records (SPF, DKIM, DMARC, DNSSEC)
- ❌ Unsafe SSL/TLS cipher suites unless exploitable
- ❌ Lack of EXIF stripping on uploads (unless publicly accessible)
- ❌ Logout CSRF
- ❌ Say Technologies: Voting info disclosure via IDOR, contact/support forms
- ❌ Third-party integrations: shop.robinhood.com, content.research.robinhood.com, etc.

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

## Robinhood & Bitstamp Program Patterns

### Overview
Robinhood (with acquired Bitstamp) uses a tier-based reward system with CVSSv3 sliding scale bounties.

**Program Type**: HackerOne  
**Response Time**: 7h first response, 1d 21h triage  
**Gold Standard Safe Harbor**: Yes  
**VIP Program**: Available for consistent researchers (3-5+ quality reports)

### Tier System

**Tier 1** (Highest Rewards):
```
Critical: $10,000-$25,000
High: $5,000-$10,000
Medium: $500-$5,000
Low: $100-$500
```

**Assets**:
- `*.robinhood.com`, `*.rhinternal.net`, `*.rhapollo.net`
- `api.robinhood.com`, `nummus.robinhood.com` (crypto trading)
- `oak.robinhood.net` (internal admin - very sensitive)
- iOS apps: 1634080733 (Wallet), 6462308655 (Credit Card), 938003185 (Trading)
- Android apps: com.robinhood.android, com.robinhood.gateway, com.robinhood.money, com.robinhood.global
- `www.bitstamp.net` (main host)

**Tier 2** (Medium Rewards):
```
High: $3,000-$6,000
Medium: $1,000-$3,000
```

**Assets**:
- `*.saytechnologies.com`, `*.say.rocks`

**Tier 3** (Lower Rewards):
```
High: $6,000-$8,000
Medium: $3,000-$6,000
Low: $500-$3,000
Info: $100-$500
```

**Assets**:
- `*.bitstamp.net` (subdomains)
- Bitstamp iOS (Id1406825640), Android (net.bitstamp.app)
- `*.x1.co`, `*.x1creditcard.com`, `*.1integrations.com`
- `fusion.tradepmr.com`, `www.tradepmr.com`, `insight2.tradepmr.com`

### Special Requirements

**Mandatory Headers**:
All requests to Robinhood assets MUST include:
```http
X-Bug-Bounty: <HackerOne_Username>
X-Test-Account-Email: <Your_Test_Account_Email>
```

**Example**:
```bash
curl -H "X-Bug-Bounty: researcher123" \
     -H "X-Test-Account-Email: test@example.com" \
     https://api.robinhood.com/accounts/
```

### Financial Testing Limits

**CRITICAL**: $1,000 USD limit for unbounded loss vulnerabilities

**Rule**: When testing unbounded loss bugs:
1. Stop at $1,000 USD in demonstrated loss
2. File report with verification completed so far
3. Internal teams verify collaboratively with you
4. Testing over $1,000 may result in program termination

**Example Scenarios**:
- ❌ Testing withdrawal bug: Withdrew $5,000 to demonstrate → VIOLATION
- ✅ Testing withdrawal bug: Withdrew $1,000, documented method → COMPLIANT

### Program-Specific Rules

**Do NOT**:
- ❌ Test against accounts you don't own
- ❌ Make financial transactions with other users' accounts
- ❌ Cause service disruption or resource-intensive tests
- ❌ Send large volumes to websockets
- ❌ Create mass support tickets
- ❌ Exfiltrate or retain sensitive data (SSN, PII, credentials)
- ❌ Disclose reports outside HackerOne (EVER)

**Special Considerations**:
- Account Takeover (ATO) findings typically not accepted (may get small bonus if novel)
- Impact must be demonstrable, not theoretical
- Demonstrate actual data accessed, not "could access"
- Mitigations reduce severity (compensating controls, auth requirements, unlikely conditions)

### Zero-Day Policy

**Accepted**: Third-party zero-days directly compromising Robinhood confidentiality/integrity

**Requirements**:
- Must permit vendor disclosure
- Cannot test against third parties/vendors
- Submit via HackerOne

**Not Accepted**:
- Zero-days without vendor disclosure permission
- Third-party testing without authorization

### CVSSv3 Scoring Adjustments

**Severity Decreases When**:
- Exploitation mitigated by compensating controls
- Only exploitable internally (behind Okta, requires privileges)
- Requires unlikely user interaction/conditions
- Already fixed before triage (no bounty)
- Already known internally (no bounty)

**Impact Requirements**:
- ✅ "Here is the SSN I accessed via this IDOR" → High/Critical
- ❌ "This IDOR could allow SSN access" → Medium/Low

### VIP Bug Bounty Program

**Eligibility**: Consistent quality researchers with 3-5+ reports over time

**Benefits**:
- Pre-release feature access
- Test features before public launch
- Higher visibility to security team

### Bitstamp Integration

**Status**: Acquired by Robinhood, integrated into Tier 1/Tier 3

**Tier 1 Assets**:
- `www.bitstamp.net` (main host)

**Tier 3 Assets**:
- `*.bitstamp.net` (all subdomains and supporting services)
- Bitstamp iOS app (Id1406825640)
- Bitstamp Android app (net.bitstamp.app)
- API documentation: https://www.bitstamp.net/api/

**Out of Scope**:
- `sandbox.bitstamp.net` (testing environment)
- Third-party subdomains

### Common Rejection Reasons

1. **Informative Impact**: Theoretical vs demonstrated
2. **Fixed Issues**: No bounty if fixed before triage
3. **Known Issues**: Already known internally
4. **Root Cause Duplicates**: Same underlying component across hosts
5. **Missing Demonstrable Impact**: "Could access" vs "I accessed"
6. **Third-Party Issues**: Must directly exploit Robinhood

### Testing Workflow

```bash
# 1. Create test account with HackerOne email
# Account must meet Robinhood requirements

# 2. Set up headers
export BB_USERNAME="your_h1_username"
export TEST_EMAIL="test@example.com"

# 3. Test authenticated endpoints
curl -H "X-Bug-Bounty: $BB_USERNAME" \
     -H "X-Test-Account-Email: $TEST_EMAIL" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.robinhood.com/accounts/

# 4. Test nummus (crypto)
curl -H "X-Bug-Bounty: $BB_USERNAME" \
     -H "X-Test-Account-Email: $TEST_EMAIL" \
     https://nummus.robinhood.com/accounts/

# 5. Document CVSS breakdown
# Include in report:
# - CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N
# - Breakdown explanation
# - Demonstrable impact (actual data accessed)

# 6. Stop if you hit sensitive data
# Report immediately, do not retain
```

### Dataset Creation (Post-Disclosure)

```bash
# After 90+ days or official disclosure
cat > reports/robinhood-idor-2026.md <<'EOF'
# Robinhood IDOR on Trading Endpoint (Disclosed)

**Program**: Robinhood HackerOne
**Tier**: 1
**Disclosed**: 2026-03-15
**Bounty**: $15,000 (High)
**CVSS**: 7.5 (High)

## Vulnerability
IDOR on /api/orders/{order_id} allowed viewing other users' trading orders

## Headers Used
X-Bug-Bounty: researcher123
X-Test-Account-Email: test@example.com

## Demonstrable Impact
Successfully accessed 5 other users' order details including:
- Stock symbols, quantities, prices
- Order timestamps
- Account IDs (partially masked)
EOF

# Ingest (90+ days post-fix)
peachtree ingest \
  --repo /tmp/disclosed-robinhood \
  --pattern "**/*.md" \
  --output data/raw/robinhood-vulns.jsonl \
  --metadata '{"program": "robinhood", "tier": "1", "platform": "web2"}'
```

## Quick Reference

**Severity**: 
- Extreme (>$30K) | Critical ($5-30K) | High ($2-5K) | Medium ($600-2K) | Low ($50-600) ← General
- Robinhood Tier 1: Critical ($10-25K) | High ($5-10K) | Medium ($500-5K) | Low ($100-500)

**Platforms**: Web2 (traditional), Web3 (wallet/blockchain), Mobile (iOS/Android), Desktop (Win/Mac)

**Report Once**: Same vuln across platforms = 1 report

**Must Include**: Reproduction steps, video PoC (if requested), business impact, CVSS score

**Robinhood Specific**: X-Bug-Bounty and X-Test-Account-Email headers, $1K USD limit on unbounded loss testing

**Out of Scope**: Scanners, self-XSS, known libs, DoS, root/jailbreak, social engineering

**Programs Covered**: Crypto.com ($10-$2M), OKX ($50-$1M), Robinhood ($100-$25K), Bitstamp (Tier 3), Coinbase, Binance

**Tools**: BugBountyAgent, bug-bounty-workflows skill, generate-dataset-card prompt

## Related Resources

- [BugBountyAgent](../../.github/agents/BugBountyAgent.agent.md)
- [bug-bounty-workflows skill](../../.github/skills/bug-bounty-workflows/SKILL.md)
- [security-dataset-integration skill](../../.github/skills/security-dataset-integration/SKILL.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CVSS Calculator](https://www.first.org/cvss/calculator/3.1)
- [HackerOne Disclosure Guidelines](https://www.hackerone.com/disclosure-guidelines)
