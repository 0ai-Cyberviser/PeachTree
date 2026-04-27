"""
Tests for security_scanner module
"""
from pathlib import Path
import pytest
import json
from peachtree.security_scanner import (
    DatasetSecurityScanner,
    SecurityScanReport,
    SecurityIssue,
    SecurityIssueType,
)


@pytest.fixture
def test_dataset_safe(tmp_path):
    """Create safe test dataset"""
    dataset = tmp_path / "safe.jsonl"
    records = [
        {"id": "1", "content": "This is safe content"},
        {"id": "2", "content": "No sensitive data here"},
        {"id": "3", "content": "Just normal text"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


@pytest.fixture
def test_dataset_unsafe(tmp_path):
    """Create unsafe test dataset with security issues"""
    dataset = tmp_path / "unsafe.jsonl"
    records = [
        {"id": "1", "content": "My password is: password123456"},
        {"id": "2", "content": "AWS key: AKIAIOSFODNN7EXAMPLE"},
        {"id": "3", "content": "Contact: user@example.com"},
        {"id": "4", "content": "Phone: 555-123-4567"},
        {"id": "5", "content": "SSN: 123-45-6789"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_security_issue_creation():
    """Test SecurityIssue dataclass"""
    issue = SecurityIssue(
        issue_type=SecurityIssueType.PASSWORD,
        severity="high",
        message="Password found",
        record_id="123",
        field_name="content",
    )
    
    assert issue.issue_type == SecurityIssueType.PASSWORD
    assert issue.severity == "high"
    assert issue.to_dict()["message"] == "Password found"


def test_security_scan_report_creation():
    """Test SecurityScanReport initialization"""
    report = SecurityScanReport(
        dataset_path="test.jsonl",
        total_records=100,
        scanned_records=100,
    )
    
    assert report.total_records == 100
    assert report.is_safe()  # No issues yet


def test_security_scan_report_add_issue():
    """Test adding issues to report"""
    report = SecurityScanReport("test.jsonl", 10, 10)
    
    issue = SecurityIssue(SecurityIssueType.SECRET, "critical", "Secret found")
    report.add_issue(issue)
    
    assert len(report.issues) == 1
    assert report.critical_count == 1
    assert not report.is_safe()


def test_security_scan_report_severity_counts():
    """Test that report tracks severity counts"""
    report = SecurityScanReport("test.jsonl", 10, 10)
    
    report.add_issue(SecurityIssue(SecurityIssueType.SECRET, "critical", "c"))
    report.add_issue(SecurityIssue(SecurityIssueType.PASSWORD, "high", "h"))
    report.add_issue(SecurityIssue(SecurityIssueType.EMAIL, "medium", "m"))
    report.add_issue(SecurityIssue(SecurityIssueType.PHONE, "low", "l"))
    
    assert report.critical_count == 1
    assert report.high_count == 1
    assert report.medium_count == 1
    assert report.low_count == 1


def test_security_scan_report_to_json():
    """Test JSON serialization"""
    report = SecurityScanReport("test.jsonl", 5, 5)
    report.add_issue(SecurityIssue(SecurityIssueType.SECRET, "critical", "msg"))
    
    json_str = report.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["total_records"] == 5
    assert parsed["is_safe"] is False
    assert len(parsed["issues"]) == 1


def test_security_scan_report_to_markdown():
    """Test markdown generation"""
    report = SecurityScanReport("test.jsonl", 10, 10)
    report.add_issue(SecurityIssue(SecurityIssueType.SECRET, "critical", "secret found"))
    
    markdown = report.to_markdown()
    
    assert "# Dataset Security Scan Report" in markdown
    assert "❌ CRITICAL ISSUES" in markdown
    assert "secret found" in markdown


def test_scanner_initialization():
    """Test scanner initialization"""
    scanner = DatasetSecurityScanner()
    
    assert SecurityIssueType.AWS_KEY in scanner.patterns
    assert SecurityIssueType.GITHUB_TOKEN in scanner.patterns


def test_scan_text_aws_key():
    """Test detecting AWS keys"""
    scanner = DatasetSecurityScanner()
    
    text = "My AWS key is AKIAIOSFODNN7EXAMPLE"
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.AWS_KEY for i in issues)


def test_scan_text_github_token():
    """Test detecting GitHub tokens"""
    scanner = DatasetSecurityScanner()
    
    text = "Token: ghp_abc123def456ghi789jkl012mno345pqr678"
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.GITHUB_TOKEN for i in issues)


def test_scan_text_private_key():
    """Test detecting private keys"""
    scanner = DatasetSecurityScanner()
    
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAI..."
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.PRIVATE_KEY for i in issues)


def test_scan_text_password():
    """Test detecting passwords"""
    scanner = DatasetSecurityScanner()
    
    text = "password: mySecretPass123"
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.PASSWORD for i in issues)


def test_scan_text_email():
    """Test detecting emails"""
    scanner = DatasetSecurityScanner()
    
    text = "Contact me at user@example.com"
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.EMAIL for i in issues)


def test_scan_text_ssn():
    """Test detecting SSNs"""
    scanner = DatasetSecurityScanner()
    
    text = "My SSN is 123-45-6789"
    issues = scanner._scan_text(text)
    
    assert len(issues) > 0
    assert any(i.issue_type == SecurityIssueType.SSN for i in issues)


def test_scan_record():
    """Test scanning single record"""
    scanner = DatasetSecurityScanner()
    
    record = {
        "id": "1",
        "content": "AWS key: AKIAIOSFODNN7EXAMPLE",
        "metadata": "Safe metadata"
    }
    
    issues = scanner.scan_record(record)
    
    assert len(issues) > 0
    assert issues[0].record_id == "1"
    assert issues[0].field_name == "content"


def test_scan_dataset_safe(test_dataset_safe):
    """Test scanning safe dataset"""
    scanner = DatasetSecurityScanner()
    report = scanner.scan_dataset(test_dataset_safe)
    
    assert report.total_records == 3
    assert report.scanned_records == 3
    assert report.is_safe()
    assert len(report.issues) == 0


def test_scan_dataset_unsafe(test_dataset_unsafe):
    """Test scanning unsafe dataset"""
    scanner = DatasetSecurityScanner()
    report = scanner.scan_dataset(test_dataset_unsafe)
    
    assert report.total_records == 5
    assert report.scanned_records == 5
    assert not report.is_safe()
    assert len(report.issues) > 0


def test_scan_dataset_stop_on_critical(test_dataset_unsafe):
    """Test stop_on_critical flag"""
    scanner = DatasetSecurityScanner()
    report = scanner.scan_dataset(test_dataset_unsafe, stop_on_critical=True)
    
    # Should stop when finding SSN (critical)
    assert report.scanned_records < report.total_records or report.critical_count > 0


def test_scan_field(test_dataset_unsafe):
    """Test scanning specific field"""
    scanner = DatasetSecurityScanner()
    report = scanner.scan_field(test_dataset_unsafe, "content")
    
    assert report.total_records == 5
    assert report.scanned_records == 5
    assert report.metadata["scanned_field"] == "content"


def test_quick_scan(test_dataset_unsafe):
    """Test quick scan with sampling"""
    scanner = DatasetSecurityScanner()
    report = scanner.quick_scan(test_dataset_unsafe, sample_size=3)
    
    assert report.scanned_records <= 3
    assert report.metadata["scan_type"] == "quick"
    assert report.metadata["sample_size"] == 3


def test_scan_multiple_issues_per_record(tmp_path):
    """Test record with multiple security issues"""
    dataset = tmp_path / "multi.jsonl"
    record = {
        "id": "1",
        "content": "Email: user@example.com, AWS: AKIAIOSFODNN7EXAMPLE, Phone: 555-1234"
    }
    dataset.write_text(json.dumps(record) + "\n")
    
    scanner = DatasetSecurityScanner()
    report = scanner.scan_dataset(dataset)
    
    assert len(report.issues) >= 3  # Email, AWS, Phone


def test_severity_levels():
    """Test that different issue types have correct severities"""
    scanner = DatasetSecurityScanner()
    
    # Critical
    aws_issues = scanner._scan_text("AKIAIOSFODNN7EXAMPLE")
    assert any(i.severity == "critical" for i in aws_issues)
    
    # High
    password_issues = scanner._scan_text("password: secret123")
    assert any(i.severity == "high" for i in password_issues)
    
    # Medium
    email_issues = scanner._scan_text("user@example.com")
    assert any(i.severity == "medium" for i in email_issues)


def test_line_number_tracking(test_dataset_unsafe):
    """Test that line numbers are tracked"""
    scanner = DatasetSecurityScanner()
    report = scanner.scan_dataset(test_dataset_unsafe)
    
    # All issues should have line numbers
    for issue in report.issues:
        assert issue.line_number is not None
        assert issue.line_number > 0
