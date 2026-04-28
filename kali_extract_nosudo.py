#!/usr/bin/env python3
"""
Kali Linux Complete Extraction - NO SUDO VERSION
Extracts all security knowledge without requiring root access
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_record(instruction: str, response: str, category: str, source_path: str) -> dict:
    """Create a dataset record"""
    content = f"{instruction}\n{response}"
    digest = hashlib.sha256(content.encode()).hexdigest()
    
    return {
        "id": f"kali-complete-{digest[:12]}",
        "instruction": instruction,
        "response": response,
        "category": category,
        "source_repo": "kali-linux-system",
        "source_path": source_path,
        "source_digest": digest,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def extract_metasploit_modules():
    """Extract Metasploit module documentation"""
    records = []
    msf_path = Path("/usr/share/metasploit-framework/modules")
    
    if not msf_path.exists():
        logger.warning(f"Metasploit not found at {msf_path}")
        return records
    
    logger.info("🔍 Extracting Metasploit modules...")
    
    count = 0
    for rb_file in msf_path.rglob("*.rb"):
        if count >= 5000:  # Limit to prevent overflow
            break
        
        try:
            content = rb_file.read_text(errors='ignore')
            
            # Extract module info
            module_name = str(rb_file.relative_to(msf_path))
            module_type = rb_file.parts[-3] if len(rb_file.parts) >= 3 else "unknown"
            
            # Create simplified instruction
            instruction = f"Explain the Metasploit {module_type} module: {module_name}"
            
            # Extract key lines
            description_lines = [line.strip() for line in content.split('\n') 
                                if line.strip().startswith('#') and len(line.strip()) > 3][:10]
            
            if description_lines:
                response = f"Module: {module_name}\nType: {module_type}\n\n" + "\n".join(description_lines[:5])
                records.append(create_record(instruction, response, "metasploit", str(rb_file)))
                count += 1
        
        except Exception as e:
            continue
    
    logger.info(f"✅ Extracted {len(records)} Metasploit modules")
    return records


def extract_exploitdb():
    """Extract Exploit-DB entries"""
    records = []
    edb_path = Path("/usr/share/exploitdb/exploits")
    
    if not edb_path.exists():
        logger.warning(f"Exploit-DB not found at {edb_path}")
        return records
    
    logger.info("🔍 Extracting Exploit-DB database...")
    
    count = 0
    for exploit_file in edb_path.rglob("*"):
        if count >= 5000:
            break
        
        if exploit_file.is_file() and exploit_file.suffix in ['.txt', '.py', '.rb', '.c', '.sh']:
            try:
                content = exploit_file.read_text(errors='ignore')[:2000]
                
                exploit_name = exploit_file.stem
                exploit_type = exploit_file.parts[-2] if len(exploit_file.parts) >= 2 else "unknown"
                
                instruction = f"Analyze the {exploit_type} exploit: {exploit_name}"
                response = f"Exploit: {exploit_name}\nPlatform: {exploit_type}\n\nCode:\n{content[:500]}"
                
                records.append(create_record(instruction, response, "exploit-db", str(exploit_file)))
                count += 1
            
            except Exception:
                continue
    
    logger.info(f"✅ Extracted {len(records)} Exploit-DB entries")
    return records


def extract_nse_scripts():
    """Extract Nmap NSE scripts"""
    records = []
    nse_path = Path("/usr/share/nmap/scripts")
    
    if not nse_path.exists():
        logger.warning(f"NSE scripts not found at {nse_path}")
        return records
    
    logger.info("🔍 Extracting Nmap NSE scripts...")
    
    for nse_file in nse_path.glob("*.nse"):
        try:
            content = nse_file.read_text(errors='ignore')
            
            # Extract description
            desc_lines = [line for line in content.split('\n') if 'description' in line.lower()][:5]
            
            instruction = f"Explain the Nmap NSE script: {nse_file.stem}"
            response = f"NSE Script: {nse_file.stem}\n\nDescription:\n" + "\n".join(desc_lines)
            
            records.append(create_record(instruction, response, "nse-scripts", str(nse_file)))
        
        except Exception:
            continue
    
    logger.info(f"✅ Extracted {len(records)} NSE scripts")
    return records


def extract_wordlists():
    """Extract wordlist information"""
    records = []
    wordlist_path = Path("/usr/share/wordlists")
    
    if not wordlist_path.exists():
        logger.warning(f"Wordlists not found at {wordlist_path}")
        return records
    
    logger.info("🔍 Extracting wordlists...")
    
    for wl_file in wordlist_path.rglob("*"):
        if wl_file.is_file():
            try:
                # Get file info without reading entire file
                size = wl_file.stat().st_size
                
                # Sample first 20 lines
                with open(wl_file, 'r', errors='ignore') as f:
                    sample_lines = [f.readline().strip() for _ in range(20) if f.readline()]
                
                instruction = f"Describe the wordlist: {wl_file.name}"
                response = f"Wordlist: {wl_file.name}\nSize: {size} bytes\n\nSample entries:\n" + "\n".join(sample_lines[:10])
                
                records.append(create_record(instruction, response, "wordlists", str(wl_file)))
            
            except Exception:
                continue
    
    logger.info(f"✅ Extracted {len(records)} wordlists")
    return records


def main():
    logger.info("\n" + "="*60)
    logger.info("KALI LINUX COMPLETE SYSTEM EXTRACTION (NO SUDO)")
    logger.info("="*60 + "\n")
    
    all_records = []
    
    # Extract from all sources
    all_records.extend(extract_metasploit_modules())
    all_records.extend(extract_exploitdb())
    all_records.extend(extract_nse_scripts())
    all_records.extend(extract_wordlists())
    
    # Save output
    output_dir = Path("data/kali-complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"kali_complete_{timestamp}.jsonl"
    
    with open(output_file, 'w') as f:
        for record in all_records:
            f.write(json.dumps(record, sort_keys=True) + '\n')
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total records: {len(all_records):,}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Breakdown
    categories = {}
    for record in all_records:
        cat = record['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    logger.info("\nBreakdown by category:")
    for cat, count in sorted(categories.items()):
        logger.info(f"  {cat}: {count:,}")
    
    return output_file


if __name__ == "__main__":
    main()
