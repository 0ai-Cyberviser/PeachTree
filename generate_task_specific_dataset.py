#!/usr/bin/env python3
"""
Multi-Domain Task-Specific Dataset Generator

Generates high-quality training records for:
- Cybersecurity & AI inference learning
- Fuzzing & bug bounty techniques
- Penetration testing & vulnerability research
- Cryptocurrency, smart contracts, blockchain nodes
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

sys.path.insert(0, 'src')

from peachtree.models import sha256_text


# AI & Inference Learning Techniques
AI_LEARNING_SCENARIOS = [
    {
        "technique": "IGRFT",
        "name": "Inference-Guided Recursive Fine-Tuning",
        "use_case": "CPU-optimized model improvement",
        "benefit": "Self-supervised learning from inference feedback"
    },
    {
        "technique": "LoRA",
        "name": "Low-Rank Adaptation",
        "use_case": "Parameter-efficient fine-tuning",
        "benefit": "8MB adapters instead of full model retraining"
    },
    {
        "technique": "QLoRA",
        "name": "Quantized Low-Rank Adaptation",
        "use_case": "4-bit quantized training",
        "benefit": "Reduces 14GB model to 4GB RAM"
    },
    {
        "technique": "PEFT",
        "name": "Parameter-Efficient Fine-Tuning",
        "use_case": "Minimal parameter updates",
        "benefit": "Preserves base model knowledge"
    },
    {
        "technique": "Chain-of-Thought",
        "name": "Step-by-step reasoning",
        "use_case": "Complex problem solving",
        "benefit": "Improves accuracy on multi-step tasks"
    },
]

# Blockchain & Cryptocurrency
BLOCKCHAIN_SCENARIOS = [
    {
        "topic": "Smart Contract Security",
        "vulnerability": "Reentrancy Attack",
        "blockchain": "Ethereum",
        "severity": "critical"
    },
    {
        "topic": "Consensus Mechanisms",
        "concept": "Proof of Stake",
        "blockchain": "Ethereum 2.0",
        "benefit": "Energy efficiency"
    },
    {
        "topic": "Node Operations",
        "task": "Validator setup",
        "blockchain": "Ethereum",
        "requirement": "32 ETH stake"
    },
    {
        "topic": "DeFi Security",
        "vulnerability": "Flash Loan Attack",
        "blockchain": "Multiple",
        "severity": "critical"
    },
    {
        "topic": "Wallet Security",
        "attack": "Private Key Extraction",
        "blockchain": "All chains",
        "severity": "critical"
    },
]

# Penetration Testing
PENTEST_SCENARIOS = [
    {
        "phase": "Reconnaissance",
        "technique": "OSINT gathering",
        "tools": ["theHarvester", "Recon-ng", "Maltego"],
        "target": "web application"
    },
    {
        "phase": "Scanning",
        "technique": "Port scanning",
        "tools": ["Nmap", "Masscan", "RustScan"],
        "target": "network infrastructure"
    },
    {
        "phase": "Exploitation",
        "technique": "SQL injection",
        "tools": ["sqlmap", "Burp Suite", "ZAP"],
        "target": "database-driven app"
    },
    {
        "phase": "Post-Exploitation",
        "technique": "Privilege escalation",
        "tools": ["LinPEAS", "WinPEAS", "GTFOBins"],
        "target": "compromised system"
    },
]

# Bug Bounty Platforms
BUG_BOUNTY_PROGRAMS = [
    {
        "platform": "HackerOne",
        "program": "Crypto.com",
        "focus": "Cryptocurrency exchange security",
        "top_bounty": "$1,000,000"
    },
    {
        "platform": "Bugcrowd",
        "program": "OKX",
        "focus": "Web3 wallet & trading",
        "top_bounty": "$500,000"
    },
    {
        "platform": "HackerOne",
        "program": "Coinbase",
        "focus": "Crypto custody & trading",
        "top_bounty": "$200,000"
    },
]


def generate_ai_learning_record(scenario: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate AI/ML learning technique record"""
    
    instruction = f"Explain {scenario['technique']} ({scenario['name']}) for AI training"
    
    input_text = f"""
Technique: {scenario['technique']}
Full Name: {scenario['name']}
Primary Use: {scenario['use_case']}
Key Benefit: {scenario['benefit']}
"""
    
    output_text = f"""
## {scenario['technique']}: {scenario['name']}

### Overview
{scenario['name']} ({scenario['technique']}) is an advanced AI training technique designed for {scenario['use_case']}.

### How It Works
{scenario['benefit']} enables efficient model fine-tuning with minimal computational overhead.

### Implementation
```python
# {scenario['technique']} implementation
from transformers import AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

# Load base model with quantization
model = AutoModelForCausalLM.from_pretrained(
    "model-name",
    load_in_4bit=True,  # QLoRA quantization
    device_map="auto"
)

# Configure {scenario['technique']}
config = LoraConfig(
    r=8,  # Low rank
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05
)

# Apply PEFT
model = get_peft_model(model, config)
print(f"Trainable params: {{model.num_parameters()}}")
```

### Benefits
- **Efficiency**: {scenario['benefit']}
- **Use Case**: {scenario['use_case']}
- **Memory**: Significantly reduced compared to full fine-tuning
- **Quality**: Preserves base model capabilities while adding task-specific knowledge

### Best Practices
1. Start with small rank (r=8) and increase if needed
2. Monitor training loss convergence
3. Use gradient accumulation for effective batch sizes
4. Enable mixed precision training (BF16)
5. Implement early stopping to prevent overfitting
"""
    
    text = f"{scenario['technique']} ({scenario['name']}): {scenario['benefit']}"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"ai-learning-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "ai-learning/techniques",
        "source_path": f"{scenario['technique'].lower()}/guide.md",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "ai_learning",
            "technique": scenario['technique'],
            "use_case": scenario['use_case'],
        }
    }


def generate_blockchain_record(scenario: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate blockchain/crypto security record"""
    
    topic = scenario.get('topic', 'Blockchain Security')
    vuln = scenario.get('vulnerability', scenario.get('concept', scenario.get('task', 'Security')))
    
    instruction = f"Analyze {vuln} in {scenario['blockchain']} blockchain"
    
    input_text = f"""
Topic: {topic}
Focus: {vuln}
Blockchain: {scenario['blockchain']}
Severity: {scenario.get('severity', 'medium').upper()}
"""
    
    output_text = f"""
## {topic}: {vuln}

### Blockchain Context
**Platform**: {scenario['blockchain']}
**Severity**: {scenario.get('severity', 'medium').upper()}

### Technical Analysis
{vuln} represents a {"critical security vulnerability" if scenario.get('severity') == 'critical' else "important security consideration"} in {scenario['blockchain']} blockchain applications.

### Attack Vector (if applicable)
```solidity
// Vulnerable smart contract example
contract Vulnerable {{
    mapping(address => uint) public balances;
    
    function withdraw(uint amount) public {{
        require(balances[msg.sender] >= amount);
        
        // VULNERABLE: External call before state update
        (bool success, ) = msg.sender.call{{value: amount}}("");
        require(success);
        
        balances[msg.sender] -= amount;  // State update AFTER call
    }}
}}
```

### Secure Implementation
```solidity
// Secure version with Checks-Effects-Interactions pattern
contract Secure {{
    mapping(address => uint) public balances;
    
    function withdraw(uint amount) public {{
        // Checks
        require(balances[msg.sender] >= amount);
        
        // Effects (update state FIRST)
        balances[msg.sender] -= amount;
        
        // Interactions (external calls LAST)
        (bool success, ) = msg.sender.call{{value: amount}}("");
        require(success);
    }}
}}
```

### Prevention Strategies
1. **Use ReentrancyGuard**: OpenZeppelin's modifier prevents recursive calls
2. **Checks-Effects-Interactions**: Update state before external calls
3. **Pull over Push**: Let users withdraw instead of sending automatically
4. **Formal Verification**: Use tools like Mythril, Slither, Certora

### Auditing Checklist
- [ ] External calls happen after state updates
- [ ] ReentrancyGuard applied to sensitive functions
- [ ] Gas limits considered for external calls
- [ ] Withdrawal patterns use pull-based design
- [ ] Comprehensive test coverage including attack scenarios
"""
    
    text = f"{scenario['blockchain']} security: {vuln} ({scenario.get('severity', 'medium')})"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"blockchain-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "blockchain/security",
        "source_path": f"{scenario['blockchain'].lower()}/{vuln.lower().replace(' ', '-')}.md",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "blockchain",
            "blockchain": scenario['blockchain'],
            "topic": topic,
            "severity": scenario.get('severity', 'medium'),
        }
    }


def generate_pentest_record(scenario: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate penetration testing methodology record"""
    
    instruction = f"Perform {scenario['phase']} phase: {scenario['technique']}"
    
    tools_str = ", ".join(scenario['tools'])
    
    input_text = f"""
Phase: {scenario['phase']}
Technique: {scenario['technique']}
Tools: {tools_str}
Target: {scenario['target']}
"""
    
    output_text = f"""
## Penetration Testing: {scenario['phase']}

### Technique: {scenario['technique']}

**Target**: {scenario['target']}
**Phase**: {scenario['phase']}

### Tools Used
{chr(10).join(f"- **{tool}**: Industry-standard {scenario['phase'].lower()} tool" for tool in scenario['tools'])}

### Methodology

#### Step 1: Preparation
```bash
# Set up testing environment
export TARGET="{scenario['target']}"
mkdir -p pentest/{{recon,scan,exploit,report}}
cd pentest
```

#### Step 2: Execution
```bash
# Example using {scenario['tools'][0]}
{scenario['tools'][0].lower()} --target $TARGET \\
    --output results.txt \\
    --verbose
```

#### Step 3: Analysis
Analyze results for:
- Security weaknesses
- Misconfigurations  
- Vulnerable services
- Exposed sensitive data

### OWASP Testing Guide Alignment
This technique aligns with:
- **OWASP Top 10**: Web Application Security Risks
- **PTES**: Penetration Testing Execution Standard
- **NIST SP 800-115**: Technical Guide to Information Security Testing

### Responsible Disclosure
1. Document all findings with screenshots/POCs
2. Assess business impact and severity
3. Report to bug bounty program or responsible party
4. Allow remediation time before public disclosure
5. Maintain ethical standards (no data exfiltration)

### Legal Considerations
⚠️ **ALWAYS obtain written authorization before testing**
- Scope agreement defining targets
- Rules of engagement
- Emergency contacts
- Legal liability limits

### Next Steps
After {scenario['phase']}, proceed to next phase based on testing methodology.
"""
    
    text = f"Pentesting {scenario['phase']}: {scenario['technique']} using {scenario['tools'][0]}"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"pentest-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "pentesting/methodologies",
        "source_path": f"{scenario['phase'].lower()}/{scenario['technique'].replace(' ', '-')}.md",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "pentesting",
            "phase": scenario['phase'],
            "technique": scenario['technique'],
            "tools": scenario['tools'],
        }
    }


def generate_bugbounty_record(program: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate bug bounty program analysis record"""
    
    instruction = f"Analyze bug bounty program: {program['program']} on {program['platform']}"
    
    input_text = f"""
Platform: {program['platform']}
Program: {program['program']}
Focus: {program['focus']}
Top Bounty: {program['top_bounty']}
"""
    
    output_text = f"""
## Bug Bounty Program: {program['program']}

### Platform & Scope
**Platform**: {program['platform']}
**Company**: {program['program']}
**Focus Area**: {program['focus']}
**Maximum Reward**: {program['top_bounty']}

### Program Highlights
{program['program']} operates a vulnerability disclosure program on {program['platform']} 
focused on {program['focus']}.

### High-Value Targets
1. **Authentication Systems**: Account takeover vulnerabilities
2. **Financial Flows**: Payment processing and fund transfers
3. **API Security**: Authentication, authorization, rate limiting
4. **Smart Contracts**: DeFi protocol vulnerabilities (if applicable)
5. **Wallet Security**: Private key management and custody

### Severity Tiers
- **Critical** (${program['top_bounty']}): RCE, fund theft, mass account takeover
- **High** ($10K-$50K): Authentication bypass, privilege escalation
- **Medium** ($2K-$10K): Stored XSS, CSRF on critical actions
- **Low** ($500-$2K): Information disclosure, open redirects

### Research Methodology
```python
# Bug bounty research workflow
def research_target(target):
    # 1. Reconnaissance
    gather_subdomains(target)
    identify_technologies(target)
    map_attack_surface()
    
    # 2. Vulnerability Discovery
    test_authentication()
    test_authorization()
    test_business_logic()
    test_api_endpoints()
    
    # 3. Exploitation & POC
    develop_exploit()
    document_steps()
    assess_impact()
    
    # 4. Responsible Disclosure
    submit_report()
    track_remediation()
    collect_bounty()
```

### Out of Scope (Common)
- Automated scanner findings without validation
- Self-XSS and clickjacking on non-sensitive pages
- SPF/DKIM/DMARC issues
- Rate limiting on non-critical features
- Theoretical vulnerabilities without POC

### Reporting Best Practices
1. **Clear Title**: "Authentication Bypass via JWT Replay Attack"
2. **Impact Assessment**: Business risk and CVSS score
3. **Reproduction Steps**: Detailed, numbered steps
4. **Proof of Concept**: Screenshots, videos, code samples
5. **Remediation**: Specific fix recommendations

### Platform-Specific Tips

**{program['platform']}**:
- Response time: {"24-48 hours" if program['platform'] == 'HackerOne' else "48-72 hours"}
- Reputation system: Build credibility through quality reports
- Private programs: Invite-only access for proven researchers
"""
    
    text = f"{program['program']} bug bounty on {program['platform']}: {program['focus']}"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"bugbounty-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": f"bugbounty/{program['platform'].lower()}",
        "source_path": f"{program['program'].lower().replace('.', '-')}/analysis.md",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "bug_bounty",
            "platform": program['platform'],
            "program": program['program'],
            "focus": program['focus'],
        }
    }


def main():
    """Generate multi-domain task-specific dataset"""
    
    print("="*80)
    print("MULTI-DOMAIN TASK-SPECIFIC DATASET GENERATOR")
    print("="*80)
    print("Domains: AI Learning, Blockchain, Pentesting, Bug Bounty")
    print("")
    
    output_dir = Path('data/hancock/task-specific')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_records = []
    
    # AI Learning records (30 records - 6 per technique)
    print("🤖 Generating AI Learning technique records...")
    for technique in AI_LEARNING_SCENARIOS:
        for variant in range(6):
            record = generate_ai_learning_record(technique, len(all_records))
            all_records.append(record)
    print(f"   Generated {len(all_records)} AI learning records")
    
    # Blockchain records (25 records - 5 per scenario)
    print("⛓️  Generating Blockchain security records...")
    blockchain_start = len(all_records)
    for scenario in BLOCKCHAIN_SCENARIOS:
        for variant in range(5):
            record = generate_blockchain_record(scenario, len(all_records))
            all_records.append(record)
    print(f"   Generated {len(all_records) - blockchain_start} blockchain records")
    
    # Pentesting records (20 records - 5 per phase)
    print("🔐 Generating Penetration testing records...")
    pentest_start = len(all_records)
    for scenario in PENTEST_SCENARIOS:
        for variant in range(5):
            record = generate_pentest_record(scenario, len(all_records))
            all_records.append(record)
    print(f"   Generated {len(all_records) - pentest_start} pentest records")
    
    # Bug Bounty records (15 records - 5 per program)
    print("💰 Generating Bug Bounty program records...")
    bounty_start = len(all_records)
    for program in BUG_BOUNTY_PROGRAMS:
        for variant in range(5):
            record = generate_bugbounty_record(program, len(all_records))
            all_records.append(record)
    print(f"   Generated {len(all_records) - bounty_start} bug bounty records")
    
    # Save dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'multi_domain_{timestamp}.jsonl'
    
    output_file.write_text(
        '\n'.join(json.dumps(r, sort_keys=True) for r in all_records) + '\n',
        encoding='utf-8'
    )
    
    print(f"\n✅ Generated {len(all_records)} task-specific records")
    print(f"   Saved to: {output_file}")
    
    # Summary
    print(f"\n{'='*80}")
    print("DATASET BREAKDOWN")
    print(f"{'='*80}")
    print(f"AI Learning Techniques: {len([r for r in all_records if r['metadata']['domain'] == 'ai_learning'])}")
    print(f"Blockchain Security: {len([r for r in all_records if r['metadata']['domain'] == 'blockchain'])}")
    print(f"Penetration Testing: {len([r for r in all_records if r['metadata']['domain'] == 'pentesting'])}")
    print(f"Bug Bounty Programs: {len([r for r in all_records if r['metadata']['domain'] == 'bug_bounty'])}")
    print(f"\nTotal: {len(all_records)} records")
    print(f"{'='*80}")
    
    # Save summary
    summary = {
        "timestamp": timestamp,
        "total_records": len(all_records),
        "domains": {
            "ai_learning": len([r for r in all_records if r['metadata']['domain'] == 'ai_learning']),
            "blockchain": len([r for r in all_records if r['metadata']['domain'] == 'blockchain']),
            "pentesting": len([r for r in all_records if r['metadata']['domain'] == 'pentesting']),
            "bug_bounty": len([r for r in all_records if r['metadata']['domain'] == 'bug_bounty']),
        },
        "output_file": str(output_file),
    }
    
    summary_file = output_dir / f'multi_domain_{timestamp}_summary.json'
    summary_file.write_text(json.dumps(summary, indent=2))
    
    print(f"\nSummary: {summary_file}")
    print(f"\nNext: Merge with unified dataset")
    print(f"  cat data/hancock/task-specific/*.jsonl >> data/hancock/unified-expanded.jsonl")
    
    return output_file


if __name__ == '__main__':
    main()
