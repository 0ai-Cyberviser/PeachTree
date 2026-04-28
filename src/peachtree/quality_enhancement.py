"""
PeachTree Quality Enhancement Engine

Automated quality improvement suggestions and fixes for dataset records.
Detects common quality issues and provides enhancement recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import re


@dataclass
class QualityIssue:
    """Single quality issue detected in a record"""
    issue_type: str  # truncation, repetition, encoding, formatting, length, metadata
    severity: str  # low, medium, high
    field: str
    message: str
    suggestion: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class EnhancementSuggestion:
    """Quality enhancement suggestion for a record"""
    record_id: str
    issues: list[QualityIssue] = field(default_factory=list)
    auto_fixable: bool = False
    quality_score_before: float = 0.0
    quality_score_after: float = 0.0
    
    def add_issue(self, issue: QualityIssue) -> None:
        """Add quality issue"""
        self.issues.append(issue)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "issues": [i.to_dict() for i in self.issues],
            "auto_fixable": self.auto_fixable,
            "quality_score_before": self.quality_score_before,
            "quality_score_after": self.quality_score_after,
            "improvement_potential": self.quality_score_after - self.quality_score_before,
        }


@dataclass
class EnhancementReport:
    """Report of quality enhancement analysis"""
    total_records: int
    records_with_issues: int
    total_issues: int
    auto_fixable_count: int
    suggestions: list[EnhancementSuggestion] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "records_with_issues": self.records_with_issues,
            "total_issues": self.total_issues,
            "auto_fixable_count": self.auto_fixable_count,
            "issue_rate": (self.records_with_issues / self.total_records * 100) if self.total_records > 0 else 0,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class QualityEnhancementEngine:
    """Detect quality issues and suggest improvements"""
    
    def __init__(self):
        """Initialize quality enhancement engine"""
        self.min_content_length = 10
        self.max_content_length = 100000
        self.repetition_threshold = 5
    
    def _check_truncation(self, content: str) -> QualityIssue | None:
        """Check for truncated content"""
        if not content:
            return None
        
        # Check for common truncation patterns
        truncation_patterns = [
            r'\.\.\.$',  # Ends with ...
            r'…$',       # Ends with ellipsis
            r'\[truncated\]$',
            r'\(continued\)$',
        ]
        
        for pattern in truncation_patterns:
            if re.search(pattern, content.strip(), re.IGNORECASE):
                return QualityIssue(
                    issue_type="truncation",
                    severity="medium",
                    field="content",
                    message="Content appears to be truncated",
                    suggestion="Ensure complete content is included",
                )
        
        return None
    
    def _check_repetition(self, content: str) -> QualityIssue | None:
        """Check for excessive repetition"""
        if not content or len(content) < 50:
            return None
        
        words = content.split()
        if len(words) < 10:
            return None
        
        # Check for repeated sequences
        word_counts: dict[str, int] = {}
        for word in words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # Find most repeated word
        max_count = max(word_counts.values()) if word_counts else 0
        
        if max_count > self.repetition_threshold and max_count > len(words) * 0.3:
            return QualityIssue(
                issue_type="repetition",
                severity="medium",
                field="content",
                message=f"Excessive word repetition detected (max: {max_count} times)",
                suggestion="Review content for unnecessary repetition",
            )
        
        return None
    
    def _check_encoding(self, content: str) -> QualityIssue | None:
        """Check for encoding issues"""
        if not content:
            return None
        
        # Check for common encoding artifacts
        encoding_issues = [
            ('�', 'replacement character'),
            ('\ufffd', 'replacement character'),
            ('Ã©', 'mojibake (incorrect é)'),
            ('Ã¨', 'mojibake (incorrect è)'),
        ]
        
        for pattern, name in encoding_issues:
            if pattern in content:
                return QualityIssue(
                    issue_type="encoding",
                    severity="high",
                    field="content",
                    message=f"Encoding issue detected: {name}",
                    suggestion="Re-encode content with proper UTF-8 encoding",
                )
        
        return None
    
    def _check_length(self, content: str) -> QualityIssue | None:
        """Check for content length issues"""
        if not content:
            return QualityIssue(
                issue_type="length",
                severity="high",
                field="content",
                message="Content is empty",
                suggestion="Add meaningful content",
            )
        
        if len(content) < self.min_content_length:
            return QualityIssue(
                issue_type="length",
                severity="medium",
                field="content",
                message=f"Content is very short ({len(content)} chars)",
                suggestion=f"Consider expanding content (minimum: {self.min_content_length} chars)",
            )
        
        if len(content) > self.max_content_length:
            return QualityIssue(
                issue_type="length",
                severity="low",
                field="content",
                message=f"Content is very long ({len(content)} chars)",
                suggestion="Consider splitting into multiple records",
            )
        
        return None
    
    def _check_metadata(self, record: dict[str, Any]) -> list[QualityIssue]:
        """Check for metadata issues"""
        issues = []
        
        # Check for required fields
        if "content" not in record:
            issues.append(QualityIssue(
                issue_type="metadata",
                severity="high",
                field="content",
                message="Missing required 'content' field",
                suggestion="Add content field to record",
            ))
        
        if "source_document" not in record:
            issues.append(QualityIssue(
                issue_type="metadata",
                severity="medium",
                field="source_document",
                message="Missing source_document provenance",
                suggestion="Add source_document for traceability",
            ))
        
        # Check for empty metadata
        if "metadata" in record and not record["metadata"]:
            issues.append(QualityIssue(
                issue_type="metadata",
                severity="low",
                field="metadata",
                message="Metadata field is empty",
                suggestion="Add descriptive metadata",
            ))
        
        return issues
    
    def _check_formatting(self, content: str) -> QualityIssue | None:
        """Check for formatting issues"""
        if not content:
            return None
        
        # Check for excessive whitespace
        if re.search(r'\s{5,}', content):
            return QualityIssue(
                issue_type="formatting",
                severity="low",
                field="content",
                message="Excessive whitespace detected",
                suggestion="Normalize whitespace",
            )
        
        # Check for mixed line endings
        if '\r\n' in content and '\n' in content.replace('\r\n', ''):
            return QualityIssue(
                issue_type="formatting",
                severity="low",
                field="content",
                message="Mixed line endings detected",
                suggestion="Normalize to Unix line endings (\\n)",
            )
        
        return None
    
    def analyze_record(self, record: dict[str, Any]) -> EnhancementSuggestion:
        """Analyze single record for quality issues"""
        record_id = record.get("id", "unknown")
        suggestion = EnhancementSuggestion(record_id=record_id)
        
        # Get content
        content = record.get("content", "")
        
        # Run all checks
        checks = [
            self._check_truncation(content),
            self._check_repetition(content),
            self._check_encoding(content),
            self._check_length(content),
            self._check_formatting(content),
        ]
        
        # Add content issues
        for issue in checks:
            if issue:
                suggestion.add_issue(issue)
        
        # Add metadata issues
        for issue in self._check_metadata(record):
            suggestion.add_issue(issue)
        
        # Determine auto-fixability
        auto_fix_types = {"formatting", "length"}
        if suggestion.issues:
            suggestion.auto_fixable = all(
                i.issue_type in auto_fix_types for i in suggestion.issues
            )
        
        # Estimate quality scores
        suggestion.quality_score_before = self._estimate_quality(record)
        suggestion.quality_score_after = min(100.0, suggestion.quality_score_before + len(suggestion.issues) * 5)
        
        return suggestion
    
    def _estimate_quality(self, record: dict[str, Any]) -> float:
        """Estimate quality score (0-100)"""
        score = 100.0
        
        content = record.get("content", "")
        
        # Penalize for length issues
        if not content:
            score -= 50
        elif len(content) < self.min_content_length:
            score -= 20
        
        # Penalize for missing metadata
        if "source_document" not in record:
            score -= 10
        
        if "metadata" not in record or not record["metadata"]:
            score -= 5
        
        return max(0.0, score)
    
    def auto_fix_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Automatically fix common quality issues"""
        fixed = record.copy()
        
        content = fixed.get("content", "")
        
        if content:
            # Fix formatting issues
            # Normalize whitespace
            content = re.sub(r'\s+', ' ', content)
            
            # Normalize line endings
            content = content.replace('\r\n', '\n')
            
            # Trim
            content = content.strip()
            
            fixed["content"] = content
        
        # Ensure metadata exists
        if "metadata" not in fixed:
            fixed["metadata"] = {}
        
        return fixed
    
    def analyze_dataset(
        self,
        dataset_path: Path | str,
        output_path: Path | str | None = None,
    ) -> EnhancementReport:
        """
        Analyze entire dataset for quality issues
        
        Args:
            dataset_path: Path to dataset JSONL file
            output_path: Optional path to save report
        
        Returns:
            EnhancementReport with all suggestions
        """
        dataset_path = Path(dataset_path)
        
        total_records = 0
        records_with_issues = 0
        total_issues = 0
        auto_fixable_count = 0
        suggestions = []
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_records += 1
                
                try:
                    record = json.loads(line)
                    suggestion = self.analyze_record(record)
                    
                    if suggestion.issues:
                        records_with_issues += 1
                        total_issues += len(suggestion.issues)
                        if suggestion.auto_fixable:
                            auto_fixable_count += 1
                        suggestions.append(suggestion)
                
                except json.JSONDecodeError:
                    continue
        
        report = EnhancementReport(
            total_records=total_records,
            records_with_issues=records_with_issues,
            total_issues=total_issues,
            auto_fixable_count=auto_fixable_count,
            suggestions=suggestions,
        )
        
        # Save report if requested
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report.to_json() + "\n", encoding="utf-8")
        
        return report
    
    def apply_auto_fixes(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> int:
        """
        Apply automatic fixes to dataset
        
        Args:
            source_path: Source dataset path
            output_path: Output dataset path
        
        Returns:
            Number of records fixed
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fixed_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    fixed = self.auto_fix_record(record)
                    f_out.write(json.dumps(fixed) + "\n")
                    
                    # Count as fixed if content changed
                    if fixed != record:
                        fixed_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return fixed_count
