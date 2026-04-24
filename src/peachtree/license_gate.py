"""License and compliance gates for PeachTree datasets.

This module is local-only. It evaluates license metadata already present in
PeachTree JSONL records and emits a review report before downstream training.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


PERMISSIVE_LICENSES = frozenset(
    {
        "apache-2.0",
        "mit",
        "bsd-2-clause",
        "bsd-3-clause",
        "isc",
        "mpl-2.0",
        "cc-by-4.0",
        "cc0-1.0",
        "unlicense",
    }
)

RESTRICTED_LICENSES = frozenset(
    {
        "agpl-3.0",
        "gpl-2.0",
        "gpl-3.0",
        "lgpl-2.1",
        "lgpl-3.0",
        "sspl-1.0",
        "cc-by-sa-4.0",
        "cc-by-nc-4.0",
        "proprietary",
        "unknown",
        "",
    }
)


@dataclass(frozen=True)
class LicenseFinding:
    record_id: str
    license_id: str
    decision: str
    reason: str
    source_repo: str = "unknown"
    source_path: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LicenseGateReport:
    dataset_path: str
    allowed_licenses: tuple[str, ...]
    denied_licenses: tuple[str, ...]
    allow_unknown: bool
    record_count: int
    allowed_count: int
    denied_count: int
    unknown_count: int
    license_counts: dict[str, int]
    findings: tuple[LicenseFinding, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.denied_count == 0 and (self.allow_unknown or self.unknown_count == 0)

    def to_dict(self, include_findings: bool = True) -> dict[str, Any]:
        data = {
            "dataset_path": self.dataset_path,
            "allowed_licenses": list(self.allowed_licenses),
            "denied_licenses": list(self.denied_licenses),
            "allow_unknown": self.allow_unknown,
            "record_count": self.record_count,
            "allowed_count": self.allowed_count,
            "denied_count": self.denied_count,
            "unknown_count": self.unknown_count,
            "license_counts": self.license_counts,
            "passed": self.passed,
        }
        if include_findings:
            data["findings"] = [finding.to_dict() for finding in self.findings]
        return data

    def to_json(self, include_findings: bool = True) -> str:
        return json.dumps(self.to_dict(include_findings=include_findings), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree License Gate Report",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Records: `{self.record_count}`",
            f"- Allowed: `{self.allowed_count}`",
            f"- Denied: `{self.denied_count}`",
            f"- Unknown: `{self.unknown_count}`",
            f"- Passed: `{'yes' if self.passed else 'no'}`",
            "",
            "## License Counts",
            "",
            "| License | Records |",
            "|---|---:|",
        ]
        for license_id, count in sorted(self.license_counts.items()):
            lines.append(f"| `{license_id}` | {count} |")

        problem_findings = [f for f in self.findings if f.decision != "allow"]
        lines += ["", "## Findings Requiring Review", ""]
        if not problem_findings:
            lines.append("- None")
        else:
            for finding in problem_findings[:100]:
                lines.append(
                    f"- `{finding.decision}` `{finding.license_id}` in `{finding.source_path}`: {finding.reason}"
                )
        return "\n".join(lines)


class LicenseGate:
    """Evaluates dataset records against license allow/deny rules."""

    def __init__(
        self,
        allowed_licenses: set[str] | None = None,
        denied_licenses: set[str] | None = None,
        allow_unknown: bool = False,
    ) -> None:
        self.allowed_licenses = {self._normalize(value) for value in (allowed_licenses or set(PERMISSIVE_LICENSES))}
        self.denied_licenses = {self._normalize(value) for value in (denied_licenses or set(RESTRICTED_LICENSES))}
        self.allow_unknown = allow_unknown

    def evaluate(self, dataset_path: str | Path) -> LicenseGateReport:
        path = Path(dataset_path)
        records = self._read_jsonl(path)
        findings: list[LicenseFinding] = []
        counts: Counter[str] = Counter()

        allowed_count = 0
        denied_count = 0
        unknown_count = 0

        for index, record in enumerate(records, start=1):
            record_id = str(record.get("id") or f"line-{index}")
            license_id = self._normalize(str(record.get("license_id", "unknown") or "unknown"))
            counts[license_id] += 1
            source_repo = str(record.get("source_repo", "unknown") or "unknown")
            source_path = str(record.get("source_path", "unknown") or "unknown")

            if license_id == "unknown":
                unknown_count += 1
                if self.allow_unknown:
                    decision = "allow"
                    reason = "unknown license allowed by policy override"
                    allowed_count += 1
                else:
                    decision = "review"
                    reason = "unknown license requires manual review"
            elif license_id in self.denied_licenses:
                decision = "deny"
                reason = "license is denied by policy"
                denied_count += 1
            elif license_id in self.allowed_licenses:
                decision = "allow"
                reason = "license is allowed by policy"
                allowed_count += 1
            else:
                decision = "review"
                reason = "license is neither explicitly allowed nor denied"
                denied_count += 1

            findings.append(
                LicenseFinding(
                    record_id=record_id,
                    license_id=license_id,
                    decision=decision,
                    reason=reason,
                    source_repo=source_repo,
                    source_path=source_path,
                )
            )

        return LicenseGateReport(
            dataset_path=str(path),
            allowed_licenses=tuple(sorted(self.allowed_licenses)),
            denied_licenses=tuple(sorted(self.denied_licenses)),
            allow_unknown=self.allow_unknown,
            record_count=len(records),
            allowed_count=allowed_count,
            denied_count=denied_count,
            unknown_count=unknown_count,
            license_counts=dict(sorted(counts.items())),
            findings=tuple(findings),
        )

    @staticmethod
    def write_report(report: LicenseGateReport, json_output: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
        return json_path, md_path

    @classmethod
    def _normalize(cls, value: str) -> str:
        value = value.strip().lower()
        aliases = {
            "apache": "apache-2.0",
            "apache2": "apache-2.0",
            "apache 2.0": "apache-2.0",
            "bsd": "bsd-3-clause",
            "bsd-3": "bsd-3-clause",
            "bsd-2": "bsd-2-clause",
            "gpl": "gpl-3.0",
            "agpl": "agpl-3.0",
            "lgpl": "lgpl-3.0",
            "none": "unknown",
            "": "unknown",
        }
        return aliases.get(value, value)

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
