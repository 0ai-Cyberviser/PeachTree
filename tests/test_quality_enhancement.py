"""Tests for quality_enhancement module"""
import json
import pytest

from peachtree.quality_enhancement import (
    QualityEnhancementEngine,
    EnhancementReport,
    EnhancementSuggestion,
    QualityIssue,
)


@pytest.fixture
def enhancement_engine():
    return QualityEnhancementEngine()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "content": "Good quality content here", "source_document": {"repo_id": "repo1"}},
        {"id": "2", "content": "", "metadata": {}},  # Empty content
        {"id": "3", "content": "Short", "source_document": {"repo_id": "repo2"}},  # Too short
        {"id": "4", "content": "This has   too    much    whitespace", "source_document": {"repo_id": "repo3"}},
        {"id": "5", "content": "This content is truncated...", "source_document": {"repo_id": "repo4"}},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_quality_issue_creation():
    issue = QualityIssue(
        issue_type="truncation",
        severity="medium",
        field="content",
        message="Content appears truncated",
        suggestion="Ensure complete content",
    )
    assert issue.issue_type == "truncation"
    assert issue.severity == "medium"
    assert issue.field == "content"


def test_enhancement_suggestion_creation():
    suggestion = EnhancementSuggestion(record_id="test1")
    assert suggestion.record_id == "test1"
    assert len(suggestion.issues) == 0
    assert suggestion.auto_fixable is False


def test_enhancement_suggestion_add_issue():
    suggestion = EnhancementSuggestion(record_id="test1")
    issue = QualityIssue("formatting", "low", "content", "Bad format")
    
    suggestion.add_issue(issue)
    assert len(suggestion.issues) == 1
    assert suggestion.issues[0].issue_type == "formatting"


def test_check_truncation_ellipsis(enhancement_engine):
    issue = enhancement_engine._check_truncation("This content is truncated...")
    assert issue is not None
    assert issue.issue_type == "truncation"
    assert issue.severity == "medium"


def test_check_truncation_unicode_ellipsis(enhancement_engine):
    issue = enhancement_engine._check_truncation("This content is truncated…")
    assert issue is not None
    assert issue.issue_type == "truncation"


def test_check_truncation_clean_content(enhancement_engine):
    issue = enhancement_engine._check_truncation("This is complete content.")
    assert issue is None


def test_check_repetition_excessive(enhancement_engine):
    content = "test " * 50  # Highly repetitive
    issue = enhancement_engine._check_repetition(content)
    assert issue is not None
    assert issue.issue_type == "repetition"


def test_check_repetition_normal(enhancement_engine):
    content = "This is normal content with varied words and no excessive repetition"
    issue = enhancement_engine._check_repetition(content)
    assert issue is None


def test_check_encoding_replacement_char(enhancement_engine):
    content = "This has encoding issues: �"
    issue = enhancement_engine._check_encoding(content)
    assert issue is not None
    assert issue.issue_type == "encoding"
    assert issue.severity == "high"


def test_check_encoding_clean(enhancement_engine):
    content = "Clean UTF-8 content: café, naïve, résumé"
    issue = enhancement_engine._check_encoding(content)
    assert issue is None


def test_check_length_empty(enhancement_engine):
    issue = enhancement_engine._check_length("")
    assert issue is not None
    assert issue.issue_type == "length"
    assert issue.severity == "high"


def test_check_length_too_short(enhancement_engine):
    issue = enhancement_engine._check_length("Short")
    assert issue is not None
    assert issue.issue_type == "length"
    assert issue.severity == "medium"


def test_check_length_good(enhancement_engine):
    issue = enhancement_engine._check_length("This is a good length of content.")
    assert issue is None


def test_check_length_too_long(enhancement_engine):
    content = "x" * 150000
    issue = enhancement_engine._check_length(content)
    assert issue is not None
    assert issue.severity == "low"


def test_check_metadata_missing_content(enhancement_engine):
    record = {"id": "1"}
    issues = enhancement_engine._check_metadata(record)
    assert len(issues) > 0
    assert any(i.field == "content" for i in issues)


def test_check_metadata_missing_source(enhancement_engine):
    record = {"id": "1", "content": "test"}
    issues = enhancement_engine._check_metadata(record)
    assert len(issues) > 0
    assert any(i.field == "source_document" for i in issues)


def test_check_metadata_empty_metadata_field(enhancement_engine):
    record = {"id": "1", "content": "test", "metadata": {}}
    issues = enhancement_engine._check_metadata(record)
    assert len(issues) > 0
    assert any(i.field == "metadata" for i in issues)


def test_check_metadata_complete(enhancement_engine):
    record = {"id": "1", "content": "test", "source_document": {"repo": "r1"}, "metadata": {"key": "value"}}
    issues = enhancement_engine._check_metadata(record)
    assert len(issues) == 0


def test_check_formatting_excessive_whitespace(enhancement_engine):
    content = "This has     excessive     whitespace"
    issue = enhancement_engine._check_formatting(content)
    assert issue is not None
    assert issue.issue_type == "formatting"


def test_check_formatting_mixed_line_endings(enhancement_engine):
    content = "Line 1\r\nLine 2\nLine 3"
    issue = enhancement_engine._check_formatting(content)
    assert issue is not None
    assert issue.issue_type == "formatting"


def test_check_formatting_clean(enhancement_engine):
    content = "Clean formatting with normal spacing"
    issue = enhancement_engine._check_formatting(content)
    assert issue is None


def test_analyze_record_good_quality(enhancement_engine):
    record = {"id": "1", "content": "Good quality content", "source_document": {"repo": "r1"}}
    suggestion = enhancement_engine.analyze_record(record)
    
    assert suggestion.record_id == "1"
    assert len(suggestion.issues) == 0


def test_analyze_record_with_issues(enhancement_engine):
    record = {"id": "2", "content": "Short"}
    suggestion = enhancement_engine.analyze_record(record)
    
    assert len(suggestion.issues) > 0
    # Should have length and metadata issues
    assert any(i.issue_type == "length" for i in suggestion.issues)
    assert any(i.issue_type == "metadata" for i in suggestion.issues)


def test_analyze_record_auto_fixable(enhancement_engine):
    record = {"id": "3", "content": "This has     excessive     whitespace"}
    suggestion = enhancement_engine.analyze_record(record)
    
    # Formatting issues should be auto-fixable
    if suggestion.issues:
        assert suggestion.auto_fixable or not all(i.issue_type == "formatting" for i in suggestion.issues)


def test_auto_fix_record_whitespace(enhancement_engine):
    record = {"id": "1", "content": "This   has    extra   whitespace"}
    fixed = enhancement_engine.auto_fix_record(record)
    
    assert fixed["content"] == "This has extra whitespace"


def test_auto_fix_record_line_endings(enhancement_engine):
    record = {"id": "1", "content": "Line 1\r\nLine 2\r\nLine 3"}
    fixed = enhancement_engine.auto_fix_record(record)
    
    assert "\r\n" not in fixed["content"]
    assert "\n" in fixed["content"]


def test_auto_fix_record_trim(enhancement_engine):
    record = {"id": "1", "content": "  padded content  "}
    fixed = enhancement_engine.auto_fix_record(record)
    
    assert fixed["content"] == "padded content"


def test_auto_fix_record_add_metadata(enhancement_engine):
    record = {"id": "1", "content": "test"}
    fixed = enhancement_engine.auto_fix_record(record)
    
    assert "metadata" in fixed


def test_analyze_dataset(enhancement_engine, sample_dataset):
    report = enhancement_engine.analyze_dataset(sample_dataset)
    
    assert report.total_records == 5
    assert report.records_with_issues > 0
    assert report.total_issues > 0
    assert len(report.suggestions) > 0


def test_analyze_dataset_with_output(enhancement_engine, sample_dataset, tmp_path):
    output = tmp_path / "report.json"
    report = enhancement_engine.analyze_dataset(sample_dataset, output)
    
    assert output.exists()
    
    with open(output) as f:
        data = json.load(f)
    
    assert data["total_records"] == report.total_records
    assert data["total_issues"] == report.total_issues


def test_apply_auto_fixes(enhancement_engine, tmp_path):
    source = tmp_path / "source.jsonl"
    records = [
        {"id": "1", "content": "  needs   fixing  "},
        {"id": "2", "content": "Line 1\r\nLine 2"},
    ]
    with open(source, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    output = tmp_path / "fixed.jsonl"
    fixed_count = enhancement_engine.apply_auto_fixes(source, output)
    
    assert fixed_count > 0
    assert output.exists()
    
    with open(output) as f:
        fixed_records = [json.loads(line) for line in f]
    
    assert len(fixed_records) == 2
    assert fixed_records[0]["content"] == "needs fixing"


def test_enhancement_report_to_dict():
    report = EnhancementReport(
        total_records=100,
        records_with_issues=20,
        total_issues=30,
        auto_fixable_count=15,
    )
    
    d = report.to_dict()
    assert d["total_records"] == 100
    assert d["records_with_issues"] == 20
    assert d["issue_rate"] == 20.0


def test_enhancement_report_to_json():
    report = EnhancementReport(
        total_records=10,
        records_with_issues=5,
        total_issues=8,
        auto_fixable_count=3,
    )
    
    json_str = report.to_json()
    data = json.loads(json_str)
    
    assert data["total_records"] == 10
    assert data["auto_fixable_count"] == 3


def test_quality_issue_to_dict():
    issue = QualityIssue(
        issue_type="truncation",
        severity="medium",
        field="content",
        message="Test message",
        suggestion="Test suggestion",
    )
    
    d = issue.to_dict()
    assert d["issue_type"] == "truncation"
    assert d["severity"] == "medium"
    assert d["suggestion"] == "Test suggestion"


def test_enhancement_suggestion_to_dict():
    suggestion = EnhancementSuggestion(
        record_id="test1",
        auto_fixable=True,
        quality_score_before=70.0,
        quality_score_after=85.0,
    )
    suggestion.add_issue(QualityIssue("formatting", "low", "content", "Bad format"))
    
    d = suggestion.to_dict()
    assert d["record_id"] == "test1"
    assert d["auto_fixable"] is True
    assert d["improvement_potential"] == 15.0
