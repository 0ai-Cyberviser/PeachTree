# 🛡️ Autonomous Defense - Command Reference

## Quick Commands

### View Generated Data

```bash
# List all autonomous datasets
ls -lh data/hancock/autonomous/

# Count total records
wc -l data/hancock/autonomous/*.jsonl

# View single enriched record (pick latest file)
head -1 data/hancock/autonomous/autonomous_*.jsonl | tail -1 | python3 -m json.tool

# Merge all enriched datasets
cat data/hancock/autonomous/*_enriched.jsonl > data/hancock/autonomous/all_autonomous.jsonl
```

### Quality Analysis

```bash
# Score single dataset
peachtree security-score --dataset data/hancock/autonomous/autonomous_20260427_225639_enriched.jsonl --format json

# Score merged dataset
peachtree security-score --dataset data/hancock/autonomous/all_autonomous.jsonl --format json

# Score with custom threshold
peachtree security-score --dataset data/hancock/autonomous/all_autonomous.jsonl --min-score 0.50 --format json
```

### Manage Background Process

```bash
# Check if running
ps aux | grep -E "python3.*demo_autonomous" | grep -v grep

# View process ID
cat /tmp/autonomous-defense.pid

# View logs (real-time)
tail -f logs/autonomous-defense.log

# View last 50 log lines
tail -50 logs/autonomous-defense.log

# Stop autonomous monitoring
kill $(cat /tmp/autonomous-defense.pid)

# Restart autonomous monitoring
nohup python3 -c "
import sys, time
sys.path.insert(0, 'src')
while True:
    exec(open('demo_autonomous.py').read())
    time.sleep(300)
" > logs/autonomous-defense.log 2>&1 &
echo $! > /tmp/autonomous-defense.pid
```

### Fuzzing Pipeline Commands

```bash
# Enrich dataset with fuzzing metadata
peachtree fuzz-enrich \
  --source data/hancock/autonomous/all_autonomous.jsonl \
  --output data/hancock/autonomous/super_enriched.jsonl

# Optimize corpus for fuzzing
peachtree corpus-optimize \
  --dataset data/hancock/autonomous/all_autonomous.jsonl \
  --output data/hancock/corpus \
  --strategy balanced \
  --max-seeds 500

# Generate PeachFuzz harness
peachtree fuzz-harness \
  --dataset data/hancock/autonomous/all_autonomous.jsonl \
  --output-dir data/hancock/harness \
  --optimize-corpus

# Security-focused quality scoring
peachtree security-score \
  --dataset data/hancock/autonomous/all_autonomous.jsonl \
  --security-weight 0.5 \
  --format json
```

### Hancock Training Workflow

```bash
# 1. Merge all autonomous data
cat data/hancock/autonomous/*_enriched.jsonl > data/hancock/hancock_training.jsonl

# 2. Run quality check
peachtree security-score --dataset data/hancock/hancock_training.jsonl

# 3. Deduplicate if needed
peachtree dedup \
  --input data/hancock/hancock_training.jsonl \
  --output data/hancock/hancock_training_deduped.jsonl

# 4. Generate trainer handoff
peachtree handoff \
  --dataset data/hancock/hancock_training_deduped.jsonl \
  --output hancock-training-manifest.json

# 5. Create model card
peachtree model-card \
  --dataset data/hancock/hancock_training_deduped.jsonl \
  --output HANCOCK-MODEL-CARD.md
```

### Data Management

```bash
# Archive old data (monthly)
tar -czf hancock-autonomous-$(date +%Y%m).tar.gz data/hancock/autonomous/*.jsonl

# Clean old files (keep last 7 days)
find data/hancock/autonomous -name "*.jsonl" -mtime +7 -delete

# Backup to external location
rsync -av data/hancock/autonomous/ /backup/hancock/$(date +%Y%m%d)/

# Check disk usage
du -sh data/hancock/autonomous/
```

### Monitoring & Stats

```bash
# Count events by type (requires jq)
cat data/hancock/autonomous/all_autonomous.jsonl | jq -r '.input' | sort | uniq -c

# Show quality distribution
cat data/hancock/autonomous/all_autonomous.jsonl | jq -r '.quality_score' | sort -n

# Count by severity
cat data/hancock/autonomous/all_autonomous.jsonl | jq -r '.metadata.autonomous' | grep -c true

# Show recent events (last 10)
tail -10 data/hancock/autonomous/all_autonomous.jsonl | jq -r '[.id, .input, .quality_score] | @tsv'

# Security statistics
peachtree security-score --dataset data/hancock/autonomous/all_autonomous.jsonl --format json | jq '.security_statistics'
```

### Troubleshooting

```bash
# Check if demo script works
python3 demo_autonomous.py

# Validate JSONL format
cat data/hancock/autonomous/autonomous_*.jsonl | python3 -m json.tool > /dev/null && echo "✅ Valid JSONL" || echo "❌ Invalid JSONL"

# Check for errors in logs
grep -i error logs/autonomous-defense.log

# Test enrichment manually
peachtree fuzz-enrich \
  --source data/hancock/autonomous/autonomous_20260427_225639.jsonl \
  --output /tmp/test_enriched.jsonl

# Verify background process is collecting data
watch -n 5 'ls -lt data/hancock/autonomous/ | head -5'
```

### Performance Tuning

```bash
# Adjust monitoring interval (in seconds)
# Edit demo_autonomous.py or background command

# Reduce corpus size for faster fuzzing
peachtree corpus-optimize \
  --dataset data/hancock/autonomous/all_autonomous.jsonl \
  --output data/hancock/corpus \
  --strategy balanced \
  --max-seeds 100  # Smaller corpus

# Filter low-quality records
cat data/hancock/autonomous/all_autonomous.jsonl | jq 'select(.quality_score >= 0.60)' > data/hancock/high_quality.jsonl
```

## Status Checks

```bash
# Full system check
echo "=== AUTONOMOUS DEFENSE STATUS ===" && \
echo -e "\n📊 Total Records: $(wc -l < data/hancock/autonomous/all_autonomous.jsonl)" && \
echo -e "📈 Latest File: $(ls -t data/hancock/autonomous/autonomous_*.jsonl | head -1)" && \
echo -e "🔍 Process Running: $(ps aux | grep -E 'python3.*demo_autonomous' | grep -v grep | wc -l)" && \
echo -e "💾 Disk Usage: $(du -sh data/hancock/autonomous/)" && \
echo -e "📋 Log Lines: $(wc -l < logs/autonomous-defense.log 2>/dev/null || echo 0)" && \
echo "================================="
```

## Integration Examples

### Custom Event Parser

```python
# Add to demo_autonomous.py
def parse_nginx_logs():
    events = []
    with open('/var/log/nginx/access.log') as f:
        for line in f.readlines()[-100:]:  # Last 100 lines
            if '404' in line:
                events.append({'type': '404_error', 'severity': 'low'})
            elif '500' in line:
                events.append({'type': '500_error', 'severity': 'high'})
    return events
```

### API Monitor

```python
import requests
def monitor_endpoint():
    try:
        resp = requests.get('https://api.example.com/health', timeout=5)
        if resp.status_code >= 500:
            return {'type': 'api_down', 'severity': 'critical'}
    except:
        return {'type': 'api_timeout', 'severity': 'high'}
```

---

**Last Updated**: April 27, 2026  
**Status**: Production-Ready ✅
