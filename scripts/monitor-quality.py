"""
PeachTree Dataset Quality Monitoring System

Automated monitoring, alerting, and reporting for dataset quality metrics.
Run this script periodically (e.g., via cron or GitHub Actions) to track
dataset health over time.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class QualityMetrics:
    """Dataset quality metrics snapshot"""
    timestamp: str
    dataset_path: str
    record_count: int
    unique_ids: int
    duplicate_count: int
    duplicate_rate: float
    avg_quality_score: float
    min_quality_score: float
    max_quality_score: float
    records_below_threshold: int
    license_distribution: Dict[str, int]
    source_repo_distribution: Dict[str, int]
    avg_content_length: float
    total_size_bytes: int
    provenance_coverage: float
    safety_gates_passed: bool
    issues: List[str]
    warnings: List[str]


class DatasetQualityMonitor:
    """Monitor and track dataset quality metrics over time"""
    
    def __init__(self, dataset_path: str, quality_threshold: float = 0.70):
        self.dataset_path = Path(dataset_path)
        self.quality_threshold = quality_threshold
        self.metrics = None
        
    def analyze(self) -> QualityMetrics:
        """Run full quality analysis on dataset"""
        
        records = self._load_records()
        
        # Basic counts
        record_count = len(records)
        unique_ids = len(set(r.get("id") for r in records))
        duplicate_count = record_count - unique_ids
        duplicate_rate = duplicate_count / record_count if record_count > 0 else 0
        
        # Quality scores
        quality_scores = [r.get("quality_score", 0) for r in records]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        min_quality = min(quality_scores) if quality_scores else 0
        max_quality = max(quality_scores) if quality_scores else 0
        below_threshold = sum(1 for s in quality_scores if s < self.quality_threshold)
        
        # License distribution
        licenses = [r.get("license", "unknown") for r in records]
        license_dist = {lic: licenses.count(lic) for lic in set(licenses)}
        
        # Source repository distribution
        sources = [r.get("source_repo", "unknown") for r in records]
        source_dist = {src: sources.count(src) for src in set(sources)}
        
        # Content analysis
        content_lengths = [len(r.get("content", "")) for r in records]
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        # File size
        total_size = self.dataset_path.stat().st_size
        
        # Provenance
        with_provenance = sum(1 for r in records if r.get("provenance"))
        provenance_coverage = with_provenance / record_count if record_count > 0 else 0
        
        # Safety and issues
        issues = []
        warnings = []
        
        if duplicate_rate > 0.05:
            issues.append(f"High duplicate rate: {duplicate_rate:.1%}")
        
        if avg_quality < self.quality_threshold:
            issues.append(f"Average quality below threshold: {avg_quality:.2f} < {self.quality_threshold}")
        
        if provenance_coverage < 1.0:
            warnings.append(f"Incomplete provenance: {provenance_coverage:.1%} coverage")
        
        if "unknown" in license_dist:
            warnings.append(f"Unknown licenses: {license_dist['unknown']} records")
        
        if below_threshold > record_count * 0.1:
            warnings.append(f"{below_threshold} records below quality threshold ({below_threshold/record_count:.1%})")
        
        safety_passed = len(issues) == 0
        
        self.metrics = QualityMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_path=str(self.dataset_path),
            record_count=record_count,
            unique_ids=unique_ids,
            duplicate_count=duplicate_count,
            duplicate_rate=duplicate_rate,
            avg_quality_score=avg_quality,
            min_quality_score=min_quality,
            max_quality_score=max_quality,
            records_below_threshold=below_threshold,
            license_distribution=license_dist,
            source_repo_distribution=source_dist,
            avg_content_length=avg_content_length,
            total_size_bytes=total_size,
            provenance_coverage=provenance_coverage,
            safety_gates_passed=safety_passed,
            issues=issues,
            warnings=warnings
        )
        
        return self.metrics
    
    def _load_records(self) -> List[Dict]:
        """Load all records from dataset"""
        records = []
        with open(self.dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate human-readable quality report"""
        
        if not self.metrics:
            self.analyze()
        
        m = self.metrics
        
        report = f"""
# Dataset Quality Report

**Generated:** {m.timestamp}  
**Dataset:** {m.dataset_path}  
**Status:** {"✅ PASSED" if m.safety_gates_passed else "❌ FAILED"}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Records | {m.record_count:,} |
| Unique IDs | {m.unique_ids:,} |
| Duplicates | {m.duplicate_count:,} ({m.duplicate_rate:.1%}) |
| Average Quality | {m.avg_quality_score:.3f} |
| Quality Range | {m.min_quality_score:.3f} - {m.max_quality_score:.3f} |
| Below Threshold | {m.records_below_threshold:,} ({m.records_below_threshold/m.record_count:.1%}) |
| Provenance Coverage | {m.provenance_coverage:.1%} |
| Dataset Size | {m.total_size_bytes:,} bytes ({m.total_size_bytes/1024/1024:.1f} MB) |
| Avg Content Length | {m.avg_content_length:.0f} characters |

---

## License Distribution

| License | Count | Percentage |
|---------|-------|------------|
"""
        for license, count in sorted(m.license_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = count / m.record_count * 100
            report += f"| {license} | {count:,} | {pct:.1f}% |\n"
        
        report += "\n---\n\n## Source Repository Distribution\n\n"
        report += "| Repository | Records | Percentage |\n"
        report += "|------------|---------|------------|\n"
        
        for source, count in sorted(m.source_repo_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = count / m.record_count * 100
            report += f"| {source} | {count:,} | {pct:.1f}% |\n"
        
        if m.issues:
            report += "\n---\n\n## ❌ Issues\n\n"
            for issue in m.issues:
                report += f"- {issue}\n"
        
        if m.warnings:
            report += "\n---\n\n## ⚠️ Warnings\n\n"
            for warning in m.warnings:
                report += f"- {warning}\n"
        
        if not m.issues and not m.warnings:
            report += "\n---\n\n## ✅ No Issues or Warnings\n\nDataset quality is excellent!\n"
        
        report += "\n---\n\n## Recommendations\n\n"
        
        if m.duplicate_rate > 0:
            report += "- **Deduplication:** Run `peachtree dedup` to remove duplicates\n"
        
        if m.avg_quality_score < 0.80:
            report += "- **Quality Improvement:** Filter low-quality records or enhance sources\n"
        
        if m.provenance_coverage < 1.0:
            report += "- **Provenance:** Rebuild dataset to ensure full provenance coverage\n"
        
        if "unknown" in m.license_distribution:
            report += "- **License Compliance:** Specify licenses for all source repositories\n"
        
        if not any([m.duplicate_rate > 0, m.avg_quality_score < 0.80, m.provenance_coverage < 1.0]):
            report += "- Dataset is in excellent condition. Continue regular monitoring.\n"
        
        if output_path:
            Path(output_path).write_text(report)
        
        return report
    
    def save_metrics(self, output_path: str) -> None:
        """Save metrics as JSON for tracking over time"""
        if not self.metrics:
            self.analyze()
        
        Path(output_path).write_text(json.dumps(asdict(self.metrics), indent=2))
    
    def compare_with_baseline(self, baseline_path: str) -> Dict[str, Any]:
        """Compare current metrics with baseline"""
        
        if not self.metrics:
            self.analyze()
        
        baseline = json.loads(Path(baseline_path).read_text())
        
        comparison = {
            "record_count_change": self.metrics.record_count - baseline["record_count"],
            "quality_score_change": self.metrics.avg_quality_score - baseline["avg_quality_score"],
            "duplicate_rate_change": self.metrics.duplicate_rate - baseline["duplicate_rate"],
            "provenance_coverage_change": self.metrics.provenance_coverage - baseline["provenance_coverage"],
            "degraded": False,
            "improved": False
        }
        
        # Determine if quality degraded or improved
        if (comparison["quality_score_change"] < -0.05 or 
            comparison["duplicate_rate_change"] > 0.05 or
            comparison["provenance_coverage_change"] < -0.05):
            comparison["degraded"] = True
        
        if (comparison["quality_score_change"] > 0.05 or 
            comparison["duplicate_rate_change"] < -0.05 or
            comparison["record_count_change"] > 100):
            comparison["improved"] = True
        
        return comparison


class AlertManager:
    """Send alerts when dataset quality degrades"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def send_alert(self, metrics: QualityMetrics, severity: str = "warning") -> None:
        """Send alert via configured channels"""
        
        if severity == "critical" and not metrics.safety_gates_passed:
            self._send_critical_alert(metrics)
        elif severity == "warning" and metrics.warnings:
            self._send_warning_alert(metrics)
    
    def _send_critical_alert(self, metrics: QualityMetrics) -> None:
        """Send critical alert (e.g., to PagerDuty, email)"""
        
        message = f"""
🚨 CRITICAL: Dataset Quality Failure

Dataset: {metrics.dataset_path}
Time: {metrics.timestamp}

Issues:
{chr(10).join(f"- {issue}" for issue in metrics.issues)}

Metrics:
- Quality Score: {metrics.avg_quality_score:.3f}
- Duplicate Rate: {metrics.duplicate_rate:.1%}
- Records: {metrics.record_count:,}

Action Required: Investigate and remediate dataset issues immediately.
"""
        
        print(message)
        # TODO: Integrate with PagerDuty, Slack, email, etc.
        self._create_github_issue(metrics, severity="critical")
    
    def _send_warning_alert(self, metrics: QualityMetrics) -> None:
        """Send warning alert (e.g., to Slack, email)"""
        
        message = f"""
⚠️ WARNING: Dataset Quality Warnings

Dataset: {metrics.dataset_path}
Time: {metrics.timestamp}

Warnings:
{chr(10).join(f"- {warning}" for warning in metrics.warnings)}

Review recommended but not critical.
"""
        
        print(message)
        # TODO: Integrate with Slack, Discord, etc.
    
    def _create_github_issue(self, metrics: QualityMetrics, severity: str) -> None:
        """Create GitHub issue for quality problems"""
        
        title = f"[{severity.upper()}] Dataset Quality Issue - {metrics.dataset_path}"
        body = f"""
## Dataset Quality Alert

**Severity:** {severity}  
**Timestamp:** {metrics.timestamp}  
**Dataset:** {metrics.dataset_path}

### Issues

{chr(10).join(f"- {issue}" for issue in metrics.issues)}

### Warnings

{chr(10).join(f"- {warning}" for warning in metrics.warnings)}

### Metrics

- Record Count: {metrics.record_count:,}
- Quality Score: {metrics.avg_quality_score:.3f}
- Duplicate Rate: {metrics.duplicate_rate:.1%}
- Provenance Coverage: {metrics.provenance_coverage:.1%}

### Action Items

- [ ] Investigate root cause
- [ ] Remediate dataset issues
- [ ] Re-run quality checks
- [ ] Update documentation if needed
"""
        
        # TODO: Use GitHub API to create issue
        print(f"\n[GitHub Issue Preview]\nTitle: {title}\n{body}")


# ============================================================================
# MAIN MONITORING SCRIPT
# ============================================================================

def main():
    """Main monitoring workflow"""
    
    print("=== PeachTree Dataset Quality Monitor ===\n")
    
    # Configuration
    dataset_path = "data/datasets/multi-org-security-training.jsonl"
    baseline_path = "reports/baseline-metrics.json"
    report_path = "reports/quality-report-latest.md"
    metrics_path = f"reports/metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    # Initialize monitor
    monitor = DatasetQualityMonitor(dataset_path, quality_threshold=0.70)
    
    # Run analysis
    print("📊 Analyzing dataset quality...")
    metrics = monitor.analyze()
    
    # Save metrics
    monitor.save_metrics(metrics_path)
    print(f"✅ Metrics saved to {metrics_path}")
    
    # Generate report
    print("📝 Generating quality report...")
    report = monitor.generate_report(report_path)
    print(f"✅ Report saved to {report_path}")
    
    # Compare with baseline (if exists)
    if Path(baseline_path).exists():
        print("\n📈 Comparing with baseline...")
        comparison = monitor.compare_with_baseline(baseline_path)
        
        if comparison["degraded"]:
            print("❌ Quality has DEGRADED since baseline")
        elif comparison["improved"]:
            print("✅ Quality has IMPROVED since baseline")
        else:
            print("➡️  Quality is STABLE (no significant change)")
        
        print(f"  Record count: {comparison['record_count_change']:+,}")
        print(f"  Quality score: {comparison['quality_score_change']:+.3f}")
        print(f"  Duplicate rate: {comparison['duplicate_rate_change']:+.1%}")
    else:
        # Create baseline
        print("\n📌 Creating baseline metrics...")
        monitor.save_metrics(baseline_path)
        print(f"✅ Baseline saved to {baseline_path}")
    
    # Send alerts if needed
    alert_manager = AlertManager({})
    
    if not metrics.safety_gates_passed:
        print("\n🚨 CRITICAL: Safety gates failed!")
        alert_manager.send_alert(metrics, severity="critical")
    elif metrics.warnings:
        print("\n⚠️  WARNING: Quality warnings detected")
        alert_manager.send_alert(metrics, severity="warning")
    else:
        print("\n✅ All quality checks passed!")
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Records: {metrics.record_count:,}")
    print(f"Quality: {metrics.avg_quality_score:.3f}")
    print(f"Duplicates: {metrics.duplicate_rate:.1%}")
    print(f"Provenance: {metrics.provenance_coverage:.1%}")
    print(f"Status: {'✅ PASSED' if metrics.safety_gates_passed else '❌ FAILED'}")
    
    # Exit with appropriate code
    exit_code = 0 if metrics.safety_gates_passed else 1
    return exit_code


if __name__ == "__main__":
    exit(main())
