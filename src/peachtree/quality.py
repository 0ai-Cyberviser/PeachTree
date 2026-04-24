"""Dataset quality scoring and training readiness gates for PeachTree.

This module is local-only. It scores reviewed PeachTree dataset JSONL files and
produces human-readable gates before downstream model training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class QualityIssue:
    severity: str
    code: str
    message: str
    record_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecordQualityScore:
    record_id: str
    score: int
    passed: bool
    issues: tuple[QualityIssue, ...] = field(default_factory=tuple)
    source_repo: str = "unknown"
    source_path: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["issues"] = [issue.to_dict() for issue in self.issues]
        return data


@dataclass(frozen=True)
class QualityGate:
    name: str
    passed: bool
    threshold: str
    actual: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetQualityReport:
    dataset_path: str
    record_count: int
    average_score: float
    min_score: int
    passed_records: int
    failed_records: int
    gates: tuple[QualityGate, ...]
    records: tuple[RecordQualityScore, ...]
    issues: tuple[QualityIssue, ...] = field(default_factory=tuple)

    @property
    def gate_passed(self) -> bool:
        return all(gate.passed for gate in self.gates)

    @property
    def readiness_level(self) -> str:
        if self.gate_passed and self.average_score >= 90:
            return "excellent"
        if self.gate_passed:
            return "ready"
        if self.average_score >= 70:
            return "review-required"
        return "not-ready"

    def to_dict(self, include_records: bool = True) -> dict[str, Any]:
        data = {
            "dataset_path": self.dataset_path,
            "record_count": self.record_count,
            "average_score": self.average_score,
            "min_score": self.min_score,
            "passed_records": self.passed_records,
            "failed_records": self.failed_records,
            "gate_passed": self.gate_passed,
            "readiness_level": self.readiness_level,
            "gates": [gate.to_dict() for gate in self.gates],
            "issues": [issue.to_dict() for issue in self.issues],
        }
        if include_records:
            data["records"] = [record.to_dict() for record in self.records]
        return data

    def to_json(self, include_records: bool = True) -> str:
        return json.dumps(self.to_dict(include_records=include_records), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Dataset Quality Report",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Records: `{self.record_count}`",
            f"- Average score: `{self.average_score}`",
            f"- Minimum score: `{self.min_score}`",
            f"- Passed records: `{self.passed_records}`",
            f"- Failed records: `{self.failed_records}`",
            f"- Gate passed: `{'yes' if self.gate_passed else 'no'}`",
            f"- Readiness level: `{self.readiness_level}`",
            "",
            "## Gates",
            "",
            "| Gate | Passed | Threshold | Actual | Message |",
            "|---|---|---|---|---|",
        ]
        for gate in self.gates:
            lines.append(
                f"| `{gate.name}` | `{'yes' if gate.passed else 'no'}` | `{gate.threshold}` | `{gate.actual}` | {gate.message} |"
            )
        if self.issues:
            lines += ["", "## Dataset Issues", ""]
            for issue in self.issues:
                lines.append(f"- `{issue.severity}` `{issue.code}`: {issue.message}")
        failed = [record for record in self.records if not record.passed]
        lines += ["", "## Failed Records", ""]
        if not failed:
            lines.append("- None")
        else:
            for record in failed[:100]:
                issue_text = "; ".join(issue.code for issue in record.issues) or "unknown"
                lines.append(f"- `{record.record_id}` score `{record.score}`: {issue_text}")
        return "\n".join(lines)


class DatasetQualityScorer:
    """Scores PeachTree dataset records for training readiness."""

    def __init__(
        self,
        min_record_score: int = 70,
        min_average_score: int = 80,
        max_failed_ratio: float = 0.10,
        min_records: int = 1,
    ) -> None:
        self.min_record_score = min_record_score
        self.min_average_score = min_average_score
        self.max_failed_ratio = max_failed_ratio
        self.min_records = min_records

    def score_dataset(self, dataset_path: str | Path) -> DatasetQualityReport:
        path = Path(dataset_path)
        records = self._read_jsonl(path)
        scores = tuple(self.score_record(record, index) for index, record in enumerate(records, start=1))
        score_values = [record.score for record in scores]
        average = round(mean(score_values), 2) if score_values else 0.0
        min_score = min(score_values) if score_values else 0
        failed = [record for record in scores if not record.passed]
        failed_ratio = len(failed) / len(scores) if scores else 1.0

        dataset_issues: list[QualityIssue] = []
        if not records:
            dataset_issues.append(QualityIssue("error", "empty_dataset", "dataset has no records"))
        if any(record.source_repo == "unknown" for record in scores):
            dataset_issues.append(QualityIssue("warning", "unknown_source_repo", "one or more records lack source_repo"))

        gates = (
            QualityGate(
                "min_records",
                len(records) >= self.min_records,
                f">={self.min_records}",
                str(len(records)),
                "dataset must have enough records",
            ),
            QualityGate(
                "min_average_score",
                average >= self.min_average_score,
                f">={self.min_average_score}",
                str(average),
                "dataset average quality score must meet threshold",
            ),
            QualityGate(
                "max_failed_ratio",
                failed_ratio <= self.max_failed_ratio,
                f"<={self.max_failed_ratio}",
                str(round(failed_ratio, 4)),
                "too many records failed quality scoring",
            ),
            QualityGate(
                "min_record_score",
                all(record.score >= self.min_record_score for record in scores) if scores else False,
                f">={self.min_record_score}",
                str(min_score),
                "all records should meet the minimum record score",
            ),
            QualityGate(
                "provenance_required",
                all(record.source_repo != "unknown" and record.source_path != "unknown" for record in scores) if scores else False,
                "source_repo and source_path present",
                "present" if scores and all(record.source_repo != "unknown" and record.source_path != "unknown" for record in scores) else "missing",
                "all records must preserve provenance",
            ),
        )

        return DatasetQualityReport(
            dataset_path=str(path),
            record_count=len(records),
            average_score=average,
            min_score=min_score,
            passed_records=len(scores) - len(failed),
            failed_records=len(failed),
            gates=gates,
            records=scores,
            issues=tuple(dataset_issues),
        )

    def score_record(self, record: dict[str, Any], index: int) -> RecordQualityScore:
        record_id = str(record.get("id") or f"line-{index}")
        source_repo = str(record.get("source_repo", "unknown") or "unknown")
        source_path = str(record.get("source_path", "unknown") or "unknown")
        issues: list[QualityIssue] = []
        score = 100

        instruction = str(record.get("instruction", "")).strip()
        user_input = str(record.get("input", "")).strip()
        output = str(record.get("output", "")).strip()

        if not instruction:
            score -= 30
            issues.append(QualityIssue("error", "missing_instruction", "record has no instruction", record_id))
        elif len(instruction) < 10:
            score -= 10
            issues.append(QualityIssue("warning", "short_instruction", "instruction is very short", record_id))

        if not output:
            score -= 35
            issues.append(QualityIssue("error", "missing_output", "record has no output", record_id))
        elif len(output) < 20:
            score -= 10
            issues.append(QualityIssue("warning", "short_output", "output is very short", record_id))

        if not user_input:
            score -= 5
            issues.append(QualityIssue("info", "empty_input", "record has no input/context", record_id))

        if source_repo == "unknown":
            score -= 15
            issues.append(QualityIssue("error", "missing_source_repo", "record lacks source_repo provenance", record_id))
        if source_path == "unknown":
            score -= 15
            issues.append(QualityIssue("error", "missing_source_path", "record lacks source_path provenance", record_id))
        if not record.get("source_digest"):
            score -= 10
            issues.append(QualityIssue("warning", "missing_source_digest", "record lacks source digest", record_id))
        if not record.get("license_id"):
            score -= 5
            issues.append(QualityIssue("warning", "missing_license", "record lacks license metadata", record_id))

        safety_score = record.get("safety_score")
        if isinstance(safety_score, (int, float)) and safety_score < 0.8:
            score -= 15
            issues.append(QualityIssue("error", "low_safety_score", "record safety score is below 0.8", record_id))

        quality_score = record.get("quality_score")
        if isinstance(quality_score, (int, float)) and quality_score < 0.5:
            score -= 10
            issues.append(QualityIssue("warning", "low_builder_quality_score", "builder quality score is below 0.5", record_id))

        score = max(0, min(100, score))
        return RecordQualityScore(
            record_id=record_id,
            score=score,
            passed=score >= self.min_record_score and not any(issue.severity == "error" for issue in issues),
            issues=tuple(issues),
            source_repo=source_repo,
            source_path=source_path,
        )

    @staticmethod
    def write_report(report: DatasetQualityReport, json_output: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
        return json_path, md_path

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                value = {"id": "invalid-json", "instruction": "", "output": ""}
            if isinstance(value, dict):
                records.append(value)
        return records
