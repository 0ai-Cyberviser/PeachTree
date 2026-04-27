#!/usr/bin/env python3
"""Quick audit and export for multi-org security dataset"""

import subprocess
import json
from pathlib import Path

# Run audit
print("Running PeachTree audit...")
audit_result = subprocess.run(
    ['peachtree', 'audit', '--dataset', 'data/datasets/multi-org-security-training.jsonl'],
    capture_output=True,
    text=True,
    cwd='/tmp/peachtree'
)

audit_data = json.loads(audit_result.stdout)
print(json.dumps(audit_data, indent=2))

# Save audit to file
Path('/tmp/peachtree/reports/multi-org-audit.json').write_text(
    json.dumps(audit_data, indent=2),
    encoding='utf-8'
)

print("\n✅ Audit complete!")
print(f"Records: {audit_data['records']}")
print(f"Unique IDs: {audit_data['unique_ids']}")
print(f"Duplicates: {audit_data['duplicates']}")
print(f"Has Provenance: {audit_data['has_provenance']}")
print(f"Min Quality Score: {audit_data.get('min_quality_score', 'N/A')}")

# Sample first record
print("\n" + "="*60)
print("Checking first record...")
dataset_file = Path('/tmp/peachtree/data/datasets/multi-org-security-training.jsonl')
first_line = dataset_file.read_text(encoding='utf-8').split('\n')[0]
first_record = json.loads(first_line)

print(f"Record ID: {first_record.get('id', 'N/A')}")
print(f"Source: {first_record.get('source_repo', 'N/A')}")
print(f"Content length: {len(first_record.get('content', ''))} chars")
print(f"Has instruction: {'instruction' in first_record}")

if 'instruction' in first_record:
    print(f"Instruction preview: {first_record['instruction'][:100]}...")
