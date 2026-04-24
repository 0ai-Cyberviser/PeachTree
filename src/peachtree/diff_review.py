"""Dataset diff and review reports for PeachTree.

This module compares reviewed PeachTree dataset JSONL files and produces
human-readable change reports before any downstream training run.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class DatasetRecordSummary:
    record_id: str
    digest: str
    source_repo: str = "unknown"
    source_path: str = "unknown"
    source_digest: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetFingerprint:
    path: str
    file_digest: str
    record_count: int
    record_ids: tuple[str, ...]
    source_repos: tuple[str, ...]
    source_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetDiff:
    baseline_path: str
    candidate_path: str
    baseline_count: int
    candidate_count: int
    added_ids: tuple[str, ...] = field(default_factory=tuple)
    removed_ids: tuple[str, ...] = field(default_factory=tuple)
    changed_ids: tuple[str, ...] = field(default_factory=tuple)
    unchanged_count: int = 0
    new_source_repos: tuple[str, ...] = field(default_factory=tuple)
    removed_source_repos: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def record_delta(self) -> int:
        return self.candidate_count - self.baseline_count

    @property
    def risk_score(self) -> int:
        score = 0
        score += min(len(self.added_ids), 25)
        score += min(len(self.removed_ids) * 2, 40)
        score += min(len(self.changed_ids), 25)
        score += min(len(self.new_source_repos) * 5, 20)
        score += len(self.warnings) * 10
        return min(score, 100)

    @property
    def review_required(self) -> bool:
        return bool(self.added_ids or self.removed_ids or self.changed_ids or self.new_source_repos or self.warnings)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["record_delta"] = self.record_delta
        data["risk_score"] = self.risk_score
        data["review_required"] = self.review_required
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Dataset Diff Review",
            "",
            f"- Baseline: `{self.baseline_path}`",
            f"- Candidate: `{self.candidate_path}`",
            f"- Baseline records: `{self.baseline_count}`",
            f"- Candidate records: `{self.candidate_count}`",
            f"- Record delta: `{self.record_delta}`",
            f"- Risk score: `{self.risk_score}/100`",
            f"- Review required: `{'yes' if self.review_required else 'no'}`",
            "",
            "## Change Summary",
            "",
            f"- Added records: `{len(self.added_ids)}`",
            f"- Removed records: `{len(self.removed_ids)}`",
            f"- Changed records: `{len(self.changed_ids)}`",
            f"- New source repos: `{len(self.new_source_repos)}`",
            f"- Removed source repos: `{len(self.removed_source_repos)}`",
        ]
        if self.warnings:
            lines += ["", "## Warnings", ""]
            lines.extend(f"- {warning}" for warning in self.warnings)
        lines += ["", "## Added IDs", ""]
        if self.added_ids:
            lines.extend(f"- `{value}`" for value in self.added_ids[:100])
        else:
            lines.append("- None")
        lines += ["", "## Removed IDs", ""]
        if self.removed_ids:
            lines.extend(f"- `{value}`" for value in self.removed_ids[:100])
        else:
            lines.append("- None")
        lines += ["", "## Changed IDs", ""]
        if self.changed_ids:
            lines.extend(f"- `{value}`" for value in self.changed_ids[:100])
        else:
            lines.append("- None")
        return "\n".join(lines)


class DatasetDiffReviewer:
    """Compares PeachTree datasets and emits reviewable reports."""

    def fingerprint(self, dataset_path: str | Path) -> DatasetFingerprint:
        path = Path(dataset_path)
        summaries = self._summaries(path)
        return DatasetFingerprint(
            path=str(path),
            file_digest=sha256_bytes(path.read_bytes()) if path.exists() else "",
            record_count=len(summaries),
            record_ids=tuple(sorted(summaries)),
            source_repos=tuple(sorted({item.source_repo for item in summaries.values()})),
            source_paths=tuple(sorted({item.source_path for item in summaries.values()})),
        )

    def compare(self, baseline_path: str | Path, candidate_path: str | Path) -> DatasetDiff:
        baseline = self._summaries(Path(baseline_path))
        candidate = self._summaries(Path(candidate_path))
        baseline_ids = set(baseline)
        candidate_ids = set(candidate)
        added = tuple(sorted(candidate_ids - baseline_ids))
        removed = tuple(sorted(baseline_ids - candidate_ids))
        shared = baseline_ids & candidate_ids
        changed = tuple(sorted(record_id for record_id in shared if baseline[record_id].digest != candidate[record_id].digest))
        unchanged = len(shared) - len(changed)
        baseline_repos = {item.source_repo for item in baseline.values()}
        candidate_repos = {item.source_repo for item in candidate.values()}
        warnings = self._warnings(baseline, candidate, added, removed, changed)
        return DatasetDiff(
            baseline_path=str(baseline_path),
            candidate_path=str(candidate_path),
            baseline_count=len(baseline),
            candidate_count=len(candidate),
            added_ids=added,
            removed_ids=removed,
            changed_ids=changed,
            unchanged_count=unchanged,
            new_source_repos=tuple(sorted(candidate_repos - baseline_repos)),
            removed_source_repos=tuple(sorted(baseline_repos - candidate_repos)),
            warnings=tuple(warnings),
        )

    def write_reports(self, diff: DatasetDiff, json_output: str | Path, markdown_output: str | Path) -> tuple[Path, Path]:
        json_path = Path(json_output)
        md_path = Path(markdown_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(diff.to_json() + "\n", encoding="utf-8")
        md_path.write_text(diff.to_markdown() + "\n", encoding="utf-8")
        return json_path, md_path

    def _summaries(self, path: Path) -> dict[str, DatasetRecordSummary]:
        if not path.exists():
            return {}
        summaries: dict[str, DatasetRecordSummary] = {}
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                record = {"id": f"invalid-json-line-{index}", "_raw": line}
            if not isinstance(record, dict):
                record = {"id": f"invalid-record-line-{index}", "_raw": repr(record)}
            record_id = str(record.get("id") or sha256_bytes(json.dumps(record, sort_keys=True).encode())[:16])
            digest = sha256_bytes(json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8"))
            summaries[record_id] = DatasetRecordSummary(
                record_id=record_id,
                digest=digest,
                source_repo=str(record.get("source_repo", "unknown")),
                source_path=str(record.get("source_path", "unknown")),
                source_digest=str(record.get("source_digest", "unknown")),
            )
        return summaries

    @staticmethod
    def _warnings(
        baseline: dict[str, DatasetRecordSummary],
        candidate: dict[str, DatasetRecordSummary],
        added: tuple[str, ...],
        removed: tuple[str, ...],
        changed: tuple[str, ...],
    ) -> list[str]:
        warnings: list[str] = []
        if not candidate:
            warnings.append("candidate dataset is empty")
        if len(removed) > len(baseline) * 0.25 and baseline:
            warnings.append("more than 25% of baseline records were removed")
        if len(added) > max(50, len(baseline) * 0.5):
            warnings.append("large number of records added; manual review recommended")
        candidate_unknown = [record for record in candidate.values() if record.source_repo == "unknown"]
        if candidate_unknown:
            warnings.append("candidate contains records without source_repo provenance")
        if changed:
            warnings.append("existing record IDs changed content")
        return warnings
