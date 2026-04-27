# PeachTree Workflow Harness Guide

Comprehensive guide for the integrated Monitor-Audit-Review-Test-Log-Learn-Repeat workflow system.

## Overview

The Workflow Harness orchestrates continuous dataset improvement through an automated 7-phase cycle:

```
┌─────────────────────────────────────────────────────────────┐
│                  WORKFLOW HARNESS CYCLE                      │
└─────────────────────────────────────────────────────────────┘

1. MONITOR   → Track quality metrics and health
2. AUDIT     → Validate integrity and compliance
3. REVIEW    → Generate reports and identify issues
4. TEST      → Run evaluation tests
5. LOG       → Record all operations
6. LEARN     → Analyze trends and optimize
7. REPEAT    → Schedule next cycle

                        ↓
                   [CONTINUOUS]
```

## Quick Start

### Run Full Cycle

```bash
# Run complete workflow cycle
python scripts/workflow-harness.py --full-cycle

# Run with custom config
python scripts/workflow-harness.py \
  --config config/workflow-config.yml \
  --full-cycle
```

### Run Single Phase

```bash
# Run only monitoring phase
python scripts/workflow-harness.py --cycle monitor

# Run audit phase
python scripts/workflow-harness.py --cycle audit

# Run learning phase
python scripts/workflow-harness.py --cycle learn
```

### GitHub Actions Integration

The workflow runs automatically:
- **Daily at 00:00 UTC** (scheduled)
- **Manual trigger** via GitHub Actions UI
- **On dataset changes** (optional)

## Phase Details

### Phase 1: MONITOR

**Purpose:** Track dataset quality metrics over time

**What it does:**
- Runs quality monitoring (via `monitor-quality.py`)
- Tracks record count, quality scores, duplicates
- Checks provenance coverage
- Validates safety gates

**Outputs:**
- `workflow-state/metrics-{cycle_id}.json` - Detailed metrics
- Quality status: success/warning/failure

**Metrics tracked:**
```json
{
  "record_count": 7202,
  "quality_score": 0.85,
  "duplicate_rate": 0.00,
  "provenance_coverage": 1.0
}
```

**Triggers:**
- ⚠️ Warning: Quality score < 0.70 or duplicates > 5%
- ❌ Failure: Safety gates not passed

---

### Phase 2: AUDIT

**Purpose:** Validate dataset integrity and compliance

**What it does:**
- Runs `peachtree audit` command
- Checks for duplicates
- Verifies provenance completeness
- Validates unique IDs

**Outputs:**
- `workflow-state/audit-{cycle_id}.txt` - Audit report
- Integrity validation results

**Checks performed:**
- ✅ All IDs unique
- ✅ No duplicates
- ✅ Provenance complete
- ✅ File integrity valid

---

### Phase 3: REVIEW

**Purpose:** Generate comprehensive reports and analyze trends

**What it does:**
- Generates quality report (markdown)
- Creates lineage/provenance report
- Compares with previous cycles
- Identifies quality trends

**Outputs:**
- `workflow-state/quality-report-{cycle_id}.md`
- `workflow-state/lineage-{cycle_id}.md`
- Trend analysis

**Reports generated:**
- Quality summary with statistics
- License distribution
- Source repository breakdown
- Quality trend analysis (improving/declining/stable)

---

### Phase 4: TEST

**Purpose:** Run comprehensive tests and validation

**What it does:**
- Runs Python test suite (`pytest`)
- Executes evaluation tests (if available)
- Validates dataset exports
- Tests model integration (optional)

**Outputs:**
- `workflow-state/test-results-{cycle_id}.txt`
- Test pass/fail status

**Tests executed:**
- Unit tests (129 tests)
- Integration tests
- Evaluation tests (Hancock eval set)
- Export format validation

---

### Phase 5: LOG

**Purpose:** Record all operations and consolidate results

**What it does:**
- Consolidates all phase results
- Creates cycle summary JSON
- Archives logs permanently
- Tracks historical data

**Outputs:**
- `workflow-state/cycle-summary-{cycle_id}.json`
- `logs/workflow/archive/cycle-summary-{cycle_id}.json`

**Log structure:**
```json
{
  "cycle_id": "20260427-080000",
  "timestamp": "2026-04-27T08:00:00Z",
  "phases": [...],
  "overall_status": "success"
}
```

---

### Phase 6: LEARN

**Purpose:** Analyze trends and generate insights

**What it does:**
- Analyzes historical cycles (last 5-10)
- Identifies quality trends
- Detects common issues
- Generates optimization recommendations

**Outputs:**
- `workflow-state/learning-{cycle_id}.json`
- Insights and recommendations

**Learning capabilities:**
- Quality trend analysis (improving/declining)
- Duplicate rate trends
- Common issue patterns
- Optimization recommendations

**Example insights:**
```json
{
  "insights": [
    "Quality trend: improving (avg: 0.82)",
    "Duplicate rate stable at 0%",
    "Common issue: license compliance (3 occurrences)"
  ],
  "recommendations": [
    "Continue current quality standards",
    "Focus on improving license tracking in next cycle"
  ]
}
```

---

### Phase 7: REPEAT

**Purpose:** Schedule next workflow cycle

**What it does:**
- Determines next run time
- Creates scheduling marker
- Prepares for continuous operation

**Outputs:**
- `workflow-state/next-cycle.txt`

**Scheduling options:**
- Hourly (for rapid iteration)
- Daily (recommended for production)
- Weekly (for stable datasets)
- Custom cron expression

---

## Configuration

### Edit config/workflow-config.yml

```yaml
# Dataset paths
dataset_path: data/datasets/multi-org-security-training.jsonl
manifest_path: data/manifests/multi-org-build-manifest.json

# Quality thresholds
quality_threshold: 0.70
duplicate_threshold: 0.05

# Schedule
schedule: daily  # hourly, daily, weekly

# Enable/disable phases
phases:
  monitor:
    enabled: true
    timeout: 300
  audit:
    enabled: true
  # ... other phases
  
# Alert configuration
alerts:
  enabled: true
  channels:
    - console
    - log_file
  thresholds:
    quality_score_drop: 0.10
    duplicate_rate_increase: 0.05
```

### Key Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `quality_threshold` | 0.70 | Minimum acceptable quality score |
| `duplicate_threshold` | 0.05 | Maximum acceptable duplicate rate |
| `continue_on_failure` | true | Continue to next phase if one fails |
| `schedule` | daily | How often to run cycles |
| `learning.min_cycles_for_trends` | 3 | Cycles needed for trend analysis |
| `alerts.enabled` | true | Enable alert notifications |

---

## Workflow State

All workflow state is stored in `workflow-state/` directory:

```
workflow-state/
├── metrics-20260427-080000.json         # Quality metrics
├── audit-20260427-080000.txt            # Audit report
├── quality-report-20260427-080000.md    # Quality report
├── test-results-20260427-080000.txt     # Test results
├── cycle-summary-20260427-080000.json   # Cycle summary
├── learning-20260427-080000.json        # Learning insights
├── state-20260427-080000.json           # Workflow state
└── next-cycle.txt                       # Next run schedule
```

### State Persistence

- State files retained for 90 days by default
- Archived to `logs/workflow/archive/` permanently
- Used for historical trend analysis
- Enables cycle-to-cycle comparison

---

## Monitoring & Alerts

### Alert Levels

**CRITICAL** - Immediate action required
- Safety gate failures
- Missing provenance
- Test failures

**WARNING** - Review recommended
- Quality degradation (> 10% drop)
- Duplicate rate increase
- Test warnings

**INFO** - Informational
- Quality improvements
- Successful cycles
- Insights generated

### Alert Channels

Configure in `workflow-config.yml`:

```yaml
alerts:
  channels:
    - console      # Print to stdout
    - log_file     # Write to log files
    - slack        # Post to Slack (requires webhook)
    - email        # Send email (requires SMTP config)
```

---

## Integration

### GitHub Actions

The workflow runs automatically via `.github/workflows/workflow-harness.yml`:

**Scheduled runs:**
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
```

**Manual trigger:**
1. Go to Actions tab in GitHub
2. Select "PeachTree Workflow Harness"
3. Click "Run workflow"
4. Choose cycle type (full-cycle or specific phase)

**Artifacts:**
- Workflow state uploaded as artifacts
- Retained for 90 days
- Accessible from Actions runs

**Issue creation:**
- Automatically creates GitHub issue on failure
- Includes failed phases and recommendations
- Tagged with `workflow-failure` label

### Prometheus Integration

Enable in config:

```yaml
integrations:
  prometheus:
    enabled: true
    push_gateway: http://localhost:9091
```

Metrics exported:
- `peachtree_workflow_cycle_duration_seconds`
- `peachtree_workflow_phase_status{phase="monitor"}`
- `peachtree_quality_score`
- `peachtree_duplicate_rate`

### Weights & Biases

Track experiments:

```yaml
integrations:
  weights_and_biases:
    enabled: true
    project: peachtree-monitoring
```

---

## Troubleshooting

### Issue: Workflow fails at monitor phase

**Symptoms:**
```
❌ Phase monitor failed
Issues: Low quality score: 0.62
```

**Solutions:**
1. Check source repository quality
2. Review filtering criteria
3. Increase quality threshold temporarily
4. Run manual quality review

### Issue: Tests failing in test phase

**Symptoms:**
```
❌ Phase test failed
Some tests failed
```

**Solutions:**
1. Check test output: `workflow-state/test-results-{cycle_id}.txt`
2. Run tests manually: `pytest tests/ -v`
3. Fix failing tests before next cycle
4. Disable test phase temporarily if needed

### Issue: Learning phase not generating insights

**Symptoms:**
```
⚠️ Phase learn completed with warnings
Not enough historical data
```

**Solutions:**
- Need at least 3 previous cycles for trend analysis
- Run workflow multiple times to build history
- Check `learning.min_cycles_for_trends` in config

### Issue: Workflow taking too long

**Symptoms:**
```
Command timed out after 300s
```

**Solutions:**
1. Increase timeout in config:
```yaml
phases:
  monitor:
    timeout: 600  # Increase from 300
```
2. Optimize dataset size
3. Run phases separately instead of full cycle

---

## Best Practices

### For Development

1. **Test phases individually first**
   ```bash
   python scripts/workflow-harness.py --cycle monitor
   python scripts/workflow-harness.py --cycle audit
   ```

2. **Review configuration before full cycle**
   - Check thresholds match your dataset
   - Verify paths are correct
   - Test with small dataset first

3. **Monitor workflow state**
   - Review cycle summaries regularly
   - Track quality trends
   - Act on recommendations

### For Production

1. **Enable all phases**
   - All 7 phases should be enabled
   - Set appropriate timeouts
   - Configure alerts

2. **Schedule appropriately**
   - Daily for active development
   - Weekly for stable datasets
   - Hourly for critical datasets

3. **Archive workflow state**
   - Retain logs for compliance
   - Track long-term trends
   - Enable auto-remediation carefully

4. **Integrate monitoring**
   - Use Prometheus/Grafana
   - Set up Slack/email alerts
   - Create GitHub issues automatically

---

## Advanced Usage

### Custom Phase Implementation

Add custom phases by extending `WorkflowHarness`:

```python
class CustomWorkflowHarness(WorkflowHarness):
    def phase_custom(self) -> CycleResult:
        """Custom workflow phase"""
        # Your custom logic here
        return CycleResult(
            phase="custom",
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={},
            issues=[],
            recommendations=[],
            artifacts=[]
        )
```

### Auto-Remediation

Enable automatic fixing of issues:

```yaml
learning:
  auto_remediation:
    enabled: true
    max_retries: 3
```

**Available auto-remediations:**
- Run deduplication if duplicates > threshold
- Filter low-quality records automatically
- Rebalance source repository weights

### Cycle Chaining

Chain multiple cycles for complex workflows:

```bash
# Morning cycle: monitor and audit
python scripts/workflow-harness.py --cycle monitor
python scripts/workflow-harness.py --cycle audit

# Afternoon cycle: review and learn
python scripts/workflow-harness.py --cycle review
python scripts/workflow-harness.py --cycle learn
```

---

## Metrics & KPIs

Track workflow effectiveness:

| Metric | Formula | Target |
|--------|---------|--------|
| Cycle Success Rate | Successful cycles / Total cycles | > 95% |
| Quality Trend | Current quality - Average quality | Positive |
| Issue Resolution Time | Time from issue detection to fix | < 24 hours |
| False Positive Rate | False alerts / Total alerts | < 10% |
| Learning Accuracy | Correct recommendations / Total | > 80% |

---

## FAQ

**Q: How often should the workflow run?**
A: Daily for active development, weekly for stable production datasets.

**Q: Can I run phases in parallel?**
A: No, phases must run sequentially as each depends on previous results.

**Q: What happens if a phase fails?**
A: By default, workflow continues to next phase. Set `continue_on_failure: false` to stop on failures.

**Q: How long is state retained?**
A: 90 days by default, configurable via `retention_days` in config.

**Q: Can I customize alert thresholds?**
A: Yes, edit `alerts.thresholds` in `config/workflow-config.yml`.

**Q: Does this work with multiple datasets?**
A: Yes, create separate config files for each dataset.

---

## Support

- **GitHub Issues:** Report bugs and feature requests
- **Discussions:** Ask questions and share insights
- **Documentation:** See other guides in docs/

---

**The Workflow Harness enables continuous dataset improvement through automated monitoring, learning, and optimization!**
