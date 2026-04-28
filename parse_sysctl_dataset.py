#!/usr/bin/env python3
"""
Parse sysctl output into cybersecurity training records.
Extracts kernel configuration, network settings, and security parameters.
"""

from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path


def sha256_text(text: str) -> str:
    """Generate SHA256 digest of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def parse_sysctl_output(sysctl_text: str) -> list[dict]:
    """Parse sysctl -a output into structured records."""
    records = []
    
    # Security-focused categories
    security_params = {
        "kernel.randomize_va_space": "ASLR configuration",
        "kernel.kptr_restrict": "Kernel pointer restriction",
        "kernel.dmesg_restrict": "Kernel log access control",
        "kernel.yama.ptrace_scope": "Ptrace protection",
        "kernel.unprivileged_bpf_disabled": "BPF access control",
        "kernel.unprivileged_userns_clone": "User namespace creation",
        "net.ipv4.conf.all.accept_redirects": "ICMP redirect handling",
        "net.ipv4.conf.all.accept_source_route": "Source routing",
        "net.ipv4.conf.all.log_martians": "Martian packet logging",
        "net.ipv4.conf.all.rp_filter": "Reverse path filtering",
        "net.ipv4.tcp_syncookies": "SYN flood protection",
        "net.ipv4.icmp_echo_ignore_all": "ICMP ping response",
        "net.ipv6.conf.all.accept_ra": "IPv6 router advertisements",
        "fs.suid_dumpable": "SUID core dump control",
        "fs.protected_hardlinks": "Hardlink protection",
        "fs.protected_symlinks": "Symlink protection",
        "kernel.core_pattern": "Core dump handling",
    }
    
    network_params = {
        "net.ipv4.ip_forward": "IPv4 packet forwarding",
        "net.core.rmem_max": "Max socket receive buffer",
        "net.core.wmem_max": "Max socket send buffer",
        "net.ipv4.tcp_max_syn_backlog": "TCP SYN queue size",
        "net.netfilter.nf_conntrack_max": "Connection tracking limit",
        "net.ipv4.tcp_keepalive_time": "TCP keepalive interval",
    }
    
    # Parse sysctl lines
    params = {}
    for line in sysctl_text.splitlines():
        line = line.strip()
        if not line or "permission denied" in line.lower():
            continue
        
        if " = " in line:
            key, value = line.split(" = ", 1)
            params[key.strip()] = value.strip()
    
    # Generate security analysis records
    for param, description in security_params.items():
        if param in params:
            value = params[param]
            
            # Determine security impact
            is_secure = analyze_security_param(param, value)
            recommendation = get_security_recommendation(param, value, is_secure)
            
            instruction = f"Analyze the security configuration of kernel parameter `{param}` with value `{value}`. What are the security implications?"
            
            input_text = f"System: Kali Linux\nParameter: {param}\nCurrent Value: {value}\nDescription: {description}"
            
            output = f"""Security Analysis:
- **Parameter**: {param}
- **Current Value**: {value}
- **Security Status**: {"✅ SECURE" if is_secure else "⚠️ INSECURE"}
- **Description**: {description}

{recommendation}

**Penetration Testing Impact**:
{get_pentest_impact(param, value)}

**Hardening Recommendation**:
{get_hardening_advice(param)}
"""
            
            text = f"{instruction}\n\n{input_text}\n\n{output}"
            
            records.append({
                "instruction": instruction,
                "input": input_text,
                "output": output,
                "text": text,
                "source_repo": "0ai-Cyberviser/PeachTree",
                "source_path": "kali-system/sysctl-analysis",
                "source_digest": sha256_text(text),
                "license_id": "MIT",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "domain": "kernel-security",
                    "category": "security-configuration",
                    "parameter": param,
                    "value": value,
                    "is_secure": is_secure,
                    "source": "sysctl"
                }
            })
    
    # Generate network configuration records
    for param, description in network_params.items():
        if param in params:
            value = params[param]
            
            instruction = f"Explain the network configuration parameter `{param}` and its implications for penetration testing."
            
            input_text = f"Parameter: {param}\nValue: {value}\nDescription: {description}"
            
            output = f"""Network Configuration Analysis:
- **Parameter**: {param}
- **Value**: {value}
- **Purpose**: {description}

{get_network_analysis(param, value)}
"""
            
            text = f"{instruction}\n\n{input_text}\n\n{output}"
            
            records.append({
                "instruction": instruction,
                "input": input_text,
                "output": output,
                "text": text,
                "source_repo": "0ai-Cyberviser/PeachTree",
                "source_path": "kali-system/sysctl-network",
                "source_digest": sha256_text(text),
                "license_id": "MIT",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "domain": "network-configuration",
                    "category": "networking",
                    "parameter": param,
                    "value": value,
                    "source": "sysctl"
                }
            })
    
    # Generate comprehensive system overview record
    security_overview = generate_security_overview(params)
    records.append(security_overview)
    
    return records


def analyze_security_param(param: str, value: str) -> bool:
    """Determine if parameter value is secure."""
    secure_configs = {
        "kernel.randomize_va_space": "2",
        "kernel.kptr_restrict": "2",
        "kernel.dmesg_restrict": "1",
        "kernel.yama.ptrace_scope": ["1", "2", "3"],
        "kernel.unprivileged_bpf_disabled": "2",
        "kernel.unprivileged_userns_clone": "0",
        "net.ipv4.conf.all.accept_redirects": "0",
        "net.ipv4.conf.all.accept_source_route": "0",
        "net.ipv4.conf.all.log_martians": "1",
        "net.ipv4.conf.all.rp_filter": ["1", "2"],
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.icmp_echo_ignore_all": "0",  # Usually want this 0 for network testing
        "fs.suid_dumpable": "0",
        "fs.protected_hardlinks": "1",
        "fs.protected_symlinks": "1",
    }
    
    if param in secure_configs:
        expected = secure_configs[param]
        if isinstance(expected, list):
            return value in expected
        return value == expected
    
    return True  # Unknown param, assume OK


def get_security_recommendation(param: str, value: str, is_secure: bool) -> str:
    """Get security recommendation for parameter."""
    recommendations = {
        "kernel.randomize_va_space": {
            True: "ASLR is fully enabled (value 2), providing strong protection against buffer overflow attacks.",
            False: "⚠️ ASLR is disabled or partially enabled. Set to 2 for full randomization."
        },
        "kernel.kptr_restrict": {
            True: "Kernel pointers are fully restricted, preventing information disclosure.",
            False: "⚠️ Kernel pointers may be exposed. Set to 2 to hide from all users."
        },
        "kernel.unprivileged_bpf_disabled": {
            True: "Unprivileged BPF is disabled (value 2, permanent). Prevents local privilege escalation via BPF.",
            False: "⚠️ Unprivileged BPF may be enabled. Set to 2 to permanently disable."
        },
        "net.ipv4.tcp_syncookies": {
            True: "SYN cookies enabled. System resistant to SYN flood DoS attacks.",
            False: "⚠️ SYN cookies disabled. Vulnerable to SYN flood attacks."
        },
        "net.ipv4.conf.all.accept_redirects": {
            True: "ICMP redirects accepted. May be vulnerable to MITM attacks.",
            False: "ICMP redirects rejected. Protected against redirect-based MITM."
        },
    }
    
    if param in recommendations:
        return recommendations[param].get(is_secure, "Configuration requires review.")
    
    return "Configuration should be reviewed based on security policy."


def get_pentest_impact(param: str, value: str) -> str:
    """Describe penetration testing impact."""
    impacts = {
        "kernel.randomize_va_space": "ASLR affects exploit reliability. Value 2 requires bypasses or information leaks.",
        "kernel.kptr_restrict": "Restricts kernel address disclosure, making ROP chain construction harder.",
        "net.ipv4.ip_forward": "IP forwarding enabled suggests routing/gateway role. Check for routing misconfigurations.",
        "net.ipv4.tcp_syncookies": "SYN cookies make SYN flood DoS attacks less effective.",
        "net.ipv4.conf.all.accept_redirects": "If enabled (1), ICMP redirect attacks may be possible.",
    }
    
    return impacts.get(param, "Review parameter for potential security impact during assessment.")


def get_hardening_advice(param: str) -> str:
    """Get hardening advice."""
    advice = {
        "kernel.randomize_va_space": "sysctl -w kernel.randomize_va_space=2",
        "kernel.kptr_restrict": "sysctl -w kernel.kptr_restrict=2",
        "kernel.dmesg_restrict": "sysctl -w kernel.dmesg_restrict=1",
        "kernel.unprivileged_bpf_disabled": "sysctl -w kernel.unprivileged_bpf_disabled=2",
        "net.ipv4.conf.all.accept_redirects": "sysctl -w net.ipv4.conf.all.accept_redirects=0",
        "net.ipv4.conf.all.accept_source_route": "sysctl -w net.ipv4.conf.all.accept_source_route=0",
        "net.ipv4.conf.all.log_martians": "sysctl -w net.ipv4.conf.all.log_martians=1",
        "net.ipv4.tcp_syncookies": "sysctl -w net.ipv4.tcp_syncookies=1",
    }
    
    return advice.get(param, f"Review documentation for {param} and apply appropriate hardening.")


def get_network_analysis(param: str, value: str) -> str:
    """Analyze network parameter."""
    analyses = {
        "net.ipv4.ip_forward": {
            "1": "IP forwarding is ENABLED. System acts as router. Check for:\n- Unauthorized routing\n- Packet sniffing opportunities\n- Pivot potential in network",
            "0": "IP forwarding is DISABLED. System is end-host only."
        },
        "net.core.rmem_max": f"Maximum socket receive buffer: {value} bytes. Affects network performance and potential buffer overflow attacks.",
        "net.netfilter.nf_conntrack_max": f"Connection tracking limit: {value}. Affects firewall capacity and DoS resistance.",
    }
    
    if param in analyses:
        if isinstance(analyses[param], dict):
            return analyses[param].get(value, f"Value {value} requires analysis.")
        return analyses[param]
    
    return f"Network parameter {param} set to {value}. Impacts network stack behavior."


def generate_security_overview(params: dict) -> dict:
    """Generate comprehensive security overview record."""
    instruction = "Provide a comprehensive security assessment of a Kali Linux system based on its kernel parameters."
    
    input_text = f"System: Kali Linux\nKernel: {params.get('kernel.osrelease', 'Unknown')}\nTotal Parameters: {len(params)}"
    
    # Analyze key security settings
    aslr = params.get("kernel.randomize_va_space", "0")
    kptr = params.get("kernel.kptr_restrict", "0")
    bpf = params.get("kernel.unprivileged_bpf_disabled", "0")
    syncookies = params.get("net.ipv4.tcp_syncookies", "0")
    ip_forward = params.get("net.ipv4.ip_forward", "0")
    
    output = f"""Comprehensive Security Assessment:

**Kernel Information**:
- Release: {params.get('kernel.osrelease', 'Unknown')}
- Architecture: {params.get('kernel.arch', 'Unknown')}
- Hostname: {params.get('kernel.hostname', 'Unknown')}

**Memory Protection**:
- ASLR: {"✅ Enabled (Full)" if aslr == "2" else "⚠️ Weak/Disabled"}
- Kernel Pointer Restriction: {"✅ Enabled" if kptr in ["1", "2"] else "❌ Disabled"}
- SUID Dumpable: {params.get('fs.suid_dumpable', 'Unknown')}

**Access Control**:
- Unprivileged BPF: {"✅ Disabled" if bpf == "2" else "⚠️ Enabled"}
- Ptrace Scope: {params.get('kernel.yama.ptrace_scope', 'Unknown')}
- User Namespaces: {"⚠️ Allowed" if params.get('kernel.unprivileged_userns_clone') == "1" else "✅ Restricted"}

**Network Security**:
- IP Forwarding: {"⚠️ Enabled (Router Mode)" if ip_forward == "1" else "✅ Disabled"}
- SYN Cookies: {"✅ Enabled" if syncookies == "1" else "❌ Disabled"}
- ICMP Redirects: {params.get('net.ipv4.conf.all.accept_redirects', 'Unknown')}
- Source Routing: {params.get('net.ipv4.conf.all.accept_source_route', 'Unknown')}

**File System Protection**:
- Protected Hardlinks: {params.get('fs.protected_hardlinks', 'Unknown')}
- Protected Symlinks: {params.get('fs.protected_symlinks', 'Unknown')}

**Penetration Testing Observations**:
1. IP forwarding enabled suggests this is a routing/gateway system
2. ASLR enabled at level {aslr} will affect exploit development
3. Connection tracking limit: {params.get('net.netfilter.nf_conntrack_max', 'Unknown')}
4. Docker detected: {params.get('net.ipv4.conf.docker0.forwarding', 'Not present')}

**Hardening Priority**:
1. Review IP forwarding requirement
2. Enable SYN cookies if disabled
3. Restrict ICMP redirects
4. Enable kernel pointer restriction
5. Audit container security settings
"""
    
    text = f"{instruction}\n\n{input_text}\n\n{output}"
    
    return {
        "instruction": instruction,
        "input": input_text,
        "output": output,
        "text": text,
        "source_repo": "0ai-Cyberviser/PeachTree",
        "source_path": "kali-system/sysctl-comprehensive",
        "source_digest": sha256_text(text),
        "license_id": "MIT",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "domain": "security-assessment",
            "category": "system-hardening",
            "source": "sysctl",
            "kernel_version": params.get('kernel.osrelease', 'Unknown')
        }
    }


def main():
    """Main execution."""
    # Read sysctl output from stdin or file
    import sys
    
    if len(sys.argv) > 1:
        sysctl_file = Path(sys.argv[1])
        sysctl_text = sysctl_file.read_text(encoding='utf-8')
    else:
        print("Reading from stdin (paste sysctl -a output, Ctrl+D when done)...")
        sysctl_text = sys.stdin.read()
    
    # Parse and generate records
    records = parse_sysctl_output(sysctl_text)
    
    # Output directory
    output_dir = Path("data/hancock/sysctl")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"sysctl_analysis_{timestamp}.jsonl"
    
    # Write JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + '\n')
    
    # Summary
    summary = {
        "timestamp": timestamp,
        "total_records": len(records),
        "output_file": str(output_file),
        "categories": {
            "security_configuration": sum(1 for r in records if r["metadata"].get("category") == "security-configuration"),
            "network_configuration": sum(1 for r in records if r["metadata"].get("category") == "networking"),
            "comprehensive_assessment": sum(1 for r in records if r["metadata"].get("category") == "system-hardening")
        }
    }
    
    summary_file = output_dir / f"sysctl_analysis_{timestamp}_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(summary, indent=2, sort_keys=True))
    
    print(f"\n✅ Sysctl Analysis Complete!")
    print(f"   Total Records: {len(records)}")
    print(f"   Output: {output_file}")
    print(f"   Size: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"\nBreakdown:")
    print(f"   - Security Config: {summary['categories']['security_configuration']}")
    print(f"   - Network Config: {summary['categories']['network_configuration']}")
    print(f"   - System Assessment: {summary['categories']['comprehensive_assessment']}")
    print(f"\nNext: cat {output_file} >> data/hancock/unified-expanded.jsonl")


if __name__ == "__main__":
    main()
