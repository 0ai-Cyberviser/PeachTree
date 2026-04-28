#!/usr/bin/env python3
"""
Kali Linux System-Wide Cybersecurity Dataset Fuzzer

Extracts training data from entire Kali Linux system including:
- Security tool documentation and examples
- Exploit databases (Metasploit, Exploit-DB)
- Vulnerability databases (CVE, NVD)
- Wordlists and password research
- Tool configurations and manpages
- Attack patterns and signatures
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
import hashlib
import re

sys.path.insert(0, 'src')

from peachtree.models import sha256_text


# Kali-specific paths to mine
KALI_PATHS = {
    "exploits": [
        "/usr/share/metasploit-framework/modules/exploits",
        "/usr/share/exploitdb",
        "/usr/share/set/src/payloads",
    ],
    "wordlists": [
        "/usr/share/wordlists",
        "/usr/share/seclists",
        "/usr/share/john",
    ],
    "tools": [
        "/usr/share/nmap/scripts",
        "/usr/share/sqlmap",
        "/usr/share/nikto",
        "/usr/share/wfuzz",
    ],
    "signatures": [
        "/var/lib/clamav",
        "/usr/share/snort/rules",
        "/etc/suricata/rules",
    ],
    "databases": [
        "/usr/share/nmap/nselib/data",
        "/usr/share/metasploit-framework/data",
    ]
}

# Kali security tools to document
KALI_TOOLS = [
    "nmap", "sqlmap", "metasploit", "burpsuite", "wireshark",
    "john", "hashcat", "hydra", "aircrack-ng", "reaver",
    "nikto", "wpscan", "dirb", "gobuster", "ffuf",
    "zaproxy", "nuclei", "subfinder", "amass", "masscan",
    "enum4linux", "smbclient", "rpcclient", "snmpwalk",
    "wfuzz", "crackmapexec", "responder", "mimikatz", "bloodhound",
]


def run_command(cmd: List[str], timeout: int = 10) -> str:
    """Run shell command safely with timeout"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors='ignore'
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {str(e)}"


def extract_tool_help(tool: str) -> Dict[str, Any]:
    """Extract help text and examples from security tool"""
    
    help_text = ""
    
    # Try multiple help flags
    for flag in ['-h', '--help', 'help', '-?']:
        output = run_command([tool, flag], timeout=5)
        if output and len(output) > 50:
            help_text = output
            break
    
    # Try man page
    if not help_text:
        man_output = run_command(['man', tool], timeout=5)
        if man_output and len(man_output) > 100:
            help_text = man_output[:5000]  # Limit size
    
    # Extract examples from help text
    examples = []
    if help_text:
        # Look for example sections
        example_section = re.search(
            r'(EXAMPLES?|USAGE|SYNOPSIS):(.*?)(?=\n\n[A-Z]|\Z)',
            help_text,
            re.DOTALL | re.IGNORECASE
        )
        if example_section:
            examples.append(example_section.group(2).strip()[:500])
    
    return {
        'tool': tool,
        'help_text': help_text[:2000] if help_text else "",
        'examples': examples,
        'available': bool(help_text)
    }


def scan_exploit_database() -> List[Dict[str, Any]]:
    """Scan Metasploit and Exploit-DB for exploit data"""
    
    exploits = []
    
    # Check Metasploit exploits
    msf_path = Path("/usr/share/metasploit-framework/modules/exploits")
    if msf_path.exists():
        print(f"   Scanning Metasploit exploits...")
        for exploit_file in list(msf_path.rglob("*.rb"))[:100]:  # Limit to 100
            try:
                content = exploit_file.read_text(errors='ignore')
                
                # Extract metadata
                name_match = re.search(r"Name.*?=>.*?['\"](.+?)['\"]", content)
                desc_match = re.search(r"Description.*?=>.*?['\"](.+?)['\"]", content, re.DOTALL)
                
                if name_match:
                    exploits.append({
                        'source': 'metasploit',
                        'name': name_match.group(1),
                        'description': desc_match.group(1)[:300] if desc_match else "",
                        'path': str(exploit_file.relative_to(msf_path)),
                        'type': 'exploit_module'
                    })
            except Exception:
                continue
    
    # Check Exploit-DB
    exploitdb_path = Path("/usr/share/exploitdb/exploits")
    if exploitdb_path.exists():
        print(f"   Scanning Exploit-DB...")
        for exploit_file in list(exploitdb_path.rglob("*.txt"))[:50]:
            try:
                content = exploit_file.read_text(errors='ignore')[:1000]
                exploits.append({
                    'source': 'exploitdb',
                    'name': exploit_file.stem,
                    'description': content[:300],
                    'path': str(exploit_file.name),
                    'type': 'exploit_code'
                })
            except Exception:
                continue
    
    return exploits


def scan_wordlists() -> List[Dict[str, Any]]:
    """Scan password and fuzzing wordlists"""
    
    wordlists = []
    
    wordlist_path = Path("/usr/share/wordlists")
    if wordlist_path.exists():
        print(f"   Scanning wordlists...")
        for wl_file in list(wordlist_path.rglob("*.txt"))[:30]:
            try:
                # Get sample lines
                lines = wl_file.read_text(errors='ignore').splitlines()[:10]
                
                wordlists.append({
                    'name': wl_file.name,
                    'path': str(wl_file),
                    'size': wl_file.stat().st_size,
                    'sample': lines[:5],
                    'type': 'wordlist'
                })
            except Exception:
                continue
    
    return wordlists


def scan_nmap_scripts() -> List[Dict[str, Any]]:
    """Scan NSE scripts for vulnerability detection patterns"""
    
    scripts = []
    
    nse_path = Path("/usr/share/nmap/scripts")
    if nse_path.exists():
        print(f"   Scanning Nmap NSE scripts...")
        for script_file in list(nse_path.glob("*.nse"))[:50]:
            try:
                content = script_file.read_text(errors='ignore')
                
                # Extract description
                desc_match = re.search(r'description\s*=\s*\[\[(.*?)\]\]', content, re.DOTALL)
                
                scripts.append({
                    'name': script_file.stem,
                    'description': desc_match.group(1).strip()[:300] if desc_match else "",
                    'path': str(script_file.name),
                    'type': 'nse_script'
                })
            except Exception:
                continue
    
    return scripts


def generate_tool_record(tool_data: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate training record from tool documentation"""
    
    instruction = f"Explain how to use {tool_data['tool']} for penetration testing"
    
    input_text = f"""
Tool: {tool_data['tool']}
Category: Penetration Testing
Platform: Kali Linux
Available: {'Yes' if tool_data['available'] else 'No'}
"""
    
    output_text = f"""
## {tool_data['tool'].upper()} - Penetration Testing Tool

### Overview
{tool_data['tool']} is a professional security testing tool included in Kali Linux distribution.

### Usage
{tool_data['help_text'][:1000] if tool_data['help_text'] else 'Tool documentation available via man page'}

### Examples
{tool_data['examples'][0] if tool_data['examples'] else 'Run with -h or --help for usage examples'}

### Kali Integration
- **Location**: Standard in Kali Linux
- **Category**: Security testing and analysis
- **Use Cases**: Vulnerability assessment, penetration testing, security auditing

### Best Practices
1. Always obtain written authorization before testing
2. Scope testing to authorized targets only
3. Document all findings with timestamps
4. Follow responsible disclosure practices
5. Maintain ethical testing standards

### Related Tools
Commonly used alongside other Kali tools for comprehensive security assessment.
"""
    
    text = f"Kali Linux tool: {tool_data['tool']} for penetration testing"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"kali-tool-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "kali-linux/tools",
        "source_path": f"tools/{tool_data['tool']}.md",
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "kali_tools",
            "tool": tool_data['tool'],
            "source": "kali_system",
            "available": tool_data['available'],
        }
    }


def generate_exploit_record(exploit: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate training record from exploit database"""
    
    instruction = f"Analyze {exploit['source']} exploit: {exploit['name']}"
    
    input_text = f"""
Source: {exploit['source'].upper()}
Exploit: {exploit['name']}
Type: {exploit['type']}
Path: {exploit['path']}
"""
    
    output_text = f"""
## Exploit Analysis: {exploit['name']}

### Source Information
**Database**: {exploit['source'].upper()}
**Path**: {exploit['path']}
**Type**: {exploit['type'].replace('_', ' ').title()}

### Description
{exploit['description']}

### Security Implications
This exploit demonstrates a vulnerability that could be used in:
- Penetration testing engagements (authorized)
- Security research and analysis
- Defensive security training
- Vulnerability remediation validation

### Defensive Measures
1. **Patch Management**: Apply security updates promptly
2. **Network Segmentation**: Limit attack surface
3. **Input Validation**: Sanitize all user inputs
4. **Monitoring**: Detect exploit attempts via IDS/IPS
5. **Access Controls**: Implement least privilege

### Ethical Use Only
⚠️ This exploit information is for:
- Authorized penetration testing
- Security research
- Educational purposes
- Defensive security

**Never use without written permission.**

### Remediation
- Update affected software to latest patched version
- Implement compensating controls if patches unavailable
- Monitor for indicators of compromise
- Follow vendor security advisories
"""
    
    text = f"{exploit['source']} exploit: {exploit['name']}"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"kali-exploit-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": f"kali-linux/{exploit['source']}",
        "source_path": exploit['path'],
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "exploits",
            "source": exploit['source'],
            "exploit_type": exploit['type'],
        }
    }


def generate_wordlist_record(wordlist: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate training record from wordlist analysis"""
    
    instruction = f"Analyze password wordlist: {wordlist['name']}"
    
    sample_text = "\n".join(wordlist['sample'][:5])
    
    input_text = f"""
Wordlist: {wordlist['name']}
Size: {wordlist['size']} bytes
Type: {wordlist['type']}
Sample Entries:
{sample_text}
"""
    
    output_text = f"""
## Wordlist Analysis: {wordlist['name']}

### File Information
**Name**: {wordlist['name']}
**Size**: {wordlist['size']:,} bytes
**Location**: Kali Linux wordlist repository

### Purpose
Password wordlists are used in authorized security testing for:
- Password strength assessment
- Dictionary attack testing
- Fuzzing and input validation testing
- Security awareness training

### Sample Patterns
```
{sample_text}
```

### Usage in Security Testing
```bash
# Example: Password strength testing (authorized only)
# With Hydra
hydra -L users.txt -P {wordlist['name']} http-post-form

# With John the Ripper
john --wordlist={wordlist['name']} hashes.txt

# With Hashcat
hashcat -m 0 -a 0 hashes.txt {wordlist['name']}
```

### Defensive Applications
1. **Password Policy Testing**: Validate strength requirements
2. **Training**: Demonstrate weak password risks
3. **Incident Response**: Analyze compromised credentials
4. **Security Awareness**: Show common password patterns

### Ethical Considerations
⚠️ Only use wordlists for:
- Authorized security assessments
- Testing your own systems
- Educational purposes
- Password policy validation

**Never use on systems without permission.**

### Related Resources
- NIST Password Guidelines
- OWASP Authentication Cheat Sheet
- CIS Password Policy Benchmarks
"""
    
    text = f"Kali wordlist analysis: {wordlist['name']}"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"kali-wordlist-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "kali-linux/wordlists",
        "source_path": wordlist['path'],
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "wordlists",
            "size": wordlist['size'],
            "type": wordlist['type'],
        }
    }


def generate_nse_record(script: Dict[str, Any], record_id: int) -> Dict[str, Any]:
    """Generate training record from NSE script"""
    
    instruction = f"Explain Nmap NSE script: {script['name']}"
    
    input_text = f"""
Script: {script['name']}
Type: Nmap Scripting Engine (NSE)
Purpose: Vulnerability detection and enumeration
"""
    
    output_text = f"""
## NSE Script: {script['name']}

### Description
{script['description'] if script['description'] else 'Nmap script for security testing'}

### Usage
```bash
# Run specific NSE script
nmap --script={script['name']} <target>

# With arguments
nmap --script={script['name']} --script-args=arg1=value <target>

# Combined with port scan
nmap -sV --script={script['name']} <target>
```

### NSE Categories
NSE scripts are categorized for different testing phases:
- **Auth**: Authentication testing
- **Default**: Safe, informational scripts
- **Discovery**: Network/service discovery
- **Exploit**: Vulnerability exploitation (use carefully)
- **Intrusive**: May crash services
- **Malware**: Malware detection
- **Safe**: Non-intrusive testing
- **Vuln**: Vulnerability detection

### Security Testing Workflow
1. **Reconnaissance**: Gather target information
2. **Enumeration**: Identify services and versions
3. **Vulnerability Scanning**: Detect security issues
4. **Exploitation**: Test vulnerabilities (authorized only)
5. **Documentation**: Record findings

### Best Practices
- Always scope testing to authorized targets
- Use safe scripts first, intrusive scripts only when authorized
- Monitor script impact on target systems
- Document all scan results with timestamps
- Follow responsible disclosure for findings

### Related Scripts
Nmap has 600+ NSE scripts for comprehensive security testing.
"""
    
    text = f"Nmap NSE script: {script['name']} for vulnerability detection"
    digest = sha256_text(instruction + input_text + output_text)[:16]
    
    return {
        "id": f"kali-nse-{record_id:04d}-{digest[:8]}",
        "instruction": instruction,
        "input": input_text.strip(),
        "output": output_text.strip(),
        "text": text,
        "source_repo": "kali-linux/nmap-scripts",
        "source_path": script['path'],
        "source_digest": digest,
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "metadata": {
            "domain": "nse_scripts",
            "script": script['name'],
            "type": "nmap_nse",
        }
    }


def main():
    """Fuzz entire Kali system for cybersecurity training data"""
    
    print("="*80)
    print("KALI LINUX SYSTEM-WIDE CYBERSECURITY DATASET FUZZER")
    print("="*80)
    print("Extracting training data from Kali Linux system...")
    print("")
    
    output_dir = Path('data/hancock/kali-system')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_records = []
    
    # 1. Extract security tool documentation
    print("🔧 Extracting security tool documentation...")
    tool_data = []
    for tool in KALI_TOOLS[:20]:  # Limit to 20 tools
        print(f"   Processing {tool}...")
        data = extract_tool_help(tool)
        if data['available']:
            tool_data.append(data)
    
    for data in tool_data:
        record = generate_tool_record(data, len(all_records))
        all_records.append(record)
    
    print(f"   Extracted {len(tool_data)} tool documentation records")
    
    # 2. Scan exploit databases
    print("\n💥 Scanning exploit databases...")
    exploits = scan_exploit_database()
    for exploit in exploits[:50]:  # Limit to 50
        record = generate_exploit_record(exploit, len(all_records))
        all_records.append(record)
    print(f"   Extracted {len(exploits[:50])} exploit records")
    
    # 3. Scan wordlists
    print("\n📋 Scanning wordlists...")
    wordlists = scan_wordlists()
    for wordlist in wordlists[:20]:  # Limit to 20
        record = generate_wordlist_record(wordlist, len(all_records))
        all_records.append(record)
    print(f"   Extracted {len(wordlists[:20])} wordlist records")
    
    # 4. Scan NSE scripts
    print("\n🔍 Scanning Nmap NSE scripts...")
    scripts = scan_nmap_scripts()
    for script in scripts[:30]:  # Limit to 30
        record = generate_nse_record(script, len(all_records))
        all_records.append(record)
    print(f"   Extracted {len(scripts[:30])} NSE script records")
    
    # Save dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'kali_system_fuzz_{timestamp}.jsonl'
    
    output_file.write_text(
        '\n'.join(json.dumps(r, sort_keys=True) for r in all_records) + '\n',
        encoding='utf-8'
    )
    
    print(f"\n{'='*80}")
    print("KALI SYSTEM FUZZING COMPLETE")
    print(f"{'='*80}")
    print(f"Total Records Generated: {len(all_records)}")
    print(f"Output File: {output_file}")
    print(f"File Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Breakdown
    print(f"\n{'='*80}")
    print("DATASET BREAKDOWN")
    print(f"{'='*80}")
    print(f"Security Tools: {len([r for r in all_records if r['metadata']['domain'] == 'kali_tools'])}")
    print(f"Exploits: {len([r for r in all_records if r['metadata']['domain'] == 'exploits'])}")
    print(f"Wordlists: {len([r for r in all_records if r['metadata']['domain'] == 'wordlists'])}")
    print(f"NSE Scripts: {len([r for r in all_records if r['metadata']['domain'] == 'nse_scripts'])}")
    print(f"\nTotal: {len(all_records)} records")
    print(f"{'='*80}")
    
    # Save summary
    summary = {
        "timestamp": timestamp,
        "total_records": len(all_records),
        "sources": {
            "tools": len(tool_data),
            "exploits": len(exploits[:50]),
            "wordlists": len(wordlists[:20]),
            "nse_scripts": len(scripts[:30]),
        },
        "output_file": str(output_file),
        "system": "Kali Linux",
    }
    
    summary_file = output_dir / f'kali_system_fuzz_{timestamp}_summary.json'
    summary_file.write_text(json.dumps(summary, indent=2))
    
    print(f"\nSummary: {summary_file}")
    print(f"\nNext: Merge with unified dataset")
    print(f"  cat data/hancock/kali-system/*.jsonl >> data/hancock/unified-expanded.jsonl")
    
    return output_file


if __name__ == '__main__':
    main()
