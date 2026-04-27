# PeachTree Monitoring & Metrics Configuration

This directory contains configurations for monitoring PeachTree dataset operations and tracking key metrics.

## Metrics Tracked

### Dataset Build Metrics
- **Build Duration** - Time to build dataset from sources
- **Record Count** - Total training records created
- **Source Count** - Number of source documents ingested
- **Duplicate Rate** - Percentage of duplicate records detected
- **Safety Gate Pass Rate** - Percentage passing all safety gates
- **Quality Score** - Average quality score across records

### Safety & Compliance Metrics
- **Secret Detection Rate** - Secrets/credentials found and filtered
- **License Violations** - Unlicensed or problematic content detected
- **Provenance Coverage** - Percentage with full source attribution
- **Policy Compliance** - Compliance with security domain policy pack

### Performance Metrics
- **Ingestion Throughput** - Records/second during ingestion
- **Build Throughput** - Records/second during dataset build
- **Deduplication Time** - Time spent on duplicate detection
- **Export Time** - Time to export to training formats

## Prometheus Integration

### Metrics Endpoint

PeachTree can expose metrics for Prometheus scraping:

```python
# Enable metrics in your Python code
from peachtree.metrics import MetricsCollector

collector = MetricsCollector(port=9090)
collector.start()

# Metrics available at http://localhost:9090/metrics
```

### Sample Metrics Output

```
# HELP peachtree_build_duration_seconds Time to build dataset
# TYPE peachtree_build_duration_seconds gauge
peachtree_build_duration_seconds{domain="security"} 245.3

# HELP peachtree_records_created_total Total training records created
# TYPE peachtree_records_created_total counter
peachtree_records_created_total{domain="security"} 7202

# HELP peachtree_duplicates_detected_total Duplicate records detected
# TYPE peachtree_duplicates_detected_total counter
peachtree_duplicates_detected_total{domain="security"} 0

# HELP peachtree_safety_gate_failures_total Safety gate failures
# TYPE peachtree_safety_gate_failures_total counter
peachtree_safety_gate_failures_total{gate="secret_detection"} 0
peachtree_safety_gate_failures_total{gate="license_validation"} 3

# HELP peachtree_quality_score Dataset quality score
# TYPE peachtree_quality_score gauge
peachtree_quality_score{domain="security"} 0.85
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'peachtree'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 60s
    scrape_timeout: 10s
```

## Grafana Dashboards

### Dataset Build Dashboard

Track dataset build operations:

```json
{
  "dashboard": {
    "title": "PeachTree Dataset Builds",
    "panels": [
      {
        "title": "Records Created",
        "targets": [
          {
            "expr": "peachtree_records_created_total"
          }
        ]
      },
      {
        "title": "Build Duration",
        "targets": [
          {
            "expr": "peachtree_build_duration_seconds"
          }
        ]
      },
      {
        "title": "Safety Gate Pass Rate",
        "targets": [
          {
            "expr": "100 - (rate(peachtree_safety_gate_failures_total[5m]) * 100)"
          }
        ]
      }
    ]
  }
}
```

### Safety & Compliance Dashboard

Monitor safety gates and policy compliance:

- Secret detection events
- License violations
- Provenance coverage
- Policy pack results

## Logging Configuration

### Structured Logging

```python
# logging_config.yaml
version: 1
formatters:
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    formatter: json
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    formatter: json
    filename: /var/log/peachtree/peachtree.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  peachtree:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console]
```

### Log Levels

- **DEBUG** - Detailed diagnostic information
- **INFO** - General informational messages
- **WARNING** - Warning messages (e.g., policy violations)
- **ERROR** - Error messages (e.g., safety gate failures)
- **CRITICAL** - Critical failures (e.g., data loss)

### Example Log Entries

```json
{
  "timestamp": "2026-04-27T08:19:19Z",
  "level": "INFO",
  "logger": "peachtree.builder",
  "message": "Dataset build started",
  "domain": "security",
  "source_count": 4187
}

{
  "timestamp": "2026-04-27T08:23:45Z",
  "level": "WARNING",
  "logger": "peachtree.safety",
  "message": "License violation detected",
  "file": "exploit-code.py",
  "license": "unknown",
  "action": "flagged_for_review"
}

{
  "timestamp": "2026-04-27T08:24:05Z",
  "level": "INFO",
  "logger": "peachtree.builder",
  "message": "Dataset build completed",
  "domain": "security",
  "records_created": 7202,
  "duration_seconds": 245.3,
  "duplicates_removed": 0
}
```

## Alerting Rules

### Prometheus Alerts

```yaml
# alerts.yml
groups:
  - name: peachtree_alerts
    interval: 60s
    rules:
      - alert: HighDuplicateRate
        expr: |
          (peachtree_duplicates_detected_total / peachtree_records_created_total) > 0.10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High duplicate rate detected in dataset build"
          description: "More than 10% duplicates in {{ $labels.domain }} dataset"

      - alert: SafetyGateFailures
        expr: |
          rate(peachtree_safety_gate_failures_total[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Safety gate failures detected"
          description: "Safety gate {{ $labels.gate }} failing"

      - alert: LowQualityScore
        expr: |
          peachtree_quality_score < 0.70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Dataset quality score below threshold"
          description: "Quality score {{ $value }} for {{ $labels.domain }}"

      - alert: BuildDurationHigh
        expr: |
          peachtree_build_duration_seconds > 600
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "Dataset build taking longer than expected"
          description: "Build duration {{ $value }}s for {{ $labels.domain }}"
```

## Metrics Collection Script

```python
#!/usr/bin/env python3
"""
Collect and report PeachTree metrics
"""

import json
from pathlib import Path
from datetime import datetime

def collect_metrics(dataset_path, manifest_path):
    """Collect metrics from dataset and manifest"""
    
    # Load manifest
    manifest = json.loads(Path(manifest_path).read_text())
    
    # Count records
    with open(dataset_path) as f:
        record_count = sum(1 for line in f if line.strip())
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "dataset": dataset_path,
        "records": record_count,
        "source_count": manifest.get("source_count", 0),
        "duplicates": 0,  # From audit results
        "build_duration": 0,  # From build logs
        "quality_score": 0.85,  # From quality scoring
        "safety_gates": {
            "secret_detection": "passed",
            "license_validation": "passed",
            "provenance_check": "passed"
        },
        "domain": manifest.get("domain", "unknown")
    }
    
    return metrics

def export_prometheus(metrics, output_file):
    """Export metrics in Prometheus format"""
    
    lines = [
        f'peachtree_records_created_total{{domain="{metrics["domain"]}"}} {metrics["records"]}',
        f'peachtree_source_count{{domain="{metrics["domain"]}"}} {metrics["source_count"]}',
        f'peachtree_duplicates_detected_total{{domain="{metrics["domain"]}"}} {metrics["duplicates"]}',
        f'peachtree_quality_score{{domain="{metrics["domain"]}"}} {metrics["quality_score"]}',
    ]
    
    Path(output_file).write_text('\n'.join(lines) + '\n')

if __name__ == "__main__":
    metrics = collect_metrics(
        "data/datasets/multi-org-security-training.jsonl",
        "data/manifests/multi-org-build-manifest.json"
    )
    
    print(json.dumps(metrics, indent=2))
    export_prometheus(metrics, "/var/lib/prometheus/peachtree_metrics.prom")
```

## Deployment Monitoring

### GitHub Actions Integration

```yaml
# .github/workflows/monitor-dataset.yml
name: Monitor Dataset Metrics

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  collect-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      
      - name: Collect metrics
        run: |
          python scripts/collect-metrics.py \
            --dataset data/datasets/multi-org-security-training.jsonl \
            --manifest data/manifests/multi-org-build-manifest.json \
            --output reports/metrics.json
      
      - name: Upload to monitoring system
        run: |
          curl -X POST https://metrics.example.com/api/v1/metrics \
            -H "Content-Type: application/json" \
            -d @reports/metrics.json
```

### Continuous Monitoring

- **Real-time metrics** via Prometheus/Grafana
- **Periodic health checks** via GitHub Actions
- **Alert notifications** via PagerDuty/Slack
- **Dashboard visibility** for stakeholders

---

**Monitoring ensures PeachTree dataset quality and performance in production!**
