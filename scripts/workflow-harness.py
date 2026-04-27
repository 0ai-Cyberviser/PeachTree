#!/usr/bin/env python3
"""
PeachTree Workflow Harness - Integrated Monitor-Audit-Review-Test-Log-Learn-Repeat Cycle

Orchestrates the complete dataset lifecycle for continuous improvement:
1. MONITOR - Track dataset quality metrics
2. AUDIT - Validate dataset integrity and compliance
3. REVIEW - Generate reports and identify issues
4. TEST - Run evaluation tests on trained models
5. LOG - Record all operations and results
6. LEARN - Analyze trends and optimize
7. REPEAT - Schedule next cycle

Usage:
    python scripts/workflow-harness.py --config config/workflow-config.yml
    python scripts/workflow-harness.py --cycle monitor-audit-review
    python scripts/workflow-harness.py --full-cycle
"""

import json
import yaml
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class CyclePhase(Enum):
    """Workflow cycle phases"""
    MONITOR = "monitor"
    AUDIT = "audit"
    REVIEW = "review"
    TEST = "test"
    LOG = "log"
    LEARN = "learn"
    REPEAT = "repeat"


@dataclass
class CycleResult:
    """Result of a single cycle phase"""
    phase: str
    status: str  # success, warning, failure
    timestamp: str
    duration_seconds: float
    metrics: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    artifacts: List[str]


@dataclass
class WorkflowState:
    """Current state of workflow execution"""
    cycle_id: str
    start_time: str
    phases_completed: List[str]
    phases_failed: List[str]
    current_phase: Optional[str]
    overall_status: str
    results: List[CycleResult]


class WorkflowHarness:
    """Orchestrates the complete dataset lifecycle workflow"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.state_dir = Path(self.config.get("state_dir", "workflow-state"))
        self.state_dir.mkdir(exist_ok=True)
        
        self.cycle_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.state = WorkflowState(
            cycle_id=self.cycle_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            phases_completed=[],
            phases_failed=[],
            current_phase=None,
            overall_status="running",
            results=[]
        )
        
        self._setup_logging()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load workflow configuration"""
        if Path(config_path).exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                "dataset_path": "data/datasets/multi-org-security-training.jsonl",
                "manifest_path": "data/manifests/multi-org-build-manifest.json",
                "quality_threshold": 0.70,
                "duplicate_threshold": 0.05,
                "state_dir": "workflow-state",
                "log_dir": "logs/workflow",
                "phases": {
                    "monitor": {"enabled": True, "timeout": 300},
                    "audit": {"enabled": True, "timeout": 300},
                    "review": {"enabled": True, "timeout": 300},
                    "test": {"enabled": True, "timeout": 600},
                    "log": {"enabled": True, "timeout": 60},
                    "learn": {"enabled": True, "timeout": 300},
                    "repeat": {"enabled": True, "timeout": 60}
                }
            }
    
    def _setup_logging(self):
        """Configure logging for workflow"""
        log_dir = Path(self.config.get("log_dir", "logs/workflow"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"workflow-{self.cycle_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"=== Workflow Harness Started - Cycle {self.cycle_id} ===")
    
    def run_full_cycle(self) -> bool:
        """Execute complete workflow cycle"""
        self.logger.info("Starting full workflow cycle")
        
        phases = [
            (CyclePhase.MONITOR, self.phase_monitor),
            (CyclePhase.AUDIT, self.phase_audit),
            (CyclePhase.REVIEW, self.phase_review),
            (CyclePhase.TEST, self.phase_test),
            (CyclePhase.LOG, self.phase_log),
            (CyclePhase.LEARN, self.phase_learn),
            (CyclePhase.REPEAT, self.phase_repeat)
        ]
        
        all_success = True
        
        for phase, phase_func in phases:
            if not self._is_phase_enabled(phase.value):
                self.logger.info(f"Phase {phase.value} is disabled, skipping")
                continue
            
            self.state.current_phase = phase.value
            self._save_state()
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Phase: {phase.value.upper()}")
            self.logger.info(f"{'='*60}")
            
            start_time = datetime.now(timezone.utc)
            
            try:
                result = phase_func()
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                result.duration_seconds = duration
                
                self.state.results.append(result)
                
                if result.status == "success":
                    self.state.phases_completed.append(phase.value)
                    self.logger.info(f"✅ Phase {phase.value} completed successfully")
                elif result.status == "warning":
                    self.state.phases_completed.append(phase.value)
                    self.logger.warning(f"⚠️  Phase {phase.value} completed with warnings")
                else:
                    self.state.phases_failed.append(phase.value)
                    self.logger.error(f"❌ Phase {phase.value} failed")
                    all_success = False
                    
                    if not self.config.get("continue_on_failure", True):
                        break
                        
            except Exception as e:
                self.logger.error(f"❌ Phase {phase.value} raised exception: {e}")
                self.state.phases_failed.append(phase.value)
                all_success = False
                
                if not self.config.get("continue_on_failure", True):
                    break
        
        self.state.overall_status = "success" if all_success else "partial"
        self.state.current_phase = None
        self._save_state()
        
        self._generate_summary()
        
        return all_success
    
    def _is_phase_enabled(self, phase: str) -> bool:
        """Check if phase is enabled in config"""
        return self.config.get("phases", {}).get(phase, {}).get("enabled", True)
    
    # ========================================================================
    # PHASE 1: MONITOR
    # ========================================================================
    
    def phase_monitor(self) -> CycleResult:
        """Monitor dataset quality metrics"""
        self.logger.info("Running quality monitoring...")
        
        dataset_path = self.config["dataset_path"]
        
        # Import monitor-quality.py functionality
        sys.path.insert(0, str(Path(__file__).parent))
        from monitor_quality import DatasetQualityMonitor
        
        monitor = DatasetQualityMonitor(
            dataset_path,
            quality_threshold=self.config.get("quality_threshold", 0.70)
        )
        
        metrics = monitor.analyze()
        
        # Determine status
        status = "success"
        issues = []
        recommendations = []
        
        if metrics.duplicate_rate > self.config.get("duplicate_threshold", 0.05):
            status = "warning"
            issues.append(f"High duplicate rate: {metrics.duplicate_rate:.1%}")
            recommendations.append("Run deduplication: peachtree dedup --dataset ...")
        
        if metrics.avg_quality_score < self.config.get("quality_threshold", 0.70):
            status = "warning"
            issues.append(f"Low quality score: {metrics.avg_quality_score:.3f}")
            recommendations.append("Review source selection and filtering")
        
        if not metrics.safety_gates_passed:
            status = "failure"
            issues.extend(metrics.issues)
            recommendations.append("Fix safety gate violations immediately")
        
        # Save metrics
        metrics_file = self.state_dir / f"metrics-{self.cycle_id}.json"
        monitor.save_metrics(str(metrics_file))
        
        return CycleResult(
            phase="monitor",
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,  # Will be set by caller
            metrics={
                "record_count": metrics.record_count,
                "quality_score": metrics.avg_quality_score,
                "duplicate_rate": metrics.duplicate_rate,
                "provenance_coverage": metrics.provenance_coverage
            },
            issues=issues,
            recommendations=recommendations,
            artifacts=[str(metrics_file)]
        )
    
    # ========================================================================
    # PHASE 2: AUDIT
    # ========================================================================
    
    def phase_audit(self) -> CycleResult:
        """Audit dataset integrity and compliance"""
        self.logger.info("Running dataset audit...")
        
        dataset_path = self.config["dataset_path"]
        
        # Run PeachTree audit command
        audit_output = self._run_command([
            "peachtree", "audit",
            "--dataset", dataset_path
        ])
        
        # Parse audit results
        issues = []
        recommendations = []
        status = "success"
        
        if "duplicates: 0" not in audit_output.lower():
            status = "warning"
            issues.append("Duplicates detected in dataset")
            recommendations.append("Run deduplication")
        
        if "has_provenance: true" not in audit_output.lower():
            status = "failure"
            issues.append("Missing provenance in some records")
            recommendations.append("Rebuild dataset with proper provenance")
        
        audit_file = self.state_dir / f"audit-{self.cycle_id}.txt"
        audit_file.write_text(audit_output)
        
        return CycleResult(
            phase="audit",
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={"audit_passed": status == "success"},
            issues=issues,
            recommendations=recommendations,
            artifacts=[str(audit_file)]
        )
    
    # ========================================================================
    # PHASE 3: REVIEW
    # ========================================================================
    
    def phase_review(self) -> CycleResult:
        """Generate review reports and identify issues"""
        self.logger.info("Generating review reports...")
        
        dataset_path = self.config["dataset_path"]
        manifest_path = self.config["manifest_path"]
        
        issues = []
        recommendations = []
        artifacts = []
        
        # Generate quality report
        sys.path.insert(0, str(Path(__file__).parent))
        from monitor_quality import DatasetQualityMonitor
        
        monitor = DatasetQualityMonitor(dataset_path)
        metrics = monitor.analyze()
        
        report_file = self.state_dir / f"quality-report-{self.cycle_id}.md"
        report = monitor.generate_report(str(report_file))
        artifacts.append(str(report_file))
        
        # Generate lineage report
        lineage_output = self._run_command([
            "peachtree", "lineage",
            "--dataset", dataset_path,
            "--manifest", manifest_path,
            "--format", "markdown"
        ], check=False)
        
        if lineage_output:
            lineage_file = self.state_dir / f"lineage-{self.cycle_id}.md"
            lineage_file.write_text(lineage_output)
            artifacts.append(str(lineage_file))
        
        # Analyze trends if previous metrics exist
        previous_metrics = self._find_previous_metrics()
        if previous_metrics:
            comparison = monitor.compare_with_baseline(previous_metrics)
            
            if comparison.get("degraded"):
                issues.append("Dataset quality has degraded since last cycle")
                recommendations.append("Investigate quality degradation causes")
            elif comparison.get("improved"):
                self.logger.info("✅ Dataset quality has improved!")
        
        status = "success" if len(issues) == 0 else "warning"
        
        return CycleResult(
            phase="review",
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={
                "reports_generated": len(artifacts),
                "quality_trend": "improved" if previous_metrics and comparison.get("improved") else "stable"
            },
            issues=issues,
            recommendations=recommendations,
            artifacts=artifacts
        )
    
    # ========================================================================
    # PHASE 4: TEST
    # ========================================================================
    
    def phase_test(self) -> CycleResult:
        """Run evaluation tests"""
        self.logger.info("Running evaluation tests...")
        
        issues = []
        recommendations = []
        artifacts = []
        
        # Run Python tests
        test_output = self._run_command([
            "python", "-m", "pytest",
            "tests/", "-v", "--tb=short"
        ], check=False)
        
        test_file = self.state_dir / f"test-results-{self.cycle_id}.txt"
        test_file.write_text(test_output)
        artifacts.append(str(test_file))
        
        # Parse test results
        if "failed" in test_output.lower() or "error" in test_output.lower():
            issues.append("Some tests failed")
            recommendations.append("Fix failing tests before deployment")
            status = "failure"
        elif "warning" in test_output.lower():
            issues.append("Tests passed with warnings")
            status = "warning"
        else:
            status = "success"
        
        # Run evaluation if eval dataset exists
        eval_dataset = Path("data/eval/hancock-eval-set.jsonl")
        if eval_dataset.exists():
            self.logger.info("Running Hancock evaluation...")
            # Placeholder for actual model evaluation
            # Would integrate with examples/hancock_integration.py
            self.logger.info("Evaluation tests would run here")
        
        return CycleResult(
            phase="test",
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={"tests_passed": status in ["success", "warning"]},
            issues=issues,
            recommendations=recommendations,
            artifacts=artifacts
        )
    
    # ========================================================================
    # PHASE 5: LOG
    # ========================================================================
    
    def phase_log(self) -> CycleResult:
        """Log all operations and results"""
        self.logger.info("Logging workflow results...")
        
        # Consolidate all logs
        log_summary = {
            "cycle_id": self.cycle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phases": [asdict(r) for r in self.state.results],
            "overall_status": self.state.overall_status,
            "dataset": self.config["dataset_path"]
        }
        
        log_file = self.state_dir / f"cycle-summary-{self.cycle_id}.json"
        log_file.write_text(json.dumps(log_summary, indent=2))
        
        # Archive to permanent log storage
        permanent_log_dir = Path("logs/workflow/archive")
        permanent_log_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(log_file, permanent_log_dir / log_file.name)
        
        return CycleResult(
            phase="log",
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={"logs_archived": True},
            issues=[],
            recommendations=[],
            artifacts=[str(log_file)]
        )
    
    # ========================================================================
    # PHASE 6: LEARN
    # ========================================================================
    
    def phase_learn(self) -> CycleResult:
        """Analyze trends and optimize"""
        self.logger.info("Analyzing trends and learning...")
        
        # Load historical cycle data
        historical_cycles = self._load_historical_cycles()
        
        insights = []
        recommendations = []
        
        if len(historical_cycles) >= 3:
            # Analyze quality trends
            quality_scores = [
                c.get("phases", [{}])[0].get("metrics", {}).get("quality_score", 0)
                for c in historical_cycles[-5:]
            ]
            
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                trend = "improving" if quality_scores[-1] > avg_quality else "declining"
                
                insights.append(f"Quality trend: {trend} (avg: {avg_quality:.3f})")
                
                if trend == "declining":
                    recommendations.append("Investigate quality decline - review source selection")
            
            # Analyze duplicate trends
            duplicate_rates = [
                c.get("phases", [{}])[0].get("metrics", {}).get("duplicate_rate", 0)
                for c in historical_cycles[-5:]
            ]
            
            if duplicate_rates and max(duplicate_rates) > 0.03:
                insights.append("Duplicate rate increasing")
                recommendations.append("Schedule deduplication run")
        
        # Learn from failures
        all_issues = []
        for result in self.state.results:
            all_issues.extend(result.issues)
        
        if all_issues:
            insights.append(f"Total issues this cycle: {len(all_issues)}")
            
            # Categorize common issues
            issue_keywords = {}
            for issue in all_issues:
                for keyword in ["duplicate", "quality", "provenance", "license"]:
                    if keyword in issue.lower():
                        issue_keywords[keyword] = issue_keywords.get(keyword, 0) + 1
            
            for keyword, count in issue_keywords.items():
                insights.append(f"Common issue: {keyword} ({count} occurrences)")
                recommendations.append(f"Focus on improving {keyword} in next cycle")
        
        learning_file = self.state_dir / f"learning-{self.cycle_id}.json"
        learning_file.write_text(json.dumps({
            "insights": insights,
            "recommendations": recommendations,
            "historical_cycles_analyzed": len(historical_cycles)
        }, indent=2))
        
        return CycleResult(
            phase="learn",
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={
                "insights_generated": len(insights),
                "historical_cycles": len(historical_cycles)
            },
            issues=[],
            recommendations=recommendations,
            artifacts=[str(learning_file)]
        )
    
    # ========================================================================
    # PHASE 7: REPEAT
    # ========================================================================
    
    def phase_repeat(self) -> CycleResult:
        """Schedule next cycle"""
        self.logger.info("Scheduling next workflow cycle...")
        
        # Determine next run time based on config
        schedule = self.config.get("schedule", "daily")
        
        if schedule == "hourly":
            next_run = "in 1 hour"
        elif schedule == "daily":
            next_run = "tomorrow at same time"
        elif schedule == "weekly":
            next_run = "in 7 days"
        else:
            next_run = schedule
        
        # Create next cycle marker
        next_cycle_file = self.state_dir / "next-cycle.txt"
        next_cycle_file.write_text(f"Next cycle scheduled: {next_run}\n")
        
        return CycleResult(
            phase="repeat",
            status="success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            metrics={"next_cycle_scheduled": True},
            issues=[],
            recommendations=[f"Next cycle will run: {next_run}"],
            artifacts=[str(next_cycle_file)]
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _run_command(self, cmd: List[str], check: bool = True) -> str:
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                timeout=self.config.get("phases", {}).get(cmd[1] if len(cmd) > 1 else "default", {}).get("timeout", 300)
            )
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout + e.stderr
        except subprocess.TimeoutExpired:
            return "Command timed out"
    
    def _save_state(self):
        """Save current workflow state"""
        state_file = self.state_dir / f"state-{self.cycle_id}.json"
        state_dict = asdict(self.state)
        state_file.write_text(json.dumps(state_dict, indent=2, default=str))
    
    def _find_previous_metrics(self) -> Optional[str]:
        """Find most recent previous metrics file"""
        metrics_files = sorted(self.state_dir.glob("metrics-*.json"))
        if len(metrics_files) >= 2:
            return str(metrics_files[-2])
        return None
    
    def _load_historical_cycles(self) -> List[Dict]:
        """Load historical cycle summaries"""
        summaries = []
        for summary_file in sorted(self.state_dir.glob("cycle-summary-*.json")):
            try:
                summaries.append(json.loads(summary_file.read_text()))
            except:
                pass
        return summaries
    
    def _generate_summary(self):
        """Generate final workflow summary"""
        self.logger.info("\n" + "="*60)
        self.logger.info("WORKFLOW CYCLE SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Cycle ID: {self.cycle_id}")
        self.logger.info(f"Status: {self.state.overall_status.upper()}")
        self.logger.info(f"Phases Completed: {len(self.state.phases_completed)}/{len(self.state.results)}")
        
        if self.state.phases_failed:
            self.logger.warning(f"Phases Failed: {', '.join(self.state.phases_failed)}")
        
        self.logger.info("\nPhase Results:")
        for result in self.state.results:
            status_icon = "✅" if result.status == "success" else "⚠️" if result.status == "warning" else "❌"
            self.logger.info(f"  {status_icon} {result.phase.upper()}: {result.status} ({result.duration_seconds:.1f}s)")
            
            if result.issues:
                for issue in result.issues:
                    self.logger.info(f"      - {issue}")
        
        self.logger.info("\n" + "="*60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PeachTree Workflow Harness")
    parser.add_argument("--config", default="config/workflow-config.yml",
                        help="Path to workflow configuration file")
    parser.add_argument("--cycle", choices=["monitor", "audit", "review", "test", "log", "learn", "repeat"],
                        help="Run single cycle phase")
    parser.add_argument("--full-cycle", action="store_true",
                        help="Run complete workflow cycle")
    
    args = parser.parse_args()
    
    harness = WorkflowHarness(args.config)
    
    if args.cycle:
        # Run single phase
        phase_map = {
            "monitor": harness.phase_monitor,
            "audit": harness.phase_audit,
            "review": harness.phase_review,
            "test": harness.phase_test,
            "log": harness.phase_log,
            "learn": harness.phase_learn,
            "repeat": harness.phase_repeat
        }
        
        result = phase_map[args.cycle]()
        print(json.dumps(asdict(result), indent=2, default=str))
        sys.exit(0 if result.status in ["success", "warning"] else 1)
    
    elif args.full_cycle:
        # Run full cycle
        success = harness.run_full_cycle()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
