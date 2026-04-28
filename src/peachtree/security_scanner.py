"""
PeachTree Dataset Security Scanner

Scan datasets for security vulnerabilities including secrets, credentials, PII,
and sensitive data. Integrates with Hancock cybersecurity workflows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import re


class SecurityIssueType:
    """Security issue types"""
    SECRET = "secret"
    CREDENTIAL = "credential"
    PII = "pii"
    API_KEY = "api_key"
    PASSWORD = "password"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PRIVATE_KEY = "private_key"
    AWS_KEY = "aws_key"
    GITHUB_TOKEN = "github_token"


@dataclass
class SecurityIssue:
    """Single security issue found in dataset"""
    issue_type: str
    severity: str  # critical, high, medium, low
    message: str
    record_id: str | None = None
    field_name: str | None = None
    matched_pattern: str | None = None
    line_number: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "record_id": self.record_id,
            "field_name": self.field_name,
            "matched_pattern": self.matched_pattern,
            "line_number": self.line_number,
        }


@dataclass
class SecurityScanReport:
    """Complete security scan report"""
    dataset_path: str
    total_records: int
    scanned_records: int
    issues: list[SecurityIssue] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: SecurityIssue) -> None:
        """Add security issue to report"""
        self.issues.append(issue)
        
        if issue.severity == "critical":
            self.critical_count += 1
        elif issue.severity == "high":
            self.high_count += 1
        elif issue.severity == "medium":
            self.medium_count += 1
        elif issue.severity == "low":
            self.low_count += 1
    
    def is_safe(self) -> bool:
        """Check if dataset is safe (no critical/high issues)"""
        return self.critical_count == 0 and self.high_count == 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "total_records": self.total_records,
            "scanned_records": self.scanned_records,
            "is_safe": self.is_safe(),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "issues": [i.to_dict() for i in self.issues],
            "scan_timestamp": self.scan_timestamp,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Generate markdown security report"""
        status_icon = "✅" if self.is_safe() else "⚠️" if self.critical_count == 0 else "❌"
        status_text = "SAFE" if self.is_safe() else "ISSUES FOUND" if self.critical_count == 0 else "CRITICAL ISSUES"
        
        lines = [
            "# Dataset Security Scan Report",
            "",
            f"**Dataset:** {self.dataset_path}",
            f"**Total Records:** {self.total_records:,}",
            f"**Scanned:** {self.scanned_records:,}",
            f"**Status:** {status_icon} {status_text}",
            f"**Scan Time:** {self.scan_timestamp}",
            "",
            "## Issue Summary",
            "",
            f"- **Critical:** {self.critical_count}",
            f"- **High:** {self.high_count}",
            f"- **Medium:** {self.medium_count}",
            f"- **Low:** {self.low_count}",
            "",
        ]
        
        if self.issues:
            # Group by severity
            for severity in ["critical", "high", "medium", "low"]:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if not severity_issues:
                    continue
                
                icon = "❌" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
                lines.extend([f"### {icon} {severity.upper()} Issues", ""])
                
                for issue in severity_issues[:20]:  # Limit to first 20
                    lines.append(f"- **{issue.issue_type}**: {issue.message}")
                    if issue.record_id:
                        lines.append(f"  - Record: `{issue.record_id}`")
                    if issue.field_name:
                        lines.append(f"  - Field: `{issue.field_name}`")
                
                if len(severity_issues) > 20:
                    lines.append(f"- ... and {len(severity_issues) - 20} more {severity} issues")
                
                lines.append("")
        
        return "\n".join(lines)


class DatasetSecurityScanner:
    """Scan datasets for security vulnerabilities"""
    
    def __init__(self):
        """Initialize security scanner with detection patterns"""
        # Regex patterns for various security issues
        self.patterns = {
            SecurityIssueType.AWS_KEY: [
                (r'AKIA[0-9A-Z]{16}', "critical"),
                (r'aws_access_key_id\s*=\s*["\']?[A-Z0-9]{20}', "critical"),
            ],
            SecurityIssueType.GITHUB_TOKEN: [
                (r'ghp_[a-zA-Z0-9]{36}', "critical"),
                (r'gho_[a-zA-Z0-9]{36}', "critical"),
                (r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', "critical"),
            ],
            SecurityIssueType.PRIVATE_KEY: [
                (r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----', "critical"),
                (r'-----BEGIN PGP PRIVATE KEY BLOCK-----', "critical"),
            ],
            SecurityIssueType.PASSWORD: [
                (r'password\s*[:=]\s*["\']?[^\s"\']{8,}', "high"),
                (r'passwd\s*[:=]\s*["\']?[^\s"\']{8,}', "high"),
            ],
            SecurityIssueType.API_KEY: [
                (r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', "high"),
                (r'apikey\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', "high"),
            ],
            SecurityIssueType.EMAIL: [
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "medium"),
            ],
            SecurityIssueType.PHONE: [
                (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "low"),
                (r'\+\d{1,3}[-\s]?\(?\d{1,4}\)?[-\s]?\d{1,4}[-\s]?\d{1,9}', "low"),
            ],
            SecurityIssueType.SSN: [
                (r'\b\d{3}-\d{2}-\d{4}\b', "critical"),
            ],
            SecurityIssueType.CREDIT_CARD: [
                (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "critical"),
            ],
        }
    
    def _scan_text(self, text: str, record_id: str | None = None, field_name: str | None = None) -> list[SecurityIssue]:
        """Scan text for security issues"""
        issues = []
        
        for issue_type, patterns in self.patterns.items():
            for pattern, severity in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    issues.append(SecurityIssue(
                        issue_type=issue_type,
                        severity=severity,
                        message=f"Found {issue_type} in dataset",
                        record_id=record_id,
                        field_name=field_name,
                        matched_pattern=pattern,
                    ))
        
        return issues
    
    def scan_record(self, record: dict[str, Any]) -> list[SecurityIssue]:
        """Scan single record for security issues"""
        issues = []
        record_id = record.get("id")
        
        for field_name, value in record.items():
            if isinstance(value, str):
                field_issues = self._scan_text(value, record_id, field_name)
                issues.extend(field_issues)
        
        return issues
    
    def scan_dataset(
        self,
        dataset_path: Path | str,
        stop_on_critical: bool = False,
    ) -> SecurityScanReport:
        """
        Scan entire dataset for security issues
        
        Args:
            dataset_path: Dataset to scan
            stop_on_critical: Stop scan on first critical issue
        
        Returns:
            SecurityScanReport with all findings
        """
        dataset_path = Path(dataset_path)
        
        report = SecurityScanReport(
            dataset_path=str(dataset_path),
            total_records=0,
            scanned_records=0,
        )
        
        with open(dataset_path) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                report.total_records += 1
                record = json.loads(line)
                
                issues = self.scan_record(record)
                
                for issue in issues:
                    issue.line_number = line_num
                    report.add_issue(issue)
                    
                    if stop_on_critical and issue.severity == "critical":
                        report.scanned_records += 1
                        return report
                
                report.scanned_records += 1
        
        return report
    
    def scan_field(
        self,
        dataset_path: Path | str,
        field_name: str,
    ) -> SecurityScanReport:
        """
        Scan specific field across dataset
        
        Args:
            dataset_path: Dataset to scan
            field_name: Field to scan
        
        Returns:
            SecurityScanReport
        """
        dataset_path = Path(dataset_path)
        
        report = SecurityScanReport(
            dataset_path=str(dataset_path),
            total_records=0,
            scanned_records=0,
            metadata={"scanned_field": field_name},
        )
        
        with open(dataset_path) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                report.total_records += 1
                record = json.loads(line)
                
                if field_name in record and isinstance(record[field_name], str):
                    issues = self._scan_text(
                        record[field_name],
                        record_id=record.get("id"),
                        field_name=field_name,
                    )
                    
                    for issue in issues:
                        issue.line_number = line_num
                        report.add_issue(issue)
                
                report.scanned_records += 1
        
        return report
    
    def quick_scan(
        self,
        dataset_path: Path | str,
        sample_size: int = 100,
    ) -> SecurityScanReport:
        """
        Quick scan of dataset sample
        
        Args:
            dataset_path: Dataset to scan
            sample_size: Number of records to sample
        
        Returns:
            SecurityScanReport
        """
        dataset_path = Path(dataset_path)
        
        report = SecurityScanReport(
            dataset_path=str(dataset_path),
            total_records=0,
            scanned_records=0,
            metadata={"scan_type": "quick", "sample_size": sample_size},
        )
        
        with open(dataset_path) as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                report.total_records += 1
                
                if report.scanned_records >= sample_size:
                    continue
                
                record = json.loads(line)
                issues = self.scan_record(record)
                
                for issue in issues:
                    issue.line_number = line_num
                    report.add_issue(issue)
                
                report.scanned_records += 1
        
        return report
