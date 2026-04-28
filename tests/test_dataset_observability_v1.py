"""Tests for dataset_observability module."""
import json
from pathlib import Path
import pytest
from datetime import datetime
from src.peachtree.dataset_observability import (
    DatasetObservability,
    MetricsCollector,
    StructuredLogger,
    TraceCollector,
    Metric,
    LogEntry,
    Span,
    MetricType,
    LogLevel,
    SpanKind,
    SpanStatus,
)


def test_metrics_collector_init():
    """Test metrics collector initialization."""
    collector = MetricsCollector()
    assert collector.metrics == []
    assert collector.counters == {}


def test_record_counter():
    """Test recording a counter metric."""
    collector = MetricsCollector()
    collector.record_counter("requests", 1.0, labels={"method": "GET"})
    
    assert len(collector.metrics) == 1
    assert collector.get_counter("requests", {"method": "GET"}) == 1.0


def test_record_counter_increment():
    """Test counter increments."""
    collector = MetricsCollector()
    collector.record_counter("requests")
    collector.record_counter("requests")
    
    assert collector.get_counter("requests") == 2.0


def test_record_gauge():
    """Test recording a gauge metric."""
    collector = MetricsCollector()
    collector.record_gauge("temperature", 72.5)
    
    assert collector.get_gauge("temperature") == 72.5


def test_gauge_overwrites():
    """Test gauge overwrites previous value."""
    collector = MetricsCollector()
    collector.record_gauge("memory", 100.0)
    collector.record_gauge("memory", 200.0)
    
    assert collector.get_gauge("memory") == 200.0


def test_record_histogram():
    """Test recording a histogram metric."""
    collector = MetricsCollector()
    collector.record_histogram("response_time", 123.45, unit="ms")
    
    metrics = collector.get_metrics(metric_type=MetricType.HISTOGRAM)
    assert len(metrics) == 1
    assert metrics[0].value == 123.45


def test_get_metrics_by_name():
    """Test filtering metrics by name."""
    collector = MetricsCollector()
    collector.record_counter("a")
    collector.record_counter("b")
    
    a_metrics = collector.get_metrics(name="a")
    assert len(a_metrics) == 1


def test_get_metrics_by_type():
    """Test filtering metrics by type."""
    collector = MetricsCollector()
    collector.record_counter("c1")
    collector.record_gauge("g1", 10.0)
    
    counters = collector.get_metrics(metric_type=MetricType.COUNTER)
    assert len(counters) == 1


def test_export_metrics():
    """Test exporting metrics."""
    collector = MetricsCollector()
    collector.record_counter("test", 5.0)
    
    exported = collector.export_metrics()
    assert len(exported) == 1
    assert exported[0]["name"] == "test"


def test_structured_logger_init(tmp_path):
    """Test structured logger initialization."""
    logger = StructuredLogger(tmp_path / "logs.jsonl")
    assert logger.output_path == tmp_path / "logs.jsonl"


def test_log_message():
    """Test logging a message."""
    logger = StructuredLogger()
    logger.log(LogLevel.INFO, "test message", "test_op")
    
    assert len(logger.logs) == 1
    assert logger.logs[0].message == "test message"


def test_log_levels():
    """Test different log levels."""
    logger = StructuredLogger()
    
    logger.debug("debug", "op")
    logger.info("info", "op")
    logger.warning("warning", "op")
    logger.error("error", "op")
    logger.critical("critical", "op")
    
    assert len(logger.logs) == 5


def test_get_logs_by_level():
    """Test filtering logs by level."""
    logger = StructuredLogger()
    logger.info("info1", "op")
    logger.error("error1", "op")
    logger.info("info2", "op")
    
    errors = logger.get_logs(level=LogLevel.ERROR)
    assert len(errors) == 1


def test_get_logs_by_operation():
    """Test filtering logs by operation."""
    logger = StructuredLogger()
    logger.info("msg1", "read")
    logger.info("msg2", "write")
    logger.info("msg3", "read")
    
    reads = logger.get_logs(operation="read")
    assert len(reads) == 2


def test_log_with_context():
    """Test logging with context."""
    logger = StructuredLogger()
    logger.log(LogLevel.INFO, "test", "op", context={"user": "alice", "count": 5})
    
    assert logger.logs[0].context["user"] == "alice"


def test_log_to_file(tmp_path):
    """Test logging to file."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(log_file)
    
    logger.info("test message", "test_op")
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "test message" in content


def test_trace_collector_init():
    """Test trace collector initialization."""
    traces = TraceCollector()
    assert traces.spans == {}


def test_start_span():
    """Test starting a span."""
    traces = TraceCollector()
    span = traces.start_span("operation", "trace123")
    
    assert span.trace_id == "trace123"
    assert span.name == "operation"
    assert span.end_time is None


def test_end_span():
    """Test ending a span."""
    traces = TraceCollector()
    span = traces.start_span("op", "trace1")
    
    traces.end_span(span.span_id, SpanStatus.OK)
    
    assert span.end_time is not None
    assert span.status == SpanStatus.OK


def test_span_duration():
    """Test span duration calculation."""
    traces = TraceCollector()
    span = traces.start_span("op", "trace1")
    traces.end_span(span.span_id)
    
    duration = span.duration_ms()
    assert duration is not None
    assert duration >= 0


def test_add_span_event():
    """Test adding event to span."""
    traces = TraceCollector()
    span = traces.start_span("op", "trace1")
    
    traces.add_span_event(span.span_id, "checkpoint", {"step": 1})
    
    assert len(span.events) == 1
    assert span.events[0]["name"] == "checkpoint"


def test_get_span():
    """Test retrieving a span."""
    traces = TraceCollector()
    span = traces.start_span("op", "trace1")
    
    retrieved = traces.get_span(span.span_id)
    assert retrieved.span_id == span.span_id


def test_get_trace():
    """Test getting all spans for a trace."""
    traces = TraceCollector()
    traces.start_span("op1", "trace1")
    traces.start_span("op2", "trace1")
    traces.start_span("op3", "trace2")
    
    trace1_spans = traces.get_trace("trace1")
    assert len(trace1_spans) == 2


def test_export_traces():
    """Test exporting traces."""
    traces = TraceCollector()
    span = traces.start_span("op", "trace1")
    traces.end_span(span.span_id)
    
    exported = traces.export_traces()
    assert len(exported) == 1
    assert exported[0]["trace_id"] == "trace1"


def test_observability_init():
    """Test observability initialization."""
    obs = DatasetObservability()
    assert obs.metrics is not None
    assert obs.logger is not None
    assert obs.traces is not None


def test_observe_operation():
    """Test observing an operation."""
    obs = DatasetObservability()
    span = obs.observe_operation("read", "trace123")
    
    assert span.name == "read"
    assert span.trace_id == "trace123"


def test_complete_operation_success():
    """Test completing operation successfully."""
    obs = DatasetObservability()
    span = obs.observe_operation("write", "trace1")
    
    obs.complete_operation(span, success=True)
    
    assert span.status == SpanStatus.OK
    assert span.end_time is not None


def test_complete_operation_failure():
    """Test completing operation with failure."""
    obs = DatasetObservability()
    span = obs.observe_operation("delete", "trace1")
    
    obs.complete_operation(span, success=False, error="Not found")
    
    assert span.status == SpanStatus.ERROR


def test_get_telemetry_report():
    """Test getting telemetry report."""
    obs = DatasetObservability()
    obs.observe_operation("op1", "t1")
    obs.metrics.record_counter("test")
    obs.logger.info("test", "op")
    
    report = obs.get_telemetry_report()
    
    assert "metrics" in report
    assert "logs" in report
    assert "traces" in report


def test_export_all(tmp_path):
    """Test exporting all telemetry."""
    obs = DatasetObservability()
    obs.metrics.record_counter("test")
    obs.logger.info("test", "op")
    obs.observe_operation("op", "t1")
    
    obs.export_all(tmp_path)
    
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "logs.json").exists()
    assert (tmp_path / "traces.json").exists()


def test_metric_type_enum():
    """Test metric type enum."""
    assert MetricType.COUNTER
    assert MetricType.GAUGE
    assert MetricType.HISTOGRAM
    assert MetricType.SUMMARY


def test_log_level_enum():
    """Test log level enum."""
    assert LogLevel.DEBUG
    assert LogLevel.INFO
    assert LogLevel.WARNING
    assert LogLevel.ERROR
    assert LogLevel.CRITICAL


def test_span_kind_enum():
    """Test span kind enum."""
    assert SpanKind.INTERNAL
    assert SpanKind.SERVER
    assert SpanKind.CLIENT
    assert SpanKind.PRODUCER
    assert SpanKind.CONSUMER


def test_span_status_enum():
    """Test span status enum."""
    assert SpanStatus.UNSET
    assert SpanStatus.OK
    assert SpanStatus.ERROR


def test_metric_serialization():
    """Test metric serialization."""
    metric = Metric(
        name="test",
        metric_type=MetricType.COUNTER,
        value=5.0,
        timestamp=datetime.now(),
        labels={"env": "prod"},
        unit="requests",
    )
    
    data = metric.to_dict()
    assert "name" in data
    assert "value" in data
    assert data["labels"]["env"] == "prod"


def test_log_entry_serialization():
    """Test log entry serialization."""
    entry = LogEntry(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="test",
        operation="op",
        context={"key": "value"},
        trace_id="t1",
    )
    
    data = entry.to_dict()
    assert "message" in data
    assert "level" in data
    assert data["trace_id"] == "t1"


def test_span_serialization():
    """Test span serialization."""
    span = Span(
        span_id="s1",
        trace_id="t1",
        parent_span_id=None,
        name="operation",
        kind=SpanKind.INTERNAL,
        start_time=datetime.now(),
    )
    
    data = span.to_dict()
    assert "span_id" in data
    assert "trace_id" in data
    assert "name" in data


def test_nested_spans():
    """Test creating nested spans."""
    traces = TraceCollector()
    parent = traces.start_span("parent", "trace1")
    child = traces.start_span("child", "trace1", parent_span_id=parent.span_id)
    
    assert child.parent_span_id == parent.span_id


def test_span_with_attributes():
    """Test span with custom attributes."""
    traces = TraceCollector()
    span = traces.start_span(
        "op",
        "trace1",
        attributes={"dataset": "train.jsonl", "records": 1000},
    )
    
    assert span.attributes["dataset"] == "train.jsonl"


def test_metrics_with_labels():
    """Test metrics with labels."""
    collector = MetricsCollector()
    collector.record_counter("requests", 1.0, labels={"method": "GET", "status": "200"})
    collector.record_counter("requests", 1.0, labels={"method": "POST", "status": "201"})
    
    assert len(collector.metrics) == 2
