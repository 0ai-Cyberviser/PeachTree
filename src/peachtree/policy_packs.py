"""Dataset policy packs for PeachTree.

Policy packs compose dataset quality, deduplication, and license gates into
named review profiles for downstream model training decisions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from .dedup import DatasetDeduplicator
from .license_gate import LicenseGate, PERMISSIVE_LICENSES, RESTRICTED_LICENSES
from .quality import DatasetQualityScorer


@dataclass(frozen=True)
class PolicyPack:
    name: str
    description: str
    min_average_score: int
    min_record_score: int
    max_failed_ratio: float
    max_duplicate_ratio: float
    min_records: int
    allowed_licenses: tuple[str, ...]
    denied_licenses: tuple[str, ...]
    allow_unknown_license: bool = False
    requires_human_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BUILTIN_POLICY_PACKS: dict[str, PolicyPack] = {
    "open-safe": PolicyPack(
        name="open-safe",
        description="General open-source safe-training profile with permissive licenses only.",
        min_average_score=80,
        min_record_score=70,
        max_failed_ratio=0.10,
        max_duplicate_ratio=0.05,
        min_records=1,
        allowed_licenses=tuple(sorted(PERMISSIVE_LICENSES)),
        denied_licenses=tuple(sorted(RESTRICTED_LICENSES)),
    ),
    "commercial-ready": PolicyPack(
        name="commercial-ready",
        description="Stricter profile for commercial downstream review. Unknown and copyleft-style licenses are denied.",
        min_average_score=90,
        min_record_score=80,
        max_failed_ratio=0.02,
        max_duplicate_ratio=0.02,
        min_records=10,
        allowed_licenses=tuple(sorted({"apache-2.0", "mit", "bsd-2-clause", "bsd-3-clause", "isc", "cc0-1.0"})),
        denied_licenses=tuple(sorted(RESTRICTED_LICENSES | {"mpl-2.0", "cc-by-4.0"})),
    ),
    "internal-review": PolicyPack(
        name="internal-review",
        description="Permissive internal experimentation profile that allows unknown licenses but still requires review.",
        min_average_score=70,
        min_record_score=60,
        max_failed_ratio=0.25,
        max_duplicate_ratio=0.20,
        min_records=1,
        allowed_licenses=tuple(sorted(PERMISSIVE_LICENSES | {"unknown"})),
        denied_licenses=tuple(sorted(RESTRICTED_LICENSES - {"unknown"})),
        allow_unknown_license=True,
    ),
}


@dataclass(frozen=True)
class PolicyGateResult:
    name: str
    passed: bool
    actual: str
    threshold: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyPackEvaluation:
    dataset_path: str
    pack: PolicyPack
    passed: bool
    gates: tuple[PolicyGateResult, ...]
    quality: dict[str, Any]
    license_gate: dict[str, Any]
    deduplication: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "pack": self.pack.to_dict(),
            "passed": self.passed,
            "gates": [gate.to_dict() for gate in self.gates],
            "quality": self.quality,
            "license_gate": self.license_gate,
            "deduplication": self.deduplication,
            "safety": {
                "does_not_train_models": True,
                "does_not_upload_datasets": True,
                "requires_human_review": self.pack.requires_human_review,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Policy Pack Evaluation",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Policy pack: `{self.pack.name}`",
            f"- Description: {self.pack.description}",
            f"- Passed: `{'yes' if self.passed else 'no'}`",
            f"- Human review required: `{'yes' if self.pack.requires_human_review else 'no'}`",
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
        lines += [
            "",
            "## Summary",
            "",
            f"- Quality average: `{self.quality.get('average_score')}`",
            f"- Quality gate passed: `{self.quality.get('gate_passed')}`",
            f"- Duplicate ratio: `{self.deduplication.get('duplicate_ratio')}`",
            f"- License gate passed: `{self.license_gate.get('passed')}`",
        ]
        return "\n".join(lines)


class PolicyPackEvaluator:
    """Evaluates a dataset against a named policy pack."""

    def list_packs(self) -> tuple[PolicyPack, ...]:
        return tuple(BUILTIN_POLICY_PACKS[name] for name in sorted(BUILTIN_POLICY_PACKS))

    def get_pack(self, name: str) -> PolicyPack:
        key = name.strip().lower()
        if key not in BUILTIN_POLICY_PACKS:
            raise ValueError(f"unknown policy pack: {name}")
        return BUILTIN_POLICY_PACKS[key]

    def evaluate(self, dataset_path: str | Path, pack_name: str = "open-safe") -> PolicyPackEvaluation:
        pack = self.get_pack(pack_name)
        quality_report = DatasetQualityScorer(
            min_record_score=pack.min_record_score,
            min_average_score=pack.min_average_score,
            max_failed_ratio=pack.max_failed_ratio,
            min_records=pack.min_records,
        ).score_dataset(dataset_path)
        dedup_report = DatasetDeduplicator().analyze(dataset_path)
        license_report = LicenseGate(
            allowed_licenses=set(pack.allowed_licenses),
            denied_licenses=set(pack.denied_licenses),
            allow_unknown=pack.allow_unknown_license,
        ).evaluate(dataset_path)

        gates = (
            PolicyGateResult(
                "quality_gate",
                quality_report.gate_passed,
                "quality gates pass",
                "passed" if quality_report.gate_passed else "failed",
                "dataset must satisfy quality scoring gates",
            ),
            PolicyGateResult(
                "duplicate_ratio",
                dedup_report.duplicate_ratio <= pack.max_duplicate_ratio,
                f"<={pack.max_duplicate_ratio}",
                str(dedup_report.duplicate_ratio),
                "dataset duplicate ratio must stay below policy limit",
            ),
            PolicyGateResult(
                "license_gate",
                license_report.passed,
                "all records allowed by license policy",
                "passed" if license_report.passed else "failed",
                "dataset licenses must comply with policy pack",
            ),
        )
        passed = all(gate.passed for gate in gates)
        return PolicyPackEvaluation(
            dataset_path=str(dataset_path),
            pack=pack,
            passed=passed,
            gates=gates,
            quality=quality_report.to_dict(include_records=False),
            license_gate=license_report.to_dict(include_findings=False),
            deduplication=dedup_report.to_dict(),
        )

    @staticmethod
    def write_report(evaluation: PolicyPackEvaluation, json_output: str | Path, markdown_output: str | Path | None = None) -> tuple[Path, Path | None]:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(evaluation.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(evaluation.to_markdown() + "\n", encoding="utf-8")
        return json_path, md_path
