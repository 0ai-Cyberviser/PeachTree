"""Dataset monitoring for real-time health checks and alerts.

This module provides comprehensive monitoring capabilities including:
- Real-time health monitoring
- Metric tracking (size, quality, freshness)
- Alert configuration and triggers
- Health check endpoints
- Monitoring dashboards
- Historical trend tracking
- SLA monitoring
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class HealthCheck:
    """A single health check result."""
    
    check_id: str
    check_name: str
    status: str  # healthy, degraded, unhealthy
    message: str
    timestamp: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "value": self.value,
            "threshold": self.threshold,
        }


@dataclass
class HealthStatus:
    """Overall health status."""
    
    overall_status: str  # healthy, degraded, unhealthy
    timestamp: str
    checks: List[HealthCheck] = field(default_factory=list)
    
    def add_check(self, check: HealthCheck) -> None:
        """Add a health check."""
        self.checks.append(check)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "timestamp": self.timestamp,
            "total_checks": len(self.checks),
            "healthy_checks": sum(1 for c in self.checks if c.status == "healthy"),
            "degraded_checks": sum(1 for c in self.checks if c.status == "degraded"),
            "unhealthy_checks": sum(1 for c in self.checks if c.status == "unhealthy"),
            "checks": [c.to_dict() for c in self.checks],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Alert:
    """Monitoring alert."""
    
    alert_id: str
    alert_name: str
    severity: str  # info, warning, critical
    message: str
    timestamp: str
    dataset_id: str
    metric_name: str
    metric_value: float
    threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_name": self.alert_name,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp,
            "dataset_id": self.dataset_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
        }


@dataclass
class MetricSnapshot:
    """Snapshot of dataset metrics at a point in time."""
    
    timestamp: str
    dataset_id: str
    record_count: int
    avg_quality_score: float
    avg_content_length: float
    duplicate_rate: float
    empty_content_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "dataset_id": self.dataset_id,
            "record_count": self.record_count,
            "avg_quality_score": self.avg_quality_score,
            "avg_content_length": self.avg_content_length,
            "duplicate_rate": self.duplicate_rate,
            "empty_content_rate": self.empty_content_rate,
        }


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    
    dataset_id: str
    check_interval_seconds: int = 300  # 5 minutes
    alert_on_quality_drop: bool = True
    quality_threshold: float = 70.0
    alert_on_size_drop: bool = True
    min_record_count: int = 100
    alert_on_freshness: bool = True
    max_age_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "check_interval_seconds": self.check_interval_seconds,
            "alert_on_quality_drop": self.alert_on_quality_drop,
            "quality_threshold": self.quality_threshold,
            "alert_on_size_drop": self.alert_on_size_drop,
            "min_record_count": self.min_record_count,
            "alert_on_freshness": self.alert_on_freshness,
            "max_age_hours": self.max_age_hours,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DatasetMonitor:
    """Real-time dataset monitoring."""
    
    def __init__(self, config: MonitoringConfig) -> None:
        """Initialize the monitor.
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self.metric_history: List[MetricSnapshot] = []
        self.alert_history: List[Alert] = []
    
    def check_health(self, dataset_path: Path) -> HealthStatus:
        """Perform comprehensive health check.
        
        Args:
            dataset_path: Path to dataset file
        
        Returns:
            HealthStatus with all check results
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        status = HealthStatus(overall_status="healthy", timestamp=timestamp)
        
        # Check 1: Dataset exists
        if not dataset_path.exists():
            check = HealthCheck(
                check_id="dataset_exists",
                check_name="Dataset Exists",
                status="unhealthy",
                message=f"Dataset not found: {dataset_path}",
                timestamp=timestamp,
            )
            status.add_check(check)
            status.overall_status = "unhealthy"
            return status
        
        status.add_check(HealthCheck(
            check_id="dataset_exists",
            check_name="Dataset Exists",
            status="healthy",
            message="Dataset file exists",
            timestamp=timestamp,
        ))
        
        # Load metrics
        try:
            metrics = self._compute_metrics(dataset_path)
        except Exception as e:
            check = HealthCheck(
                check_id="metrics_computation",
                check_name="Metrics Computation",
                status="unhealthy",
                message=f"Failed to compute metrics: {e}",
                timestamp=timestamp,
            )
            status.add_check(check)
            status.overall_status = "unhealthy"
            return status
        
        # Check 2: Record count
        count_status = "healthy"
        count_message = f"Record count: {metrics.record_count:,}"
        
        if self.config.alert_on_size_drop and metrics.record_count < self.config.min_record_count:
            count_status = "unhealthy"
            count_message = f"Record count {metrics.record_count} below threshold {self.config.min_record_count}"
        
        status.add_check(HealthCheck(
            check_id="record_count",
            check_name="Record Count",
            status=count_status,
            message=count_message,
            timestamp=timestamp,
            value=float(metrics.record_count),
            threshold=float(self.config.min_record_count),
        ))
        
        if count_status != "healthy":
            status.overall_status = "degraded" if status.overall_status == "healthy" else "unhealthy"
        
        # Check 3: Quality score
        quality_status = "healthy"
        quality_message = f"Avg quality: {metrics.avg_quality_score:.2f}"
        
        if self.config.alert_on_quality_drop and metrics.avg_quality_score < self.config.quality_threshold:
            quality_status = "degraded"
            quality_message = f"Quality {metrics.avg_quality_score:.2f} below threshold {self.config.quality_threshold}"
        
        status.add_check(HealthCheck(
            check_id="quality_score",
            check_name="Quality Score",
            status=quality_status,
            message=quality_message,
            timestamp=timestamp,
            value=metrics.avg_quality_score,
            threshold=self.config.quality_threshold,
        ))
        
        if quality_status != "healthy":
            status.overall_status = "degraded" if status.overall_status == "healthy" else status.overall_status
        
        # Check 4: Freshness
        file_age = self._get_file_age(dataset_path)
        freshness_status = "healthy"
        freshness_message = f"File age: {file_age:.1f} hours"
        
        if self.config.alert_on_freshness and file_age > self.config.max_age_hours:
            freshness_status = "degraded"
            freshness_message = f"File age {file_age:.1f}h exceeds max {self.config.max_age_hours}h"
        
        status.add_check(HealthCheck(
            check_id="freshness",
            check_name="Freshness",
            status=freshness_status,
            message=freshness_message,
            timestamp=timestamp,
            value=file_age,
            threshold=float(self.config.max_age_hours),
        ))
        
        if freshness_status != "healthy":
            status.overall_status = "degraded" if status.overall_status == "healthy" else status.overall_status
        
        # Check 5: Duplicate rate
        dup_status = "healthy"
        dup_message = f"Duplicate rate: {metrics.duplicate_rate:.2f}%"
        
        if metrics.duplicate_rate > 20.0:
            dup_status = "degraded"
            dup_message = f"High duplicate rate: {metrics.duplicate_rate:.2f}%"
        
        status.add_check(HealthCheck(
            check_id="duplicate_rate",
            check_name="Duplicate Rate",
            status=dup_status,
            message=dup_message,
            timestamp=timestamp,
            value=metrics.duplicate_rate,
            threshold=20.0,
        ))
        
        # Store metric snapshot
        self.metric_history.append(metrics)
        
        return status
    
    def _compute_metrics(self, dataset_path: Path) -> MetricSnapshot:
        """Compute current dataset metrics."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        records = []
        with open(dataset_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        
        record_count = len(records)
        
        if record_count == 0:
            return MetricSnapshot(
                timestamp=timestamp,
                dataset_id=self.config.dataset_id,
                record_count=0,
                avg_quality_score=0.0,
                avg_content_length=0.0,
                duplicate_rate=0.0,
                empty_content_rate=0.0,
            )
        
        # Quality scores
        quality_scores = [r.get("quality_score", 0.0) for r in records if "quality_score" in r]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Content lengths
        content_lengths = [len(r.get("content", "")) for r in records]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0.0
        
        # Duplicates
        content_set = set()
        duplicates = 0
        for r in records:
            content = r.get("content", "")
            if content:
                if content in content_set:
                    duplicates += 1
                else:
                    content_set.add(content)
        duplicate_rate = (duplicates / record_count) * 100 if record_count > 0 else 0.0
        
        # Empty content
        empty_count = sum(1 for r in records if not r.get("content", "").strip())
        empty_rate = (empty_count / record_count) * 100 if record_count > 0 else 0.0
        
        return MetricSnapshot(
            timestamp=timestamp,
            dataset_id=self.config.dataset_id,
            record_count=record_count,
            avg_quality_score=avg_quality,
            avg_content_length=avg_length,
            duplicate_rate=duplicate_rate,
            empty_content_rate=empty_rate,
        )
    
    def _get_file_age(self, path: Path) -> float:
        """Get file age in hours."""
        import os
        
        mtime = os.path.getmtime(path)
        age_seconds = time.time() - mtime
        return age_seconds / 3600  # Convert to hours
    
    def check_alerts(self, current_metrics: MetricSnapshot) -> List[Alert]:
        """Check for alert conditions.
        
        Args:
            current_metrics: Current metric snapshot
        
        Returns:
            List of triggered alerts
        """
        alerts = []
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Quality alert
        if self.config.alert_on_quality_drop and current_metrics.avg_quality_score < self.config.quality_threshold:
            alert = Alert(
                alert_id=f"quality_{int(time.time())}",
                alert_name="Low Quality Score",
                severity="warning",
                message=f"Quality score {current_metrics.avg_quality_score:.2f} below threshold {self.config.quality_threshold}",
                timestamp=timestamp,
                dataset_id=self.config.dataset_id,
                metric_name="quality_score",
                metric_value=current_metrics.avg_quality_score,
                threshold=self.config.quality_threshold,
            )
            alerts.append(alert)
            self.alert_history.append(alert)
        
        # Size alert
        if self.config.alert_on_size_drop and current_metrics.record_count < self.config.min_record_count:
            alert = Alert(
                alert_id=f"size_{int(time.time())}",
                alert_name="Low Record Count",
                severity="critical",
                message=f"Record count {current_metrics.record_count} below minimum {self.config.min_record_count}",
                timestamp=timestamp,
                dataset_id=self.config.dataset_id,
                metric_name="record_count",
                metric_value=float(current_metrics.record_count),
                threshold=float(self.config.min_record_count),
            )
            alerts.append(alert)
            self.alert_history.append(alert)
        
        return alerts
    
    def get_metric_trend(self, metric_name: str, hours: int = 24) -> List[Tuple[str, float]]:
        """Get metric trend over time.
        
        Args:
            metric_name: Name of metric to track
            hours: Number of hours of history
        
        Returns:
            List of (timestamp, value) tuples
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        trend = []
        
        for snapshot in self.metric_history:
            snapshot_time = datetime.fromisoformat(snapshot.timestamp.replace('Z', '+00:00'))
            if snapshot_time >= cutoff:
                value = getattr(snapshot, metric_name, None)
                if value is not None:
                    trend.append((snapshot.timestamp, value))
        
        return trend
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for time period.
        
        Args:
            hours: Number of hours to summarize
        
        Returns:
            Summary dictionary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = []
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00'))
            if alert_time >= cutoff:
                recent_alerts.append(alert)
        
        severity_counts = {"info": 0, "warning": 0, "critical": 0}
        for alert in recent_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        return {
            "time_period_hours": hours,
            "total_alerts": len(recent_alerts),
            "severity_counts": severity_counts,
            "recent_alerts": [a.to_dict() for a in recent_alerts[-10:]],  # Last 10
        }
    
    def save_health_status(self, status: HealthStatus, output_path: Path) -> None:
        """Save health status to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(status.to_json())
    
    def save_metrics_history(self, output_path: Path) -> None:
        """Save metric history to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([m.to_dict() for m in self.metric_history], f, indent=2)
    
    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate monitoring dashboard data.
        
        Returns:
            Dashboard data dictionary
        """
        if not self.metric_history:
            return {
                "dataset_id": self.config.dataset_id,
                "status": "no_data",
                "message": "No monitoring data available",
            }
        
        latest_metrics = self.metric_history[-1]
        
        # Compute trends
        quality_trend = self.get_metric_trend("avg_quality_score", hours=24)
        size_trend = self.get_metric_trend("record_count", hours=24)
        
        # Alert summary
        alert_summary = self.get_alert_summary(hours=24)
        
        return {
            "dataset_id": self.config.dataset_id,
            "current_metrics": latest_metrics.to_dict(),
            "trends": {
                "quality_score_24h": quality_trend,
                "record_count_24h": size_trend,
            },
            "alerts_24h": alert_summary,
            "monitoring_config": self.config.to_dict(),
        }
