import json
from datetime import datetime
import hashlib
import os

# Create HackerOne Bug Bounty training dataset for Hancock
training_records = []

def create_record(instruction, output, metadata_type, severity="medium"):
    """Create a training record with proper provenance"""
    content = f"{instruction}\n\n{output}"
    digest = hashlib.sha256(content.encode()).hexdigest()
    
    return {
        "id": digest[:16],
        "instruction": instruction,
        "output": output,
        "metadata": {
            "type": metadata_type,
            "domain": "bug-bounty-hackerone",
            "severity": severity,
            "platform": "HackerOne"
        },
        "source_repo": "0ai-Cyberviser/PeachTree",
        "source_path": "training/hackerone-bug-bounty.py",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

print("Creating HackerOne bug bounty training records...")

# Record 1: Program Scoping
training_records.append(create_record(
    instruction="Analyze a HackerOne cryptocurrency exchange bug bounty program and identify critical testing areas.",
    output="""# HackerOne Crypto Exchange Bug Bounty Analysis

## Critical In-Scope Assets

### Tier 1: Extreme/Critical Rewards ($30K-$2M)
1. **Fund Withdrawal Endpoints**
   - POST /api/withdrawal/crypto
   - POST /api/withdrawal/fiat
   - Impact: Direct financial loss

2. **Trading Interfaces**
   - WebSocket trading feeds
   - Order execution APIs
   - Impact: Market manipulation

3. **Authentication Systems**
   - Login/2FA endpoints
   - Session management
   - Impact: Mass account takeover

## Multi-Platform Assessment Required

### Web2 (Traditional Web)
- RCE on servers: CRITICAL
- SQL Injection: HIGH to CRITICAL
- CSRF on fund transfers: HIGH
- Stored XSS: MEDIUM to HIGH

### Web3 (Wallet & Blockchain)
- Wallet signature phishing: HIGH to CRITICAL
- Smart contract exploits: CRITICAL
- ChainID manipulation: MEDIUM to HIGH

### Mobile (iOS/Android)
- App-level RCE: CRITICAL
- Hardcoded secrets: HIGH
- Insecure storage: MEDIUM to HIGH
- Cross-platform rule: Report ONCE per vuln type

## Testing Authorization
✅ Safe Harbor: Gold Standard legal protection
✅ Test accounts: Use dedicated test accounts only
✅ Financial limits: $1K USD max (Robinhood-specific)
✅ Required headers: X-Bug-Bounty (platform-specific)

## Out-of-Scope
❌ Social engineering
❌ DDoS attacks
❌ Physical security
❌ Third-party services
❌ Brute force ID enumeration without legitimate discovery""",
    metadata_type="program-scoping",
    severity="high"
))

# Record 2: IDOR Detection
training_records.append(create_record(
    instruction="How do I identify and report IDOR vulnerabilities in cryptocurrency exchange APIs for HackerOne?",
    output="""# IDOR Vulnerability Detection & Reporting

## Detection Process

### Step 1: Map User-Specific Endpoints
```
GET /api/account/12345/balance
GET /api/account/12345/transactions
GET /api/account/12345/withdrawal-history
```

### Step 2: Test with Different User IDs
```
# Authenticated as User A (ID: 12345)
# Try accessing User B's data (ID: 67890)
GET /api/account/67890/balance
```

### Step 3: Verify Discovery Path (MANDATORY)
HackerOne requires demonstrating legitimate ID discovery:

✅ Valid Discovery:
- ID in API response (referrer_id field)
- Sequential IDs from normal operations
- IDs in public profile URLs
- IDs in referral/sharing features

❌ Invalid (Will Be Rejected):
- Random ID guessing
- Brute force enumeration
- No explanation of discovery method

## Severity Classification

**Critical** ($5K-$30K): IDOR on fund withdrawal/transfer
**High** ($2K-$5K): IDOR on account data/transaction history
**Medium** ($600-$2K): IDOR on non-sensitive preferences

## Report Template

```markdown
# IDOR: Unauthorized Access to Account Balances

## Summary
IDOR vulnerability allows authenticated users to access other users' account balances by modifying the account ID parameter.

## Severity: HIGH
CVSS 3.1: AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N = 6.5

## Reproduction Steps
1. Log in as testuser1@example.com (Account ID: 12345)
2. Request: GET /api/account/12345/balance
3. Modify request: GET /api/account/67890/balance
4. Observe: Account 67890's balance is returned

## ID Discovery Method
User ID 67890 was discovered in the "referred_by" field when viewing referral dashboard.

## Impact
- All user account balances accessible
- ~5M accounts potentially affected
- PII exposure: names, emails, wallet addresses

## Remediation
Implement server-side authorization check:
if (session.user_id != requested_account_id):
    return 403 Forbidden
```""",
    metadata_type="vulnerability-detection",
    severity="high"
))

# Record 3: CSRF Testing
training_records.append(create_record(
    instruction="How should I test for CSRF vulnerabilities on cryptocurrency withdrawal endpoints?",
    output="""# CSRF Testing on Crypto Withdrawal Endpoints

## Platform-Specific Requirements

### Robinhood (MANDATORY Headers)
```bash
X-Bug-Bounty: true
X-Test-Account-Email: your-test@example.com
```
**Missing these = automatic rejection**

### Financial Testing Limits
- Robinhood: $1,000 USD maximum
- Best practice: Use $0.01-$1.00 amounts
- Always use testnet addresses when possible

## Testing Process

### Step 1: Identify State-Changing Endpoints
```python
# Critical endpoints
POST /api/withdrawal/crypto  # CRITICAL
POST /api/transfer/internal  # HIGH
POST /api/trade/execute      # HIGH
```

### Step 2: Analyze CSRF Protections
```python
import requests

headers = {'Cookie': 'session=abc123'}
data = {
    'amount': '0.01',
    'currency': 'BTC',
    'address': 'testnet-address',
    'csrf_token': 'xyz789'
}

# Test 1: Remove CSRF token
test_data = data.copy()
del test_data['csrf_token']
response = requests.post('https://api.exchange.com/withdrawal', 
                         json=test_data, headers=headers)

if response.status_code == 200:
    print("🚨 CRITICAL: CSRF token not required!")
```

### Step 3: Create PoC
```html
<form action="https://exchange.com/api/withdrawal" method="POST">
    <input name="amount" value="1000">
    <input name="address" value="attacker-wallet">
</form>
<script>document.forms[0].submit();</script>
```

## Severity Classification

**Critical** ($5K-$30K): CSRF on crypto/fiat withdrawal
**High** ($2K-$5K): CSRF on trading or 2FA disable
**Medium** ($600-$2K): CSRF on account settings

## Remediation

1. Implement CSRF tokens (unique per session)
2. SameSite=Strict cookie attribute
3. Double-submit cookie pattern
4. Require password/2FA for withdrawals
5. Email confirmation for new withdrawal addresses""",
    metadata_type="vulnerability-testing",
    severity="critical"
))

# Record 4: Web3 Wallet Security
training_records.append(create_record(
    instruction="Explain Web3 wallet signature phishing vulnerabilities in crypto exchanges.",
    output="""# Web3 Wallet Signature Phishing

## Vulnerability Overview

**Type**: Transaction Display Mismatch
**Platforms**: MetaMask, Coinbase Wallet, WalletConnect
**Severity**: HIGH to CRITICAL
**Impact**: Unauthorized transaction signing, fund theft

## Common Attack Vectors

### 1. EIP-712 Message Mismatch
```javascript
// User sees: "Login to Exchange"
// Actually signing:
{
  "types": {
    "Transfer": [
      {"name": "to", "type": "address"},
      {"name": "amount", "type": "uint256"}
    ]
  },
  "message": {
    "to": "0xAttacker...",
    "amount": "1000000000"  // 1000 USDC
  }
}
```

### 2. ChainID Manipulation
```javascript
// User expects Ethereum (chainId: 1)
// Attacker switches to BSC (chainId: 56)
const maliciousChain = {
  chainId: '0x38',  // BSC
  chainName: 'Ethereum Mainnet'  // DECEPTIVE
};
```

### 3. Blind Transaction Signing
```javascript
ethereum.request({
  method: 'eth_signTransaction',
  params: [{
    data: '0x...'  // Hidden malicious function call
  }]
});
```

## Severity Classification

**Critical** ($10K-$2M): Zero-interaction fund theft
**High** ($2K-$5K): Phishing requiring user action
**Medium** ($600-$2K): UI manipulation without fund impact

## Testing Methodology

### Monitor Signature Requests
```javascript
// Browser console
const original = window.ethereum.request;
window.ethereum.request = function(args) {
    console.log('Web3 Request:', JSON.stringify(args, null, 2));
    return original.call(this, args);
};
```

### Decode Transaction Data
```javascript
const txData = '0xa9059cbb...';
const selector = txData.slice(0, 10);
// 0xa9059cbb = transfer(address,uint256)

// Extract parameters
const toAddress = '0x' + txData.slice(34, 74);
const amount = parseInt(txData.slice(74, 138), 16);
console.log(`Transfer ${amount} to ${toAddress}`);
```

## Report Template

```markdown
# Web3 Wallet: Transaction Display Mismatch

## Summary
DApp shows "Login to Exchange" but EIP-712 payload contains token transfer. Users unknowingly sign fund transfers.

## Severity: HIGH
CVSS: AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N = 7.1

## Affected Platforms
- MetaMask, Coinbase Wallet, WalletConnect
- ❌ Hardware wallets (show full data)

## Impact
- Fund theft via deceptive signatures
- Trust violation
- Phishing at scale

## Remediation
1. Wallets: Highlight monetary actions in red
2. Show USD equivalent amounts
3. Transaction simulation before signing
4. Require "I understand I'm transferring funds" checkbox
```""",
    metadata_type="web3-security",
    severity="high"
))

# Record 5: Responsible Disclosure
training_records.append(create_record(
    instruction="What is the proper disclosure timeline for HackerOne bug bounty reports?",
    output="""# HackerOne Responsible Disclosure Timeline

## Standard Timeline

### Day 0: Submission
- Clear title (max 100 chars)
- Comprehensive summary
- Step-by-step reproduction
- PoC code/screenshots
- CVSS 3.1 score
- Remediation recommendations
- AI tool disclosure (if used)

**Expected Response:**
- Crypto.com: 11 hours average
- GitHub: 24 hours
- Coinbase: 2-3 business days
- Standard: 5 business days

### Days 1-7: Triage
Statuses:
- **Triaged**: Valid vulnerability confirmed
- **Need More Info**: Additional details required
- **Duplicate**: Already reported
- **N/A**: Out of scope/invalid

### Days 7-30: Validation
Company validates:
- Reproduction works
- Impact accurate
- Severity appropriate
- No duplicates

### Days 30-90: Fix Development
- Critical: 15-30 days
- High: 30-60 days
- Medium: 60-90 days
- Low: 90+ days

### After Fix: Bounty Award
**Payment Timelines:**
- Crypto.com: Within 1 month
- GitHub: Within 30 days
- Coinbase: Within 60 days

**Bounty Ranges (Crypto Exchanges):**
- Extreme: $30K-$2M
- Critical: $5K-$30K
- High: $2K-$5K
- Medium: $600-$2K
- Low: $50-$600

### After Fix + Approval: Public Disclosure
Requirements:
1. Fix deployed to production
2. Company approval received
3. Sensitive details redacted
4. 7-day notice before release

## Escalation Path

### No Response After 7 Days
```markdown
Subject: Follow-up on Report #123456

Hi Security Team,

I submitted report #123456 on [date]. I haven't 
received a response in 7 days.

Could you please provide a status update?

Thank you
```

### No Response After 30 Days
- Request HackerOne mediation
- HackerOne contacts program
- Timeline extended 30-60 days

### No Response After 90 Days
- Public disclosure rights (with H1 approval)
- Redact sensitive information
- Cannot weaponize vulnerability

## Communication Best Practices

### Initial Report
```markdown
# [CRITICAL] IDOR in Withdrawal API

## Summary
IDOR in /api/withdrawal allows unauthorized fund transfers.

## Severity: CRITICAL
CVSS: 9.1

## Timeline Request
- Triage within 24 hours
- Fix within 7 days
- Award upon verification

Available for immediate communication via:
- HackerOne messages
- Email: [redacted]
- Signal: [redacted]
```

## Platform-Specific Guidelines

**Crypto.com**: Fast 11h response, 1-month payment
**GitHub**: 24h critical response, 30-day payment
**Coinbase**: 2-3 day response, 60-day payment
**Robinhood**: 5-day response, tiered rewards, $1K test limit""",
    metadata_type="disclosure-process",
    severity="medium"
))

# Save dataset
os.makedirs('data/hancock', exist_ok=True)
output_path = 'data/hancock/hackerone-bug-bounty-training.jsonl'

with open(output_path, 'w') as f:
    for record in training_records:
        f.write(json.dumps(record, sort_keys=True) + '\n')

print(f"✅ Created HackerOne bug bounty training dataset")
print(f"   Output: {output_path}")
print(f"   Records: {len(training_records)}")
print(f"\nBreakdown:")
for i, record in enumerate(training_records, 1):
    print(f"   {i}. {record['metadata']['type']}: {record['metadata']['severity'].upper()}")

print(f"\nNext steps:")
print(f"   1. peachtree security-score --dataset {output_path}")
print(f"   2. peachtree fuzz-enrich --source {output_path} --output data/hancock/enriched.jsonl")
print(f"   3. peachtree handoff --dataset {output_path} --output data/handoff/hancock-training.json")
