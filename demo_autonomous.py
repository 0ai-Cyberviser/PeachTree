#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from peachtree.fuzzing_enrichment import FuzzingEnrichment
from peachtree.security_quality import SecurityQualityScorer
from peachtree.models import sha256_text
import json
from datetime import datetime

print('='*80)
print('AUTONOMOUS DEFENSE SYSTEM - DEMONSTRATION')
print('='*80)

output_dir = Path('data/hancock/autonomous')
output_dir.mkdir(parents=True, exist_ok=True)

print('\nSIMULATING SECURITY EVENTS...')
events = [
    {'type': 'sql_injection', 'severity': 'critical', 'ip': '192.168.1.100'},
    {'type': 'failed_auth', 'severity': 'medium', 'ip': '192.168.1.101'},
    {'type': 'xss_attempt', 'severity': 'high', 'ip': '192.168.1.102'},
    {'type': 'crash', 'severity': 'high', 'ip': 'internal'},
]

print(f'  Collected {len(events)} events')

training_records = []
for i, e in enumerate(events):
    training_records.append({
        'id': f'auto-{i:04d}',
        'instruction': f'Analyze {e["type"]} security event',
        'input': f'Event: {e["type"]}',
        'output': f'{e["severity"].upper()}: {e["type"]} from {e["ip"]}',
        'text': f'Security event: {e["type"]}',
        'source_repo': 'peachtree/autonomous',
        'source_path': f'events/{i:04d}.json',
        'source_digest': sha256_text(str(i))[:16],
        'license': 'MIT',
        'quality_score': 0.8,
        'metadata': {'autonomous': True},
    })

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = output_dir / f'autonomous_{timestamp}.jsonl'
output_file.write_text('\n'.join(json.dumps(r) for r in training_records) + '\n')

print(f'\nGENERATED {len(training_records)} HANCOCK TRAINING RECORDS')
print(f'Saved to: {output_file}')

enriched_file = output_dir / f'autonomous_{timestamp}_enriched.jsonl'
enricher = FuzzingEnrichment()
enricher.enrich_dataset(str(output_file), str(enriched_file))
print(f'Enriched: {enriched_file}')

scorer = SecurityQualityScorer()
report = scorer.score_dataset(str(enriched_file))
print(f'\nQUALITY SCORE: {report.average_score:.2f}')
print(f'='*80)
print('AUTONOMOUS DEFENSE COMPLETE - READY FOR HANCOCK!')
print('='*80)
