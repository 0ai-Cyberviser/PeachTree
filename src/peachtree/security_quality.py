"""Security-focused quality scoring for fuzzing and vulnerability datasets.

Extends the base DatasetQualityScorer with security-specific metrics for
crash reports, vulnerability documentation, and fuzzing corpus quality.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json
import re
from typing import Any

from .quality import DatasetQualityScorer, RecordQualityScore, DatasetQualityReport


@dataclass(frozen=True)
class SecurityDatasetReport(DatasetQualityReport):
    """Extended quality report with security statistics."""
    
    security_stats: dict[str, Any] = None  # type: ignore
    
    def to_dict(self, include_records: bool = True) -> dict[str, Any]:
        """Convert to dictionary with security stats."""
        data = super().to_dict(include_records=include_records)
        if self.security_stats:
            data["security_statistics"] = self.security_stats
        return data


@dataclass(frozen=True)
class SecurityQualityMetrics:
    """Security-specific quality metrics for a dataset record."""
    
    vulnerability_indicators: int  # Number of vulnerability keywords found
    exploit_complexity: float  # Estimated exploit complexity (0.0-1.0)
    defensive_value: float  # Value for defensive learning (0.0-1.0)
    crash_reproducibility: float  # Crash reproduction likelihood (0.0-1.0)
    sanitizer_quality: float  # Quality of sanitizer output (0.0-1.0)
    triage_completeness: float  # Completeness of triage information (0.0-1.0)
    
    @property
    def overall_security_score(self) -> float:
        """Calculate overall security quality score (0.0-100.0)."""
        weights = {
            "vulnerability_indicators": 0.15,
            "exploit_complexity": 0.10,
            "defensive_value": 0.25,
            "crash_reproducibility": 0.20,
            "sanitizer_quality": 0.15,
            "triage_completeness": 0.15,
        }
        
        score = (
            min(1.0, self.vulnerability_indicators / 5.0) * weights["vulnerability_indicators"] +
            self.exploit_complexity * weights["exploit_complexity"] +
            self.defensive_value * weights["defensive_value"] +
            self.crash_reproducibility * weights["crash_reproducibility"] +
            self.sanitizer_quality * weights["sanitizer_quality"] +
            self.triage_completeness * weights["triage_completeness"]
        )
        
        return score * 100.0


class SecurityQualityScorer(DatasetQualityScorer):
    """Enhanced quality scorer with security-specific metrics."""
    
    def __init__(
        self,
        min_record_score: int = 60,  # Lower threshold for security content
        min_average_score: int = 70,
        max_failed_ratio: float = 0.15,  # Allow more variance
        min_records: int = 1,
        security_weight: float = 0.5,  # Weight of security metrics vs base metrics
    ) -> None:
        """Initialize security quality scorer.
        
        Args:
            min_record_score: Minimum score per record (0-100)
            min_average_score: Minimum average score across dataset
            max_failed_ratio: Maximum ratio of failed records allowed
            min_records: Minimum number of records required
            security_weight: How much to weight security metrics (0.0-1.0)
        """
        super().__init__(min_record_score, min_average_score, max_failed_ratio, min_records)
        self.security_weight = security_weight
        
        # Security-specific keywords
        self.vulnerability_keywords = {
            "buffer overflow", "heap overflow", "stack overflow",
            "use-after-free", "double-free", "memory leak",
            "integer overflow", "format string", "injection",
            "xss", "csrf", "sql injection", "command injection",
            "race condition", "null pointer", "segfault",
            "exploit", "vulnerability", "CVE", "crash",
        }
        
        self.defensive_keywords = {
            "mitigation", "patch", "fix", "sanitizer",
            "validation", "bounds check", "safe", "secure",
            "defense", "protection", "hardening", "firewall",
        }
    
    def score_record(self, record: dict[str, Any], index: int) -> RecordQualityScore:
        """Score a record with security-specific metrics.
        
        Args:
            record: Dataset record to score
            index: Record index in dataset
            
        Returns:
            RecordQualityScore with security metrics added
        """
        # Get base score from parent class
        base_score = super().score_record(record, index)
        
        # Calculate security-specific metrics
        security_metrics = self._calculate_security_metrics(record)
        
        # Combine base score with security score
        combined_score = (
            base_score.score * (1.0 - self.security_weight) +
            security_metrics.overall_security_score * self.security_weight
        )
        
        # Add security metadata to record
        metadata = record.get("metadata", {})
        metadata["security_metrics"] = {
            "vulnerability_indicators": security_metrics.vulnerability_indicators,
            "exploit_complexity": security_metrics.exploit_complexity,
            "defensive_value": security_metrics.defensive_value,
            "crash_reproducibility": security_metrics.crash_reproducibility,
            "sanitizer_quality": security_metrics.sanitizer_quality,
            "triage_completeness": security_metrics.triage_completeness,
            "overall_security_score": security_metrics.overall_security_score,
        }
        
        # Update the quality score
        return replace(
            base_score,
            score=int(combined_score),
        )
    
    def _calculate_security_metrics(self, record: dict[str, Any]) -> SecurityQualityMetrics:
        """Calculate security-specific quality metrics for a record."""
        text = record.get("text", "").lower()
        metadata = record.get("metadata", {})
        
        # Count vulnerability indicators
        vuln_count = sum(1 for keyword in self.vulnerability_keywords if keyword in text)
        
        # Estimate exploit complexity (presence of technical details)
        complexity_indicators = [
            "stack trace", "assembly", "register", "memory address",
            "poc", "proof of concept", "reproducer", "exploit code",
        ]
        complexity = sum(1 for indicator in complexity_indicators if indicator in text) / len(complexity_indicators)
        
        # Measure defensive value (mitigation/fix information)
        defensive_count = sum(1 for keyword in self.defensive_keywords if keyword in text)
        defensive_value = min(1.0, defensive_count / 3.0)
        
        # Assess crash reproducibility
        reproducibility = 0.0
        if "crash_signature" in metadata:
            reproducibility = 0.7
        if any(keyword in text for keyword in ["reproducible", "reproducer", "poc"]):
            reproducibility = min(1.0, reproducibility + 0.3)
        
        # Evaluate sanitizer quality
        sanitizer_quality = 0.0
        if "sanitizer_output" in metadata or any(san in text for san in ["addresssanitizer", "memorysanitizer", "asan", "msan"]):
            sanitizer_quality = 0.5
        if "stack trace" in text:
            sanitizer_quality = min(1.0, sanitizer_quality + 0.3)
        if "memory address" in text or re.search(r"0x[0-9a-f]{8,}", text):
            sanitizer_quality = min(1.0, sanitizer_quality + 0.2)
        
        # Measure triage completeness
        triage_elements = [
            "severity" in metadata or any(sev in text for sev in ["critical", "high", "medium", "low"]),
            "crash_type" in metadata or vuln_count > 0,
            "reproducible" in text or reproducibility > 0.5,
            "impact" in text or "affect" in text,
            "mitigation" in text or defensive_count > 0,
        ]
        triage_completeness = sum(triage_elements) / len(triage_elements)
        
        return SecurityQualityMetrics(
            vulnerability_indicators=vuln_count,
            exploit_complexity=complexity,
            defensive_value=defensive_value,
            crash_reproducibility=reproducibility,
            sanitizer_quality=sanitizer_quality,
            triage_completeness=triage_completeness,
        )
    
    def score_dataset(self, dataset_path: str | Path) -> SecurityDatasetReport:
        """Score entire dataset with security-specific metrics.
        
        Args:
            dataset_path: Path to JSONL dataset file
            
        Returns:
            SecurityDatasetReport with security-enhanced scoring
        """
        # Use parent class scoring
        base_report = super().score_dataset(dataset_path)
        
        # Add security-specific summary statistics
        path = Path(dataset_path)
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        
        # Calculate security-specific aggregates
        total_vuln_indicators = 0
        total_crash_reproducible = 0
        total_with_sanitizer = 0
        
        for record in records:
            metadata = record.get("metadata", {})
            security_metrics = metadata.get("security_metrics", {})
            
            total_vuln_indicators += security_metrics.get("vulnerability_indicators", 0)
            if security_metrics.get("crash_reproducibility", 0) >= 0.7:
                total_crash_reproducible += 1
            if security_metrics.get("sanitizer_quality", 0) >= 0.5:
                total_with_sanitizer += 1
        
        # Create security statistics
        security_stats = {
            "total_vulnerability_indicators": total_vuln_indicators,
            "avg_indicators_per_record": total_vuln_indicators / len(records) if records else 0,
            "crash_reproducible_count": total_crash_reproducible,
            "crash_reproducible_ratio": total_crash_reproducible / len(records) if records else 0,
            "sanitizer_coverage_count": total_with_sanitizer,
            "sanitizer_coverage_ratio": total_with_sanitizer / len(records) if records else 0,
        }
        
        # Return SecurityDatasetReport with security stats
        return SecurityDatasetReport(
            dataset_path=base_report.dataset_path,
            record_count=base_report.record_count,
            average_score=base_report.average_score,
            min_score=base_report.min_score,
            passed_records=base_report.passed_records,
            failed_records=base_report.failed_records,
            gates=base_report.gates,
            records=base_report.records,
            issues=base_report.issues,
            security_stats=security_stats,
        )


def score_fuzzing_dataset(
    dataset_path: str | Path,
    output_json: str | Path | None = None,
    output_markdown: str | Path | None = None,
) -> DatasetQualityReport:
    """Convenience function to score a fuzzing dataset with security metrics.
    
    Args:
        dataset_path: Path to JSONL dataset
        output_json: Optional path to write JSON report
        output_markdown: Optional path to write Markdown report
        
    Returns:
        DatasetQualityReport with security scoring
    """
    scorer = SecurityQualityScorer(
        min_record_score=60,
        min_average_score=70,
        security_weight=0.6,  # Emphasize security metrics
    )
    
    report = scorer.score_dataset(dataset_path)
    
    if output_json or output_markdown:
        json_path = Path(output_json) if output_json else Path("quality-report.json")
        md_path = Path(output_markdown) if output_markdown else None
        scorer.write_report(report, json_path, md_path)
    
    return report
