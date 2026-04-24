"""Deterministic dataset deduplication for PeachTree."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def record_signature(record: dict[str, Any]) -> str:
    payload = {
        "instruction": normalized_text(str(record.get("instruction", ""))),
        "input": normalized_text(str(record.get("input", ""))),
        "output": normalized_text(str(record.get("output", ""))),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DuplicateGroup:
    signature: str
    kept_id: str
    duplicate_ids: tuple[str, ...]
    count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DedupReport:
    source_path: str
    output_path: str
    input_count: int
    output_count: int
    duplicate_count: int
    groups: tuple[DuplicateGroup, ...] = field(default_factory=tuple)

    @property
    def duplicate_ratio(self) -> float:
        return round(self.duplicate_count / self.input_count, 4) if self.input_count else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "duplicate_count": self.duplicate_count,
            "duplicate_ratio": self.duplicate_ratio,
            "groups": [group.to_dict() for group in self.groups],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Deduplication Report",
            "",
            f"- Source: `{self.source_path}`",
            f"- Output: `{self.output_path}`",
            f"- Input records: `{self.input_count}`",
            f"- Output records: `{self.output_count}`",
            f"- Duplicate records removed: `{self.duplicate_count}`",
            f"- Duplicate ratio: `{self.duplicate_ratio}`",
            "",
            "## Duplicate Groups",
            "",
        ]
        if not self.groups:
            lines.append("- None")
        else:
            for group in self.groups[:100]:
                lines.append(f"- Kept `{group.kept_id}`; removed `{', '.join(group.duplicate_ids)}`")
        return "\n".join(lines)


class DatasetDeduplicator:
    """Removes exact normalized instruction/input/output duplicates."""

    def analyze(self, source_path: str | Path) -> DedupReport:
        return self.deduplicate(source_path, output_path="", write_output=False)

    def deduplicate(
        self,
        source_path: str | Path,
        output_path: str | Path,
        write_output: bool = True,
    ) -> DedupReport:
        source = Path(source_path)
        records = self._read_jsonl(source)
        seen: dict[str, dict[str, Any]] = {}
        kept: list[dict[str, Any]] = []
        duplicate_map: dict[str, list[str]] = {}

        for index, record in enumerate(records, start=1):
            signature = record_signature(record)
            record_id = str(record.get("id") or f"line-{index}")
            if signature in seen:
                duplicate_map.setdefault(signature, []).append(record_id)
            else:
                seen[signature] = record
                kept.append(record)

        out = Path(output_path) if output_path else Path("")
        if write_output:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("\n".join(json.dumps(record, sort_keys=True, ensure_ascii=False) for record in kept) + ("\n" if kept else ""), encoding="utf-8")

        groups = []
        for signature, duplicate_ids in sorted(duplicate_map.items()):
            kept_record = seen[signature]
            kept_id = str(kept_record.get("id") or signature[:16])
            groups.append(DuplicateGroup(signature, kept_id, tuple(sorted(duplicate_ids)), len(duplicate_ids) + 1))

        return DedupReport(
            source_path=str(source),
            output_path=str(out) if output_path else "",
            input_count=len(records),
            output_count=len(kept),
            duplicate_count=sum(len(ids) for ids in duplicate_map.values()),
            groups=tuple(groups),
        )

    def write_report(self, report: DedupReport, json_output: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
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
                continue
            if isinstance(value, dict):
                records.append(value)
        return records
