#!/usr/bin/env python3
"""Enhanced Autonomous Defense with PeachFuzz Integration."""
import sys
sys.path.insert(0, 'src')

import json, hashlib
from datetime import datetime
from pathlib import Path

from peachtree.fuzzing_enrichment import FuzzingEnrichment
from peachtree.security_quality import SecurityQualityScorer

print("=" * 80)
print("ENHANCED AUTONOMOUS DEFENSE - PeachFuzz Integration")
print("=" * 80)

# Initialize
enricher = FuzzingEnrichment()
scorer = SecurityQualityScorer()
output_dir = Path('data/hancock/autonomous')
output_dir.mkdir(parents=True, exist_ok=True)

# Expanded event types (security + fuzzing)
events = [
    # Security Events
    {'type': 'sql_injection', 'severity': 'critical', 'ip': '192.168.1.100'},
    {'type': 'xss_attempt', 'severity': 'high', 'ip': '192.168.1.101'},
    {'type': 'failed_auth', 'severity': 'medium', 'ip': '192.168.1.102'},
    {'type': 'path_traversal', 'severity': 'high', 'ip': '192.168.1.103'},
    {'type': 'command_injection', 'severity': 'critical', 'ip': '192.168.1.104'},
    {'type': 'dos_attack', 'severity': 'high', 'ip': '192.168.1.105'},
    
    # Fuzzing Results
    {'type': 'heap_overflow', 'severity': 'critical', 'source': 'peachfuzz'},
    {'type': 'use_after_free', 'severity': 'critical', 'source': 'peachfuzz'},
    {'type': 'buffer_overflow', 'severity': 'critical', 'source': 'peachfuzz'},
    {'type': 'null_pointer_deref', 'severity': 'high', 'source': 'peachfuzz'},
    {'type': 'timeout', 'severity': 'medium', 'source': 'peachfuzz'},
]

print(f"\nCollecting {len(events)} events (security + fuzzing)...")

# Generate training records
records = []
for i, e in enumerate(events):
    source_type = e.get('source', 'security-monitor')
    record = {
        'id': f'auto-{i:04d}',
        'instruction': f'Analyze {e["type"]} and provide defense strategy',
        'input': f'Event: {e["type"]} (Severity: {e["severity"]}, Source: {source_type})',
        'output': f'{e["severity"].upper()}: {e["type"]} detected\nAction: Investigate, mitigate, and document',
        'text': f'Security/Fuzzing event: {e["type"]} from {source_type}',
        'source_repo': 'peachtree/autonomous',
        'source_path': f'events/{i:04d}.json',
        'source_digest': hashlib.sha256(str(e).encode()).hexdigest()[:16],
        'license': 'MIT',
        'quality_score': 0.8,
        'metadata': {
            'autonomous': True,
            'severity': e['severity'],
            'source': source_type,
            'event_type': e['type'],
        },
    }
    records.append(record)

print(f"Generated {len(records)} Hancock training records")

# Save
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
raw_file = output_dir / f'enhanced_{ts}.jsonl'
raw_file.write_text('\n'.join(json.dumps(r) for r in records) + '\n')
print(f"Saved: {raw_file}")

# Enrich
enriched_file = output_dir / f'enhanced_{ts}_enriched.jsonl'
enricher.enrich_dataset(str(raw_file), str(enriched_file))
print(f"Enriched: {enriched_file}")

# Score
report = scorer.score_dataset(str(enriched_file))
print(f"\nQuality Score: {report.average_score:.2f}")
print(f"Security Indicators: {report.security_stats['total_vulnerability_indicators']}")

print("\n" + "=" * 80)
print("✅ ENHANCED AUTONOMOUS DEFENSE COMPLETE")
print("=" * 80)
