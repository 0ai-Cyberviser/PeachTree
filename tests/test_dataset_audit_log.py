"""Tests for dataset audit log functionality."""

import json

from peachtree.dataset_audit_log import (
    DatasetAuditLog,
    AuditEntry,
    AuditContext,
    AuditAction,
    AuditSeverity,
    AuditStatus,
)


def test_audit_log_initialization(tmp_path):
    """Test that audit log initializes."""
    log_dir = tmp_path / "audit"
    audit_log = DatasetAuditLog(log_dir=log_dir)
    
    assert audit_log.log_dir == log_dir
    assert log_dir.exists()
    assert isinstance(audit_log.entries, list)


def test_log_audit_entry(tmp_path):
    """Test logging an audit entry."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context = AuditContext(
        user_id="user123",
        session_id="session456",
        ip_address="192.168.1.1",
    )
    
    entry = audit_log.log(
        action=AuditAction.CREATE,
        resource_type="dataset",
        resource_id="dataset_001",
        status=AuditStatus.SUCCESS,
        context=context,
        description="Created new dataset",
    )
    
    assert entry is not None
    assert entry.action == AuditAction.CREATE
    assert entry.status == AuditStatus.SUCCESS
    assert entry.context.user_id == "user123"
    assert len(audit_log.entries) == 1


def test_log_with_details(tmp_path):
    """Test logging with additional details."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context = AuditContext(user_id="user1", session_id="sess1")
    
    entry = audit_log.log(
        action=AuditAction.UPDATE,
        resource_type="dataset",
        resource_id="ds1",
        status=AuditStatus.SUCCESS,
        context=context,
        description="Updated dataset",
        details={"records_added": 100, "records_updated": 50},
        duration_ms=1234.56,
    )
    
    assert entry.details["records_added"] == 100
    assert entry.duration_ms == 1234.56


def test_log_with_error(tmp_path):
    """Test logging a failed operation."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context = AuditContext(user_id="user1", session_id="sess1")
    
    entry = audit_log.log(
        action=AuditAction.DELETE,
        resource_type="dataset",
        resource_id="ds1",
        status=AuditStatus.FAILURE,
        context=context,
        description="Failed to delete dataset",
        severity=AuditSeverity.ERROR,
        error_message="Permission denied",
    )
    
    assert entry.status == AuditStatus.FAILURE
    assert entry.severity == AuditSeverity.ERROR
    assert "Permission denied" in entry.error_message


def test_query_by_action(tmp_path):
    """Test querying entries by action."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    # Log different actions
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Created")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds2", AuditStatus.SUCCESS, context, "Updated")
    audit_log.log(AuditAction.CREATE, "dataset", "ds3", AuditStatus.SUCCESS, context, "Created")
    
    create_entries = audit_log.query(action=AuditAction.CREATE)
    
    assert len(create_entries) == 2
    assert all(e.action == AuditAction.CREATE for e in create_entries)


def test_query_by_resource(tmp_path):
    """Test querying entries by resource type and ID."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Created")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Updated")
    audit_log.log(AuditAction.CREATE, "model", "m1", AuditStatus.SUCCESS, context, "Created")
    
    ds1_entries = audit_log.query(resource_type="dataset", resource_id="ds1")
    
    assert len(ds1_entries) == 2
    assert all(e.resource_id == "ds1" for e in ds1_entries)


def test_query_by_user(tmp_path):
    """Test querying entries by user."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context1 = AuditContext(user_id="user1", session_id="sess1")
    context2 = AuditContext(user_id="user2", session_id="sess2")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Created")
    audit_log.log(AuditAction.CREATE, "dataset", "ds2", AuditStatus.SUCCESS, context2, "Created")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Updated")
    
    user1_entries = audit_log.query(user_id="user1")
    
    assert len(user1_entries) == 2
    assert all(e.context.user_id == "user1" for e in user1_entries)


def test_query_by_status(tmp_path):
    """Test querying entries by status."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Created")
    audit_log.log(AuditAction.DELETE, "dataset", "ds2", AuditStatus.FAILURE, context, "Failed")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds3", AuditStatus.SUCCESS, context, "Updated")
    
    failed_entries = audit_log.query(status=AuditStatus.FAILURE)
    
    assert len(failed_entries) == 1
    assert failed_entries[0].status == AuditStatus.FAILURE


def test_query_with_limit(tmp_path):
    """Test query result limiting."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    # Log 10 entries
    for i in range(10):
        audit_log.log(AuditAction.CREATE, "dataset", f"ds{i}", AuditStatus.SUCCESS, context, f"Entry {i}")
    
    entries = audit_log.query(limit=5)
    
    assert len(entries) == 5


def test_get_entry(tmp_path):
    """Test getting a specific entry."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    logged_entry = audit_log.log(
        AuditAction.CREATE,
        "dataset",
        "ds1",
        AuditStatus.SUCCESS,
        context,
        "Created",
    )
    
    retrieved_entry = audit_log.get_entry(logged_entry.entry_id)
    
    assert retrieved_entry is not None
    assert retrieved_entry.entry_id == logged_entry.entry_id


def test_get_nonexistent_entry(tmp_path):
    """Test getting an entry that doesn't exist."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    entry = audit_log.get_entry("nonexistent_id")
    
    assert entry is None


def test_get_session_entries(tmp_path):
    """Test getting all entries for a session."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context1 = AuditContext(user_id="user1", session_id="session_A")
    context2 = AuditContext(user_id="user1", session_id="session_B")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Entry 1")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Entry 2")
    audit_log.log(AuditAction.CREATE, "dataset", "ds2", AuditStatus.SUCCESS, context2, "Entry 3")
    
    session_entries = audit_log.get_session_entries("session_A")
    
    assert len(session_entries) == 2
    assert all(e.context.session_id == "session_A" for e in session_entries)


def test_get_resource_history(tmp_path):
    """Test getting resource history."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    # Log multiple operations on same resource
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Created")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Updated")
    audit_log.log(AuditAction.VALIDATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Validated")
    audit_log.log(AuditAction.CREATE, "dataset", "ds2", AuditStatus.SUCCESS, context, "Other dataset")
    
    history = audit_log.get_resource_history("dataset", "ds1")
    
    assert len(history) == 3
    assert all(e.resource_id == "ds1" for e in history)


def test_get_user_activity(tmp_path):
    """Test getting user activity."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context = AuditContext(user_id="alice", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Entry 1")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds2", AuditStatus.SUCCESS, context, "Entry 2")
    
    activity = audit_log.get_user_activity("alice")
    
    assert len(activity) == 2
    assert all(e.context.user_id == "alice" for e in activity)


def test_get_failed_operations(tmp_path):
    """Test getting failed operations."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Success")
    audit_log.log(AuditAction.DELETE, "dataset", "ds2", AuditStatus.FAILURE, context, "Failed", error_message="Error")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds3", AuditStatus.FAILURE, context, "Failed", error_message="Error")
    
    failed = audit_log.get_failed_operations()
    
    assert len(failed) == 2
    assert all(e.status == AuditStatus.FAILURE for e in failed)


def test_get_critical_events(tmp_path):
    """Test getting critical severity events."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Info", severity=AuditSeverity.INFO)
    audit_log.log(AuditAction.DELETE, "dataset", "ds2", AuditStatus.FAILURE, context, "Critical", severity=AuditSeverity.CRITICAL)
    audit_log.log(AuditAction.UPDATE, "dataset", "ds3", AuditStatus.SUCCESS, context, "Warning", severity=AuditSeverity.WARNING)
    
    critical = audit_log.get_critical_events()
    
    assert len(critical) == 1
    assert critical[0].severity == AuditSeverity.CRITICAL


def test_generate_report(tmp_path):
    """Test generating audit report."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context1 = AuditContext(user_id="user1", session_id="sess1")
    context2 = AuditContext(user_id="user2", session_id="sess2")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Created")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Updated")
    audit_log.log(AuditAction.DELETE, "dataset", "ds2", AuditStatus.FAILURE, context2, "Failed")
    
    report = audit_log.generate_report()
    
    assert "time_range" in report
    assert "summary" in report
    assert report["summary"]["total_entries"] == 3
    assert report["summary"]["successful_operations"] == 2
    assert report["summary"]["failed_operations"] == 1
    assert "by_action" in report
    assert "by_status" in report
    assert "top_users" in report


def test_export_logs(tmp_path):
    """Test exporting logs to file."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Entry 1")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds2", AuditStatus.SUCCESS, context, "Entry 2")
    
    output_path = tmp_path / "exported_logs.jsonl"
    count = audit_log.export_logs(output_path)
    
    assert count == 2
    assert output_path.exists()
    
    # Verify exported content
    lines = output_path.read_text().strip().split("\n")
    assert len(lines) == 2


def test_load_logs(tmp_path):
    """Test loading logs from file."""
    # Create and export logs
    audit_log1 = DatasetAuditLog(log_dir=tmp_path / "audit1")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    audit_log1.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context, "Entry 1")
    audit_log1.log(AuditAction.UPDATE, "dataset", "ds2", AuditStatus.SUCCESS, context, "Entry 2")
    
    export_path = tmp_path / "logs.jsonl"
    audit_log1.export_logs(export_path)
    
    # Load into new audit log
    audit_log2 = DatasetAuditLog(log_dir=tmp_path / "audit2")
    count = audit_log2.load_logs(export_path)
    
    assert count == 2
    assert len(audit_log2.entries) == 2


def test_clear_old_logs(tmp_path):
    """Test clearing old logs."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    context = AuditContext(user_id="user1", session_id="sess1")
    
    # Add some entries
    for i in range(5):
        audit_log.log(AuditAction.CREATE, "dataset", f"ds{i}", AuditStatus.SUCCESS, context, f"Entry {i}")
    
    # Clear logs older than 1000 days (should clear none for recent entries)
    cleared = audit_log.clear_old_logs(days=1000)
    
    assert cleared == 0
    assert len(audit_log.entries) == 5


def test_get_statistics(tmp_path):
    """Test getting audit log statistics."""
    audit_log = DatasetAuditLog(log_dir=tmp_path / "audit")
    
    context1 = AuditContext(user_id="user1", session_id="sess1")
    context2 = AuditContext(user_id="user2", session_id="sess2")
    
    audit_log.log(AuditAction.CREATE, "dataset", "ds1", AuditStatus.SUCCESS, context1, "Entry 1")
    audit_log.log(AuditAction.UPDATE, "dataset", "ds2", AuditStatus.SUCCESS, context1, "Entry 2")
    audit_log.log(AuditAction.DELETE, "dataset", "ds3", AuditStatus.FAILURE, context2, "Entry 3")
    
    stats = audit_log.get_statistics()
    
    assert stats["total_entries"] == 3
    assert stats["active_sessions"] == 2
    assert "date_range" in stats
    assert "by_action" in stats
    assert "by_status" in stats


def test_audit_context_to_dict():
    """Test converting audit context to dictionary."""
    context = AuditContext(
        user_id="user123",
        session_id="sess456",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        additional_metadata={"key": "value"},
    )
    
    data = context.to_dict()
    
    assert data["user_id"] == "user123"
    assert data["session_id"] == "sess456"
    assert data["ip_address"] == "192.168.1.1"
    assert data["user_agent"] == "Mozilla/5.0"
    assert data["additional_metadata"]["key"] == "value"


def test_audit_entry_to_dict():
    """Test converting audit entry to dictionary."""
    context = AuditContext(user_id="user1", session_id="sess1")
    
    entry = AuditEntry(
        entry_id="entry_123",
        timestamp="2024-01-01T00:00:00Z",
        action=AuditAction.CREATE,
        resource_type="dataset",
        resource_id="ds1",
        status=AuditStatus.SUCCESS,
        severity=AuditSeverity.INFO,
        context=context,
        description="Created dataset",
        details={"records": 100},
        duration_ms=123.45,
    )
    
    data = entry.to_dict()
    
    assert data["entry_id"] == "entry_123"
    assert data["action"] == "create"
    assert data["status"] == "success"
    assert data["severity"] == "info"
    assert data["details"]["records"] == 100


def test_audit_entry_to_json():
    """Test converting audit entry to JSON string."""
    context = AuditContext(user_id="user1", session_id="sess1")
    
    entry = AuditEntry(
        entry_id="entry_123",
        timestamp="2024-01-01T00:00:00Z",
        action=AuditAction.CREATE,
        resource_type="dataset",
        resource_id="ds1",
        status=AuditStatus.SUCCESS,
        severity=AuditSeverity.INFO,
        context=context,
        description="Created dataset",
    )
    
    json_str = entry.to_json()
    
    # Should be valid JSON
    data = json.loads(json_str)
    assert data["entry_id"] == "entry_123"


def test_audit_action_enum_values():
    """Test AuditAction enum has expected values."""
    assert AuditAction.CREATE.value == "create"
    assert AuditAction.READ.value == "read"
    assert AuditAction.UPDATE.value == "update"
    assert AuditAction.DELETE.value == "delete"
    assert AuditAction.EXPORT.value == "export"
    assert AuditAction.IMPORT.value == "import"


def test_audit_severity_enum_values():
    """Test AuditSeverity enum has expected values."""
    assert AuditSeverity.DEBUG.value == "debug"
    assert AuditSeverity.INFO.value == "info"
    assert AuditSeverity.WARNING.value == "warning"
    assert AuditSeverity.ERROR.value == "error"
    assert AuditSeverity.CRITICAL.value == "critical"


def test_audit_status_enum_values():
    """Test AuditStatus enum has expected values."""
    assert AuditStatus.SUCCESS.value == "success"
    assert AuditStatus.FAILURE.value == "failure"
    assert AuditStatus.PARTIAL.value == "partial"
    assert AuditStatus.PENDING.value == "pending"
