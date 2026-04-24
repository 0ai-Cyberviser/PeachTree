"""Model exporter profiles for PeachTree datasets.

The exporter reads PeachTree JSONL datasets and converts them into common
fine-tuning schemas. It is local-only and does not train models.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EXPORT_FORMATS = ("chatml", "alpaca", "sharegpt")


@dataclass(frozen=True)
class ExportIssue:
    line: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExportStats:
    source_path: str
    output_path: str
    format: str
    records_read: int
    records_written: int
    issues: tuple[ExportIssue, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.issues and self.records_written > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "format": self.format,
            "records_read": self.records_read,
            "records_written": self.records_written,
            "issues": [issue.to_dict() for issue in self.issues],
            "ok": self.ok,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class ValidationReport:
    path: str
    format: str
    records: int
    issues: tuple[ExportIssue, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.issues and self.records > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "format": self.format,
            "records": self.records,
            "issues": [issue.to_dict() for issue in self.issues],
            "ok": self.ok,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def export_format_names() -> tuple[str, ...]:
    return SUPPORTED_EXPORT_FORMATS


def normalize_format(name: str) -> str:
    normalized = name.strip().lower()
    if normalized not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(f"unsupported export format: {name}")
    return normalized


class ModelExporter:
    """Converts PeachTree instruction JSONL into training export schemas."""

    def __init__(
        self,
        system_prompt: str = "You are a helpful, safe, and precise AI assistant.",
        include_metadata: bool = True,
    ) -> None:
        self.system_prompt = system_prompt
        self.include_metadata = include_metadata

    def export_file(
        self,
        source_path: str | Path,
        output_path: str | Path,
        export_format: str,
        limit: int | None = None,
    ) -> ExportStats:
        fmt = normalize_format(export_format)
        source = Path(source_path)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        issues: list[ExportIssue] = []
        written = 0
        read = 0
        lines: list[str] = []

        for line_number, record in self._iter_jsonl(source):
            read += 1
            try:
                exported = self.convert_record(record, fmt)
            except ValueError as exc:
                issues.append(ExportIssue(line_number, str(exc)))
                continue
            lines.append(json.dumps(exported, sort_keys=True, ensure_ascii=False))
            written += 1
            if limit is not None and written >= limit:
                break

        output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return ExportStats(str(source), str(output), fmt, read, written, tuple(issues))

    def convert_record(self, record: dict[str, Any], export_format: str) -> dict[str, Any]:
        fmt = normalize_format(export_format)
        instruction = str(record.get("instruction", "")).strip()
        user_input = str(record.get("input", "")).strip()
        output = str(record.get("output", "")).strip()

        if not instruction:
            raise ValueError("missing instruction")
        if not output:
            raise ValueError("missing output")

        if fmt == "chatml":
            return self._to_chatml(record, instruction, user_input, output)
        if fmt == "alpaca":
            return self._to_alpaca(record, instruction, user_input, output)
        if fmt == "sharegpt":
            return self._to_sharegpt(record, instruction, user_input, output)
        raise ValueError(f"unsupported export format: {export_format}")

    def validate_export(self, path: str | Path, export_format: str) -> ValidationReport:
        fmt = normalize_format(export_format)
        issues: list[ExportIssue] = []
        records = 0
        for line_number, record in self._iter_jsonl(Path(path)):
            records += 1
            issue = self._validate_record(record, fmt)
            if issue:
                issues.append(ExportIssue(line_number, issue))
        return ValidationReport(str(path), fmt, records, tuple(issues))

    def _to_chatml(self, record: dict[str, Any], instruction: str, user_input: str, output: str) -> dict[str, Any]:
        item: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._join_instruction_input(instruction, user_input)},
                {"role": "assistant", "content": output},
            ]
        }
        if self.include_metadata:
            item["metadata"] = self._metadata(record)
        return item

    def _to_alpaca(self, record: dict[str, Any], instruction: str, user_input: str, output: str) -> dict[str, Any]:
        item: dict[str, Any] = {"instruction": instruction, "input": user_input, "output": output}
        if self.include_metadata:
            item["metadata"] = self._metadata(record)
        return item

    def _to_sharegpt(self, record: dict[str, Any], instruction: str, user_input: str, output: str) -> dict[str, Any]:
        item: dict[str, Any] = {
            "conversations": [
                {"from": "system", "value": self.system_prompt},
                {"from": "human", "value": self._join_instruction_input(instruction, user_input)},
                {"from": "gpt", "value": output},
            ]
        }
        record_id = str(record.get("id", "")).strip()
        if record_id:
            item["id"] = record_id
        if self.include_metadata:
            item["metadata"] = self._metadata(record)
        return item

    @staticmethod
    def _join_instruction_input(instruction: str, user_input: str) -> str:
        return f"{instruction}\n\n{user_input}" if user_input else instruction

    @staticmethod
    def _metadata(record: dict[str, Any]) -> dict[str, Any]:
        keys = (
            "id",
            "domain",
            "source_repo",
            "source_path",
            "source_digest",
            "license_id",
            "quality_score",
            "safety_score",
            "record_type",
            "created_at",
        )
        return {key: record[key] for key in keys if key in record}

    @staticmethod
    def _iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                yield line_number, {"instruction": "", "output": "", "_invalid_json": True}
                continue
            if isinstance(value, dict):
                yield line_number, value
            else:
                yield line_number, {"instruction": "", "output": "", "_invalid_type": type(value).__name__}

    def _validate_record(self, record: dict[str, Any], export_format: str) -> str | None:
        fmt = normalize_format(export_format)
        if fmt == "chatml":
            messages = record.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                return "chatml record must contain messages list"
            roles = [message.get("role") for message in messages if isinstance(message, dict)]
            if "user" not in roles or "assistant" not in roles:
                return "chatml messages must include user and assistant roles"
            for message in messages:
                if not isinstance(message, dict) or not message.get("content"):
                    return "chatml message missing content"
            return None
        if fmt == "alpaca":
            if not record.get("instruction"):
                return "alpaca record missing instruction"
            if "input" not in record:
                return "alpaca record missing input field"
            if not record.get("output"):
                return "alpaca record missing output"
            return None
        if fmt == "sharegpt":
            conversations = record.get("conversations")
            if not isinstance(conversations, list) or len(conversations) < 2:
                return "sharegpt record must contain conversations list"
            speakers = [message.get("from") for message in conversations if isinstance(message, dict)]
            if "human" not in speakers or "gpt" not in speakers:
                return "sharegpt conversations must include human and gpt turns"
            for message in conversations:
                if not isinstance(message, dict) or not message.get("value"):
                    return "sharegpt message missing value"
            return None
        return f"unsupported export format: {export_format}"
