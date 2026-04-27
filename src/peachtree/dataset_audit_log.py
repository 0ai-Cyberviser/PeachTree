"""Comprehensive audit logging for dataset operations."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditAction(Enum):
    """Types of audit actions."""
    
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    MERGE = "merge"
    SPLIT = "split"
    DEDUPLICATE = "deduplicate"
    QUALITY_CHECK = "quality_check"
    COMPLIANCE_CHECK = "compliance_check"
    BACKUP = "backup"
    RESTORE = "restore"
    PUBLISH = "publish"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditStatus(Enum):
    """Status of audited operations."""
    
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class AuditContext:
    """Context information for audit events."""
    
    user_id: str
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "additional_metadata": self.additional_metadata,
        }


@dataclass
class AuditEntry:
    """A single audit log entry."""
    
    entry_id: str
    timestamp: str
    action: AuditAction
    resource_type: str
    resource_id: str
    status: AuditStatus
    severity: AuditSeverity
    context: AuditContext
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
            "description": self.description,
            "details": self.details,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class DatasetAuditLog:
    """Audit log system for dataset operations."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the audit log system."""
        self.log_dir = log_dir or Path(".peachtree/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.entries: List[AuditEntry] = []
        self.active_sessions: Dict[str, List[str]] = {}
    
    def log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        status: AuditStatus,
        context: AuditContext,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> AuditEntry:
        """Log an audit event."""
        entry_id = f"audit_{datetime.utcnow().timestamp()}"
        
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            severity=severity,
            context=context,
            description=description,
            details=details or {},
            error_message=error_message,
            duration_ms=duration_ms,
        )
        
        self.entries.append(entry)
        
        # Track session
        session_id = context.session_id
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = []
        self.active_sessions[session_id].append(entry_id)
        
        # Write to log file
        self._write_to_file(entry)
        
        return entry
    
    def _write_to_file(self, entry: AuditEntry) -> None:
        """Write entry to log file."""
        # Create daily log file
        date_str = entry.timestamp[:10]  # YYYY-MM-DD
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        
        with log_file.open("a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")
    
    def query(
        self,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit log entries."""
        results = self.entries.copy()
        
        # Apply filters
        if action:
            results = [e for e in results if e.action == action]
        
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        
        if user_id:
            results = [e for e in results if e.context.user_id == user_id]
        
        if session_id:
            results = [e for e in results if e.context.session_id == session_id]
        
        if status:
            results = [e for e in results if e.status == status]
        
        if severity:
            results = [e for e in results if e.severity == severity]
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        return results[:limit]
    
    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Get a specific audit entry."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def get_session_entries(self, session_id: str) -> List[AuditEntry]:
        """Get all entries for a session."""
        return self.query(session_id=session_id, limit=1000)
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get full history for a resource."""
        return self.query(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
    
    def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get activity for a user."""
        return self.query(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
    
    def get_failed_operations(
        self,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get all failed operations."""
        return self.query(
            status=AuditStatus.FAILURE,
            resource_type=resource_type,
            limit=limit,
        )
    
    def get_critical_events(
        self,
        start_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get critical severity events."""
        return self.query(
            severity=AuditSeverity.CRITICAL,
            start_time=start_time,
            limit=limit,
        )
    
    def generate_report(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate audit report."""
        entries = self.query(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )
        
        # Count by action
        by_action = {}
        for entry in entries:
            action = entry.action.value
            by_action[action] = by_action.get(action, 0) + 1
        
        # Count by status
        by_status = {}
        for entry in entries:
            status = entry.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by severity
        by_severity = {}
        for entry in entries:
            severity = entry.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by user
        by_user = {}
        for entry in entries:
            user_id = entry.context.user_id
            by_user[user_id] = by_user.get(user_id, 0) + 1
        
        # Count by resource type
        by_resource_type = {}
        for entry in entries:
            resource_type = entry.resource_type
            by_resource_type[resource_type] = by_resource_type.get(resource_type, 0) + 1
        
        # Calculate metrics
        total_entries = len(entries)
        successful = by_status.get("success", 0)
        failed = by_status.get("failure", 0)
        success_rate = successful / max(total_entries, 1)
        
        # Find most active users
        top_users = sorted(
            by_user.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]
        
        return {
            "time_range": {
                "start": start_time,
                "end": end_time,
            },
            "summary": {
                "total_entries": total_entries,
                "successful_operations": successful,
                "failed_operations": failed,
                "success_rate": success_rate,
            },
            "by_action": by_action,
            "by_status": by_status,
            "by_severity": by_severity,
            "by_resource_type": by_resource_type,
            "top_users": [
                {"user_id": user_id, "count": count}
                for user_id, count in top_users
            ],
        }
    
    def export_logs(
        self,
        output_path: Path,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> int:
        """Export logs to file."""
        entries = self.query(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry.to_json() + "\n")
        
        return len(entries)
    
    def load_logs(self, input_path: Path) -> int:
        """Load logs from file."""
        count = 0
        
        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                data = json.loads(line)
                
                context = AuditContext(
                    user_id=data["context"]["user_id"],
                    session_id=data["context"]["session_id"],
                    ip_address=data["context"].get("ip_address"),
                    user_agent=data["context"].get("user_agent"),
                    additional_metadata=data["context"].get("additional_metadata", {}),
                )
                
                entry = AuditEntry(
                    entry_id=data["entry_id"],
                    timestamp=data["timestamp"],
                    action=AuditAction(data["action"]),
                    resource_type=data["resource_type"],
                    resource_id=data["resource_id"],
                    status=AuditStatus(data["status"]),
                    severity=AuditSeverity(data["severity"]),
                    context=context,
                    description=data["description"],
                    details=data.get("details", {}),
                    error_message=data.get("error_message"),
                    duration_ms=data.get("duration_ms"),
                )
                
                self.entries.append(entry)
                count += 1
        
        return count
    
    def clear_old_logs(self, days: int) -> int:
        """Clear logs older than specified days."""
        cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
        cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat() + "Z"
        
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.timestamp >= cutoff_iso]
        
        return original_count - len(self.entries)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        total_entries = len(self.entries)
        active_sessions = len(self.active_sessions)
        
        # Get date range
        if self.entries:
            earliest = min(e.timestamp for e in self.entries)
            latest = max(e.timestamp for e in self.entries)
        else:
            earliest = None
            latest = None
        
        # Count by action
        by_action = {}
        for entry in self.entries:
            action = entry.action.value
            by_action[action] = by_action.get(action, 0) + 1
        
        # Count by status
        by_status = {}
        for entry in self.entries:
            status = entry.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_entries": total_entries,
            "active_sessions": active_sessions,
            "date_range": {
                "earliest": earliest,
                "latest": latest,
            },
            "by_action": by_action,
            "by_status": by_status,
        }


# Context manager for audit logging
class AuditContext:
    """Context manager for audit logging with automatic timing."""
    
    def __init__(
        self,
        audit_log: DatasetAuditLog,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        context: AuditContext,
        description: str,
    ):
        """Initialize audit context."""
        self.audit_log = audit_log
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.context = context
        self.description = description
        self.start_time = None
        self.entry = None
    
    def __enter__(self):
        """Enter context."""
        self.start_time = datetime.utcnow().timestamp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log entry."""
        end_time = datetime.utcnow().timestamp()
        duration_ms = (end_time - self.start_time) * 1000
        
        if exc_type:
            # Operation failed
            self.entry = self.audit_log.log(
                action=self.action,
                resource_type=self.resource_type,
                resource_id=self.resource_id,
                status=AuditStatus.FAILURE,
                context=self.context,
                description=self.description,
                severity=AuditSeverity.ERROR,
                error_message=str(exc_val),
                duration_ms=duration_ms,
            )
        else:
            # Operation succeeded
            self.entry = self.audit_log.log(
                action=self.action,
                resource_type=self.resource_type,
                resource_id=self.resource_id,
                status=AuditStatus.SUCCESS,
                context=self.context,
                description=self.description,
                duration_ms=duration_ms,
            )
        
        return False  # Don't suppress exceptions
