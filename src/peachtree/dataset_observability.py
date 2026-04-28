"""Dataset observability with metrics, traces, and logs.

Provides OpenTelemetry-style observability for dataset operations
with metrics collection, distributed tracing, and structured logging.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import time


class MetricType(Enum):
    """Metric type."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Log level."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SpanKind(Enum):
    """Trace span kind."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Trace span status."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Metric:
    """Observability metric."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "unit": self.unit,
        }


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    operation: str
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "operation": self.operation,
            "context": self.context,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }


@dataclass
class Span:
    """Distributed trace span."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "duration_ms": self.duration_ms(),
            "attributes": self.attributes,
            "events": self.events,
        }
    
    def duration_ms(self) -> Optional[float]:
        """Calculate span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


class MetricsCollector:
    """Collect and aggregate metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
    
    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record counter metric."""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self.counters[key] = self.counters.get(key, 0) + value
        
        metric = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
        )
        self.metrics.append(metric)
    
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record gauge metric."""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self.gauges[key] = value
        
        metric = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
        )
        self.metrics.append(metric)
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
    ) -> None:
        """Record histogram metric."""
        metric = Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            unit=unit,
        )
        self.metrics.append(metric)
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        return self.gauges.get(key)
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
    ) -> List[Metric]:
        """Get metrics with optional filtering."""
        filtered = self.metrics
        
        if name:
            filtered = [m for m in filtered if m.name == name]
        
        if metric_type:
            filtered = [m for m in filtered if m.metric_type == metric_type]
        
        return filtered
    
    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export all metrics."""
        return [m.to_dict() for m in self.metrics]


class StructuredLogger:
    """Structured logging with context."""
    
    def __init__(self, output_path: Optional[Path] = None):
        """Initialize logger."""
        self.output_path = output_path
        self.logs: List[LogEntry] = []
    
    def log(
        self,
        level: LogLevel,
        message: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ) -> None:
        """Log a message."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            operation=operation,
            context=context or {},
            trace_id=trace_id,
            span_id=span_id,
        )
        
        self.logs.append(entry)
        
        # Write to file if configured
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.output_path.open("a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
    
    def debug(self, message: str, operation: str, **kwargs) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, operation, kwargs)
    
    def info(self, message: str, operation: str, **kwargs) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, operation, kwargs)
    
    def warning(self, message: str, operation: str, **kwargs) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, operation, kwargs)
    
    def error(self, message: str, operation: str, **kwargs) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, operation, kwargs)
    
    def critical(self, message: str, operation: str, **kwargs) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, operation, kwargs)
    
    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        operation: Optional[str] = None,
    ) -> List[LogEntry]:
        """Get logs with optional filtering."""
        filtered = self.logs
        
        if level:
            filtered = [log for log in filtered if log.level == level]
        
        if operation:
            filtered = [log for log in filtered if log.operation == operation]
        
        return filtered


class TraceCollector:
    """Collect distributed traces."""
    
    def __init__(self):
        """Initialize trace collector."""
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, str] = {}  # trace_id -> span_id
    
    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span."""
        span_id = f"span_{len(self.spans)}_{int(time.time() * 1000)}"
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=datetime.now(),
            attributes=attributes or {},
        )
        
        self.spans[span_id] = span
        self.active_spans[trace_id] = span_id
        
        return span
    
    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
    ) -> None:
        """End a span."""
        if span_id in self.spans:
            span = self.spans[span_id]
            span.end_time = datetime.now()
            span.status = status
            
            # Remove from active
            if span.trace_id in self.active_spans and self.active_spans[span.trace_id] == span_id:
                del self.active_spans[span.trace_id]
    
    def add_span_event(
        self,
        span_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event to span."""
        if span_id in self.spans:
            event = {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
            self.spans[span_id].events.append(event)
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get span by ID."""
        return self.spans.get(span_id)
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        return [span for span in self.spans.values() if span.trace_id == trace_id]
    
    def export_traces(self) -> List[Dict[str, Any]]:
        """Export all traces."""
        return [span.to_dict() for span in self.spans.values()]


class DatasetObservability:
    """Unified observability for datasets."""
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        logger: Optional[StructuredLogger] = None,
        trace_collector: Optional[TraceCollector] = None,
    ):
        """Initialize observability."""
        self.metrics = metrics_collector or MetricsCollector()
        self.logger = logger or StructuredLogger()
        self.traces = trace_collector or TraceCollector()
    
    def observe_operation(
        self,
        operation: str,
        trace_id: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start observing an operation."""
        # Start span
        span = self.traces.start_span(operation, trace_id, attributes=attributes)
        
        # Log operation start
        self.logger.info(
            f"Starting {operation}",
            operation,
            trace_id=trace_id,
            span_id=span.span_id,
        )
        
        # Record counter
        self.metrics.record_counter(
            f"dataset.operations.{operation}",
            labels={"status": "started"},
        )
        
        return span
    
    def complete_operation(
        self,
        span: Span,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Complete an observed operation."""
        # End span
        status = SpanStatus.OK if success else SpanStatus.ERROR
        self.traces.end_span(span.span_id, status)
        
        # Log completion
        if success:
            self.logger.info(
                f"Completed {span.name}",
                span.name,
                trace_id=span.trace_id,
                span_id=span.span_id,
            )
        else:
            self.logger.error(
                f"Failed {span.name}: {error}",
                span.name,
                trace_id=span.trace_id,
                span_id=span.span_id,
                error=error,
            )
        
        # Record metrics
        self.metrics.record_counter(
            f"dataset.operations.{span.name}",
            labels={"status": "completed" if success else "failed"},
        )
        
        if span.duration_ms():
            self.metrics.record_histogram(
                f"dataset.duration.{span.name}",
                span.duration_ms(),
                unit="ms",
            )
    
    def get_telemetry_report(self) -> Dict[str, Any]:
        """Get comprehensive telemetry report."""
        return {
            "metrics": {
                "total": len(self.metrics.metrics),
                "counters": len(self.metrics.counters),
                "gauges": len(self.metrics.gauges),
            },
            "logs": {
                "total": len(self.logger.logs),
                "by_level": {
                    level.value: len(self.logger.get_logs(level=level))
                    for level in LogLevel
                },
            },
            "traces": {
                "total_spans": len(self.traces.spans),
                "active_spans": len(self.traces.active_spans),
                "completed_spans": len([s for s in self.traces.spans.values() if s.end_time]),
            },
        }
    
    def export_all(self, output_dir: Path) -> None:
        """Export all telemetry data."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export metrics
        metrics_file = output_dir / "metrics.json"
        metrics_file.write_text(json.dumps(self.metrics.export_metrics(), indent=2))
        
        # Export logs
        logs_file = output_dir / "logs.json"
        logs_file.write_text(json.dumps([log.to_dict() for log in self.logger.logs], indent=2))
        
        # Export traces
        traces_file = output_dir / "traces.json"
        traces_file.write_text(json.dumps(self.traces.export_traces(), indent=2))
