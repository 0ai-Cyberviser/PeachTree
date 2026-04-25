from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import platform
import shutil
import sys
from typing import Iterable, Literal

from .models import SourceDocument
from .safety import SafetyGate

CheckStatus = Literal["pass", "warn", "fail"]


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: CheckStatus
    message: str
    detail: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    root: str
    checks: tuple[DoctorCheck, ...]

    @property
    def failures(self) -> tuple[DoctorCheck, ...]:
        return tuple(check for check in self.checks if check.status == "fail")

    @property
    def warnings(self) -> tuple[DoctorCheck, ...]:
        return tuple(check for check in self.checks if check.status == "warn")

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "root": self.root,
            "summary": {
                "checks": len(self.checks),
                "failures": len(self.failures),
                "warnings": len(self.warnings),
            },
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
        lines = [
            "# PeachTree Doctor",
            "",
            f"Root: `{self.root}`",
            f"Status: {'OK' if self.ok else 'NEEDS ATTENTION'}",
            "",
            "| Status | Check | Message |",
            "|---|---|---|",
        ]
        for check in self.checks:
            lines.append(f"| {icon[check.status]} | `{check.name}` | {check.message} |")
        if self.failures:
            lines.extend(["", "## Required fixes"])
            for check in self.failures:
                lines.append(f"- `{check.name}`: {check.message}")
        if self.warnings:
            lines.extend(["", "## Warnings"])
            for check in self.warnings:
                lines.append(f"- `{check.name}`: {check.message}")
        return "\n".join(lines)


class PeachTreeDoctor:
    """Maintainer health checks for local PeachTree workspaces.

    The doctor is intentionally local-only. It does not contact GitHub, upload datasets,
    run training jobs, or execute fuzzing targets.
    """

    REQUIRED_DIRS = (
        "data/raw",
        "data/datasets",
        "data/manifests",
        "data/exports",
        "reports",
        "dist",
    )
    EXPECTED_COMMANDS = {
        "policy",
        "plan",
        "ingest-local",
        "build",
        "audit",
        "github-owned",
        "github-plan",
        "graph",
        "lineage",
        "ecosystem",
        "export",
        "validate-export",
        "diff",
        "update-plan",
        "review-report",
        "score",
        "dedup",
        "readiness",
        "policy-pack",
        "license-gate",
        "model-card",
        "registry",
        "sign",
        "sbom",
        "bundle",
        "handoff",
        "lora-card",
        "train-plan",
    }

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def run(
        self,
        *,
        dataset: str | Path | None = None,
        command_names: Iterable[str] | None = None,
    ) -> DoctorReport:
        checks: list[DoctorCheck] = []
        checks.append(self._check_python_version())
        checks.append(self._check_project_layout())
        checks.extend(self._check_directories())
        checks.append(self._check_gitignore())
        checks.append(self._check_optional_tool("git"))
        checks.append(self._check_optional_tool("gh"))
        checks.append(self._check_safety_gate())
        if command_names is not None:
            checks.append(self._check_cli_commands(set(command_names)))
        if dataset:
            checks.append(self._check_dataset(Path(dataset)))
        ok = all(check.status != "fail" for check in checks)
        return DoctorReport(ok=ok, root=str(self.root), checks=tuple(checks))

    def _check_python_version(self) -> DoctorCheck:
        version = sys.version_info
        if version >= (3, 10):
            return DoctorCheck(
                "python-version",
                "pass",
                f"Python {platform.python_version()} is supported.",
                {"required": ">=3.10", "actual": platform.python_version()},
            )
        return DoctorCheck(
            "python-version",
            "fail",
            f"Python {platform.python_version()} is too old; PeachTree requires >=3.10.",
            {"required": ">=3.10", "actual": platform.python_version()},
        )

    def _check_project_layout(self) -> DoctorCheck:
        pyproject = self.root / "pyproject.toml"
        package_dir = self.root / "src" / "peachtree"
        if pyproject.exists() and package_dir.exists():
            return DoctorCheck("project-layout", "pass", "pyproject.toml and src/peachtree are present.")
        missing = [str(path.relative_to(self.root)) for path in (pyproject, package_dir) if not path.exists()]
        return DoctorCheck("project-layout", "fail", f"Missing expected project paths: {', '.join(missing)}")

    def _check_directories(self) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []
        for rel in self.REQUIRED_DIRS:
            path = self.root / rel
            if path.exists() and path.is_dir():
                checks.append(DoctorCheck(f"dir:{rel}", "pass", f"`{rel}` exists."))
            else:
                checks.append(
                    DoctorCheck(
                        f"dir:{rel}",
                        "warn",
                        f"`{rel}` is missing. Create it before running full dataset workflows.",
                    )
                )
        return checks

    def _check_gitignore(self) -> DoctorCheck:
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            return DoctorCheck(
                "gitignore-datasets",
                "warn",
                ".gitignore is missing; generated datasets should be ignored until reviewed.",
            )
        text = gitignore.read_text(encoding="utf-8", errors="replace")
        required_patterns = ("data/raw", "data/datasets", "data/exports", "dist")
        missing = [pattern for pattern in required_patterns if pattern not in text]
        if not missing:
            return DoctorCheck("gitignore-datasets", "pass", "generated dataset/release paths are ignored.")
        return DoctorCheck(
            "gitignore-datasets",
            "warn",
            "Generated artifact paths are not fully ignored.",
            {"missing_patterns": missing},
        )

    @staticmethod
    def _check_optional_tool(name: str) -> DoctorCheck:
        path = shutil.which(name)
        if path:
            return DoctorCheck(f"tool:{name}", "pass", f"`{name}` is available.", {"path": path})
        status: CheckStatus = "warn" if name in {"gh", "git"} else "pass"
        return DoctorCheck(f"tool:{name}", status, f"`{name}` was not found on PATH.")

    def _check_safety_gate(self) -> DoctorCheck:
        gate = SafetyGate(allow_unknown_license=False)
        secret_doc = SourceDocument(
            repo_name="doctor",
            path="fixture.txt",
            content="api_key = '1234567890abcdef1234567890abcdef'",
            license_id="apache-2.0",
        )
        unknown_license_doc = SourceDocument(
            repo_name="doctor",
            path="fixture.md",
            content="safe content",
            license_id="unknown",
        )
        secret_decision = gate.check_document(secret_doc)
        license_decision = gate.check_document(unknown_license_doc)
        if not secret_decision.allowed and not license_decision.allowed:
            return DoctorCheck(
                "safety-gate",
                "pass",
                "SafetyGate rejects secret-like content and unknown licenses in strict mode.",
            )
        return DoctorCheck(
            "safety-gate",
            "fail",
            "SafetyGate smoke test did not fail closed.",
            {
                "secret_allowed": secret_decision.allowed,
                "unknown_license_allowed": license_decision.allowed,
            },
        )

    def _check_cli_commands(self, command_names: set[str]) -> DoctorCheck:
        missing = sorted(self.EXPECTED_COMMANDS - command_names)
        if not missing:
            return DoctorCheck("cli-commands", "pass", "Expected PeachTree CLI commands are registered.")
        return DoctorCheck(
            "cli-commands",
            "warn",
            "Some expected PeachTree CLI commands are not registered.",
            {"missing": missing},
        )

    def _check_dataset(self, dataset: Path) -> DoctorCheck:
        path = dataset if dataset.is_absolute() else self.root / dataset
        if not path.exists():
            return DoctorCheck("dataset", "warn", f"Dataset `{dataset}` does not exist yet.")
        records = 0
        duplicate_ids = 0
        seen_ids: set[str] = set()
        missing_provenance = 0
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                records += 1
                record_id = record.get("id")
                if record_id in seen_ids:
                    duplicate_ids += 1
                if record_id:
                    seen_ids.add(record_id)
                if not record.get("source_repo") or not record.get("source_path"):
                    missing_provenance += 1
        except (OSError, json.JSONDecodeError) as exc:
            return DoctorCheck("dataset", "fail", f"Dataset `{dataset}` is not valid JSONL: {exc}")

        status: CheckStatus = "pass" if records and not duplicate_ids and not missing_provenance else "warn"
        message = f"Dataset `{dataset}` has {records} records."
        if duplicate_ids:
            message += f" Duplicate IDs: {duplicate_ids}."
        if missing_provenance:
            message += f" Missing provenance: {missing_provenance}."
        return DoctorCheck(
            "dataset",
            status,
            message,
            {
                "records": records,
                "duplicate_ids": duplicate_ids,
                "missing_provenance": missing_provenance,
            },
        )


def command_names_from_parser(parser: object) -> set[str]:
    names: set[str] = set()
    actions = getattr(parser, "_actions", [])
    for action in actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            names.update(str(name) for name in choices)
    return names
