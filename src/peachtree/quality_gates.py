"""
PeachTree Quality Gates

Pre-commit quality checks and CI/CD integration gates for dataset validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import json


@dataclass
class GateRule:
    """Single quality gate rule"""
    rule_id: str
    rule_name: str
    rule_type: str  # must_pass, should_pass, warn_only
    threshold: float = 0.0
    message: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "threshold": self.threshold,
            "message": self.message,
        }


@dataclass
class GateCheckResult:
    """Result of a single gate check"""
    rule_id: str
    passed: bool
    actual_value: float
    threshold: float
    message: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "actual_value": self.actual_value,
            "threshold": self.threshold,
            "message": self.message,
        }


@dataclass
class GateEvaluationReport:
    """Complete gate evaluation report"""
    dataset_id: str
    timestamp: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    warnings: int
    gate_passed: bool
    results: list[GateCheckResult] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "timestamp": self.timestamp,
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "gate_passed": self.gate_passed,
            "pass_rate": (self.passed_rules / self.total_rules * 100) if self.total_rules > 0 else 0,
            "results": [r.to_dict() for r in self.results],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        status = "✅ PASSED" if self.gate_passed else "❌ FAILED"
        
        lines = [
            f"# Quality Gate Report",
            f"",
            f"**Dataset:** {self.dataset_id}  ",
            f"**Timestamp:** {self.timestamp}  ",
            f"**Status:** {status}  ",
            f"**Pass Rate:** {self.passed_rules}/{self.total_rules} ({self.passed_rules / self.total_rules * 100:.1f}%)  ",
            f"",
            "## Results",
            "",
            "| Rule | Status | Actual | Threshold | Message |",
            "|------|--------|--------|-----------|---------|",
        ]
        
        for result in self.results:
            status_icon = "✅" if result.passed else "❌"
            lines.append(
                f"| {result.rule_id} | {status_icon} | {result.actual_value:.2f} | {result.threshold:.2f} | {result.message} |"
            )
        
        return "\n".join(lines)


@dataclass
class QualityGateConfig:
    """Quality gate configuration"""
    gate_id: str
    gate_name: str
    rules: list[GateRule] = field(default_factory=list)
    fail_on_warning: bool = False
    
    def add_rule(self, rule: GateRule) -> None:
        """Add rule to gate"""
        self.rules.append(rule)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "rules": [r.to_dict() for r in self.rules],
            "fail_on_warning": self.fail_on_warning,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class QualityGateEngine:
    """Execute quality gates for dataset validation"""
    
    def __init__(self):
        """Initialize quality gate engine"""
        self.check_functions: dict[str, Callable] = {
            "min_quality_score": self._check_min_quality_score,
            "min_record_count": self._check_min_record_count,
            "max_duplicate_rate": self._check_max_duplicate_rate,
            "min_metadata_coverage": self._check_min_metadata_coverage,
            "max_empty_content_rate": self._check_max_empty_content_rate,
            "min_avg_content_length": self._check_min_avg_content_length,
        }
    
    def _check_min_quality_score(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check minimum average quality score"""
        total_score = 0.0
        count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    total_score += record.get("quality_score", 0.0)
                    count += 1
                except json.JSONDecodeError:
                    continue
        
        avg_score = total_score / count if count > 0 else 0.0
        return (avg_score >= threshold, avg_score)
    
    def _check_min_record_count(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check minimum record count"""
        count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    count += 1
        
        return (count >= threshold, float(count))
    
    def _check_max_duplicate_rate(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check maximum duplicate rate"""
        seen_content: set[str] = set()
        total_count = 0
        duplicate_count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_count += 1
                
                try:
                    record = json.loads(line)
                    content = record.get("content", "").strip()
                    
                    if content in seen_content:
                        duplicate_count += 1
                    else:
                        seen_content.add(content)
                
                except json.JSONDecodeError:
                    continue
        
        duplicate_rate = duplicate_count / total_count if total_count > 0 else 0.0
        return (duplicate_rate <= threshold, duplicate_rate)
    
    def _check_min_metadata_coverage(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check minimum metadata coverage"""
        total_count = 0
        with_metadata = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_count += 1
                
                try:
                    record = json.loads(line)
                    
                    if "source_document" in record and record["source_document"]:
                        with_metadata += 1
                
                except json.JSONDecodeError:
                    continue
        
        coverage = with_metadata / total_count if total_count > 0 else 0.0
        return (coverage >= threshold, coverage)
    
    def _check_max_empty_content_rate(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check maximum empty content rate"""
        total_count = 0
        empty_count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_count += 1
                
                try:
                    record = json.loads(line)
                    content = record.get("content", "").strip()
                    
                    if not content:
                        empty_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        empty_rate = empty_count / total_count if total_count > 0 else 0.0
        return (empty_rate <= threshold, empty_rate)
    
    def _check_min_avg_content_length(self, dataset_path: Path, threshold: float) -> tuple[bool, float]:
        """Check minimum average content length"""
        total_length = 0
        count = 0
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    content = record.get("content", "")
                    total_length += len(content)
                    count += 1
                
                except json.JSONDecodeError:
                    continue
        
        avg_length = total_length / count if count > 0 else 0.0
        return (avg_length >= threshold, avg_length)
    
    def execute_rule(
        self,
        rule: GateRule,
        dataset_path: Path | str,
    ) -> GateCheckResult:
        """
        Execute single gate rule
        
        Args:
            rule: Gate rule to execute
            dataset_path: Dataset to check
        
        Returns:
            GateCheckResult
        """
        dataset_path = Path(dataset_path)
        
        if rule.rule_id not in self.check_functions:
            return GateCheckResult(
                rule_id=rule.rule_id,
                passed=False,
                actual_value=0.0,
                threshold=rule.threshold,
                message=f"Unknown rule: {rule.rule_id}",
            )
        
        check_func = self.check_functions[rule.rule_id]
        passed, actual_value = check_func(dataset_path, rule.threshold)
        
        message = rule.message or ("Passed" if passed else "Failed")
        
        return GateCheckResult(
            rule_id=rule.rule_id,
            passed=passed,
            actual_value=actual_value,
            threshold=rule.threshold,
            message=message,
        )
    
    def evaluate_gate(
        self,
        config: QualityGateConfig,
        dataset_path: Path | str,
        dataset_id: str = "dataset",
    ) -> GateEvaluationReport:
        """
        Evaluate all rules in quality gate
        
        Args:
            config: Quality gate configuration
            dataset_path: Dataset to evaluate
            dataset_id: Dataset identifier
        
        Returns:
            GateEvaluationReport with all results
        """
        dataset_path = Path(dataset_path)
        
        results = []
        passed_count = 0
        failed_count = 0
        warning_count = 0
        
        for rule in config.rules:
            result = self.execute_rule(rule, dataset_path)
            results.append(result)
            
            if result.passed:
                passed_count += 1
            else:
                if rule.rule_type == "must_pass":
                    failed_count += 1
                elif rule.rule_type == "should_pass":
                    failed_count += 1
                else:  # warn_only
                    warning_count += 1
        
        # Determine if gate passed
        gate_passed = failed_count == 0
        if config.fail_on_warning and warning_count > 0:
            gate_passed = False
        
        return GateEvaluationReport(
            dataset_id=dataset_id,
            timestamp=datetime.utcnow().isoformat(),
            total_rules=len(config.rules),
            passed_rules=passed_count,
            failed_rules=failed_count,
            warnings=warning_count,
            gate_passed=gate_passed,
            results=results,
        )
    
    def create_standard_gate(
        self,
        gate_id: str = "standard_quality_gate",
        strict: bool = False,
    ) -> QualityGateConfig:
        """
        Create standard quality gate with common rules
        
        Args:
            gate_id: Gate identifier
            strict: Use strict thresholds
        
        Returns:
            QualityGateConfig
        """
        config = QualityGateConfig(
            gate_id=gate_id,
            gate_name="Standard Quality Gate",
        )
        
        if strict:
            # Strict thresholds
            config.add_rule(GateRule(
                rule_id="min_quality_score",
                rule_name="Minimum Quality Score",
                rule_type="must_pass",
                threshold=80.0,
                message="Average quality score must be >= 80",
            ))
            config.add_rule(GateRule(
                rule_id="min_record_count",
                rule_name="Minimum Record Count",
                rule_type="must_pass",
                threshold=100.0,
                message="Dataset must have >= 100 records",
            ))
            config.add_rule(GateRule(
                rule_id="max_duplicate_rate",
                rule_name="Maximum Duplicate Rate",
                rule_type="must_pass",
                threshold=0.05,
                message="Duplicate rate must be <= 5%",
            ))
            config.add_rule(GateRule(
                rule_id="min_metadata_coverage",
                rule_name="Minimum Metadata Coverage",
                rule_type="must_pass",
                threshold=0.90,
                message="Metadata coverage must be >= 90%",
            ))
        else:
            # Standard thresholds
            config.add_rule(GateRule(
                rule_id="min_quality_score",
                rule_name="Minimum Quality Score",
                rule_type="must_pass",
                threshold=70.0,
                message="Average quality score must be >= 70",
            ))
            config.add_rule(GateRule(
                rule_id="min_record_count",
                rule_name="Minimum Record Count",
                rule_type="should_pass",
                threshold=50.0,
                message="Dataset should have >= 50 records",
            ))
            config.add_rule(GateRule(
                rule_id="max_duplicate_rate",
                rule_name="Maximum Duplicate Rate",
                rule_type="should_pass",
                threshold=0.10,
                message="Duplicate rate should be <= 10%",
            ))
            config.add_rule(GateRule(
                rule_id="min_metadata_coverage",
                rule_name="Minimum Metadata Coverage",
                rule_type="warn_only",
                threshold=0.80,
                message="Metadata coverage warning at < 80%",
            ))
        
        return config
    
    def create_ci_gate(self) -> QualityGateConfig:
        """Create CI/CD-friendly gate with fast checks"""
        config = QualityGateConfig(
            gate_id="ci_quality_gate",
            gate_name="CI/CD Quality Gate",
        )
        
        config.add_rule(GateRule(
            rule_id="min_record_count",
            rule_name="Minimum Records",
            rule_type="must_pass",
            threshold=10.0,
            message="Must have at least 10 records",
        ))
        
        config.add_rule(GateRule(
            rule_id="max_empty_content_rate",
            rule_name="No Empty Content",
            rule_type="must_pass",
            threshold=0.0,
            message="No records with empty content allowed",
        ))
        
        config.add_rule(GateRule(
            rule_id="min_metadata_coverage",
            rule_name="Metadata Required",
            rule_type="must_pass",
            threshold=1.0,
            message="All records must have metadata",
        ))
        
        return config
    
    def save_config(self, config: QualityGateConfig, output_path: Path | str) -> None:
        """Save gate configuration to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(config.to_json() + "\n", encoding="utf-8")
    
    def load_config(self, config_path: Path | str) -> QualityGateConfig:
        """Load gate configuration from file"""
        with open(config_path) as f:
            data = json.load(f)
        
        config = QualityGateConfig(
            gate_id=data["gate_id"],
            gate_name=data["gate_name"],
            fail_on_warning=data.get("fail_on_warning", False),
        )
        
        for rule_data in data.get("rules", []):
            rule = GateRule(**rule_data)
            config.add_rule(rule)
        
        return config
