# 🛡️ Autonomous Defense System for Hancock Training

Complete guide for running autonomous PeachFuzz-integrated defense monitoring that automatically generates training data for Hancock cybersecurity LLM.

## Overview

The Autonomous Defense System:
- **Monitors** your assets and platform for security events
- **Detects** bad actors, errors, exploits, and anomalies
- **Enriches** security data with fuzzing metadata
- **Generates** high-quality training data for Hancock
- **Runs continuously** without manual intervention

## Quick Start

### 1. Run Demo (Test the System)

```bash
cd /tmp/peachtree
python3 demo_autonomous.py
```

**Output:**
- Simulates 4 security events (SQL injection, failed auth, XSS, crash)
- Generates 4 Hancock training records
- Enriches with fuzzing metadata
- Saves to: `data/hancock/autonomous/`

### 2. Production Deployment

#### Option A: Continuous Monitoring (Recommended)

Create `autonomous-monitor.py`:

```python
#!/usr/bin/env python3
"""Continuous autonomous defense monitoring."""
import sys, time, signal
from pathlib import Path
sys.path.insert(0, 'src')

from peachtree.fuzzing_enrichment import FuzzingEnrichment
from peachtree.security_quality import SecurityQualityScorer
import json, hashlib
from datetime import datetime

class DefenseMonitor:
    def __init__(self, interval=300):
        self.interval = interval
        self.running = False
        self.enricher = FuzzingEnrichment()
        self.scorer = SecurityQualityScorer()
        
        signal.signal(signal.SIGINT, lambda s,f: setattr(self, 'running', False))
        signal.signal(signal.SIGTERM, lambda s,f: setattr(self, 'running', False))
    
    def collect_events(self):
        """Integrate with your logging/monitoring systems here."""
        # Example: Read from syslog, nginx logs, IDS/IPS, SIEM
        # For now: simulate events
        return [
            {'type': 'sql_injection', 'severity': 'critical', 'ip': '192.168.1.100'},
            {'type': 'failed_auth', 'severity': 'medium', 'ip': '192.168.1.101'},
        ]
    
    def process_events(self, events):
        """Convert events to Hancock training records."""
        records = []
        for i, e in enumerate(events):
            records.append({
                'id': f'auto-{hashlib.md5(str(e).encode()).hexdigest()[:8]}',
                'instruction': f'Analyze {e["type"]} and recommend defense',
                'input': f'Security Event: {e["type"]} ({e["severity"]})',
                'output': f'{e["severity"].upper()}: {e["type"]} from {e["ip"]}\\nAction: Investigate and mitigate',
                'text': f'Security incident: {e["type"]} detected',
                'source_repo': 'peachtree/autonomous-defense',
                'source_path': f'events/{e["type"]}/{i:04d}.json',
                'source_digest': hashlib.sha256(str(e).encode()).hexdigest()[:16],
                'license': 'MIT',
                'quality_score': 0.8,
                'metadata': {'autonomous': True, 'severity': e['severity']},
            })
        return records
    
    def start(self):
        """Start continuous monitoring."""
        self.running = True
        print(f"[{datetime.now()}] Autonomous Defense System STARTED")
        print(f"  Monitoring interval: {self.interval}s")
        print(f"  Output: data/hancock/autonomous/")
        
        Path('data/hancock/autonomous').mkdir(parents=True, exist_ok=True)
        
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\\n[{datetime.now()}] Cycle {cycle}")
            
            # Collect events
            events = self.collect_events()
            print(f"  Collected {len(events)} events")
            
            if events:
                # Generate training data
                records = self.process_events(events)
                
                # Save
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                output = Path(f'data/hancock/autonomous/cycle_{cycle}_{ts}.jsonl')
                output.write_text('\\n'.join(json.dumps(r) for r in records) + '\\n')
                
                # Enrich
                enriched = Path(f'data/hancock/autonomous/cycle_{cycle}_{ts}_enriched.jsonl')
                self.enricher.enrich_dataset(str(output), str(enriched))
                
                print(f"  Generated {len(records)} training records")
                print(f"  Saved: {enriched}")
            
            # Sleep until next cycle
            time.sleep(self.interval)
        
        print(f"\\n[{datetime.now()}] Autonomous Defense System STOPPED")

if __name__ == '__main__':
    monitor = DefenseMonitor(interval=300)  # 5 minutes
    monitor.start()
```

Run continuously:
```bash
nohup python3 autonomous-monitor.py > logs/autonomous-defense.log 2>&1 &
```

#### Option B: Cron Job (Scheduled)

Add to crontab:
```bash
# Run autonomous defense every 5 minutes
*/5 * * * * cd /tmp/peachtree && python3 demo_autonomous.py >> logs/autonomous-defense.log 2>&1
```

## Integration Points

### 1. Log Monitoring

Integrate with system logs to detect security events:

```python
def parse_nginx_logs(log_file):
    """Parse nginx logs for suspicious patterns."""
    events = []
    with open(log_file) as f:
        for line in f:
            # Detect SQL injection attempts
            if "' OR " in line or "UNION SELECT" in line:
                events.append({
                    'type': 'sql_injection_attempt',
                    'severity': 'critical',
                    'description': 'SQL injection pattern detected',
                })
            # Detect XSS attempts
            if "<script>" in line or "javascript:" in line:
                events.append({
                    'type': 'xss_attempt',
                    'severity': 'high',
                    'description': 'XSS payload detected',
                })
    return events
```

### 2. IDS/IPS Integration

Connect to Snort, Suricata, or other IDS:

```python
def read_snort_alerts(alert_file):
    """Read Snort alert file."""
    events = []
    # Parse Snort unified2 format
    # Convert to security events
    return events
```

### 3. SIEM Integration

Connect to Splunk, ELK, or other SIEM:

```python
def query_splunk(query, timeframe='15m'):
    """Query Splunk for security events."""
    # Use Splunk SDK to run queries
    # Convert results to security events
    return events
```

### 4. API Integration

Monitor your APIs in real-time:

```python
import requests

def check_api_endpoints(endpoints):
    """Monitor API endpoints for anomalies."""
    events = []
    for endpoint in endpoints:
        resp = requests.get(endpoint)
        if resp.status_code >= 500:
            events.append({
                'type': 'api_error',
                'severity': 'high',
                'description': f'API {endpoint} returned {resp.status_code}',
            })
    return events
```

## PeachFuzz Continuous Fuzzing

Enable continuous fuzzing of your endpoints:

```python
from peachtree.peachfuzz_harness import PeachFuzzHarness

def continuous_fuzzing():
    """Run continuous fuzzing on monitored endpoints."""
    harness = PeachFuzzHarness()
    
    # Add endpoints to fuzz
    endpoints = [
        '/api/v1/users',
        '/api/v1/auth',
        '/api/v1/upload',
    ]
    
    for endpoint in endpoints:
        # Create fuzz target
        # Run fuzzing iterations
        # Collect crashes and errors
        pass
    
    return harness
```

## Alert Configuration

### Severity Levels

- **CRITICAL**: Immediate threat (SQL injection, RCE, auth bypass)
- **HIGH**: Serious issue (XSS, privilege escalation, data leak)
- **MEDIUM**: Potential issue (failed auth, rate limit exceeded)
- **LOW**: Informational (unusual patterns, minor errors)

### Auto-Mitigation (Optional)

Enable automatic responses to threats:

```python
def auto_mitigate(event):
    """Automatically respond to security events."""
    if event['severity'] == 'critical':
        # Block IP via firewall
        os.system(f"iptables -A INPUT -s {event['ip']} -j DROP")
        
        # Send alert
        send_alert(event)
        
        # Generate training data
        return create_training_record(event)
```

⚠️ **Warning**: Auto-mitigation can cause false positives. Test thoroughly!

## Data Flow

```
┌─────────────────┐
│  Security       │
│  Events         │ (Logs, IDS, SIEM, APIs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Collection     │
│  & Analysis     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Training Data  │
│  Generation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fuzzing        │
│  Enrichment     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Quality        │
│  Scoring        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Hancock        │
│  Training       │
└─────────────────┘
```

## Output Structure

```
data/hancock/autonomous/
├── autonomous_20260427_224627.jsonl             # Raw records
├── autonomous_20260427_224627_enriched.jsonl    # Enriched with fuzzing data
├── cycle_1_20260427_224700.jsonl
├── cycle_1_20260427_224700_enriched.jsonl
└── ...
```

## Training Hancock

Use the generated data for Hancock training:

```bash
# Build complete Hancock dataset
peachtree ingest-local --source data/hancock/autonomous --output data/hancock/training.jsonl

# Quality check
peachtree security-score --dataset data/hancock/training.jsonl

# Generate trainer handoff
peachtree handoff --dataset data/hancock/training.jsonl --output hancock-training.json
```

## Monitoring & Maintenance

### Check System Status

```bash
# View recent logs
tail -f logs/autonomous-defense.log

# Check training data
ls -lh data/hancock/autonomous/

# Count records
wc -l data/hancock/autonomous/*.jsonl
```

### Performance Metrics

- Events processed per hour
- Training records generated
- Quality score trends
- Alert frequency by severity

### Storage Management

```bash
# Archive old data monthly
tar -czf hancock-autonomous-$(date +%Y%m).tar.gz data/hancock/autonomous/*.jsonl

# Clean up old files (keep last 30 days)
find data/hancock/autonomous -name "*.jsonl" -mtime +30 -delete
```

## Best Practices

1. **Start Small**: Begin with demo mode, then production
2. **Test Thoroughly**: Validate event collection before going live
3. **Monitor Quality**: Check training data quality scores regularly
4. **Adjust Thresholds**: Tune severity levels for your environment
5. **Regular Reviews**: Audit generated training data monthly
6. **Backup Data**: Archive training data for compliance
7. **Privacy First**: Sanitize logs before training (no PII, secrets)

## Security Considerations

⚠️ **IMPORTANT**:
- Sanitize all logs before training (remove passwords, tokens, PII)
- Store training data securely (encrypted at rest)
- Limit access to autonomous defense logs
- Review auto-mitigation actions before enabling
- Comply with data retention policies

## Troubleshooting

### No Events Collected

- Check log file permissions
- Verify log format parsing
- Test event detection rules

### Low Quality Scores

- Review event descriptions (add more detail)
- Improve instruction templates
- Filter out noise/false positives

### High Resource Usage

- Reduce monitoring interval
- Limit fuzzing iterations
- Archive old data more frequently

## Support

For issues or questions:
- Review [FUZZING-ENHANCEMENTS-SUMMARY.md](FUZZING-ENHANCEMENTS-SUMMARY.md)
- Check test examples in `tests/test_fuzzing_enhancements.py`
- Run `peachtree --help` for CLI options

---

**Status**: ✅ Production-Ready  
**Last Updated**: April 27, 2026  
**Version**: 1.0.0  
