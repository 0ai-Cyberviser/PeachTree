"""Scheduled dataset update planning for PeachTree.

This module generates review-first update plans. It does not run background
jobs itself and does not push data without an explicit CI workflow.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetUpdateTarget:
    name: str
    repo_path: str
    repo_name: str
    raw_output: str
    dataset_output: str
    manifest_output: str
    domain: str
    export_formats: tuple[str, ...] = ("chatml", "alpaca", "sharegpt")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScheduledUpdatePlan:
    name: str
    cron: str
    branch_prefix: str
    targets: tuple[DatasetUpdateTarget, ...]
    review_required: bool = True
    open_pull_request: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Scheduled Dataset Update Plan",
            "",
            f"- Name: `{self.name}`",
            f"- Cron: `{self.cron}`",
            f"- Branch prefix: `{self.branch_prefix}`",
            f"- Review required: `{'yes' if self.review_required else 'no'}`",
            f"- Opens pull request: `{'yes' if self.open_pull_request else 'no'}`",
            "",
            "## Targets",
            "",
            "| Name | Repo Name | Repo Path | Dataset | Manifest | Exports |",
            "|---|---|---|---|---|---|",
        ]
        for target in self.targets:
            lines.append(
                f"| `{target.name}` | `{target.repo_name}` | `{target.repo_path}` | `{target.dataset_output}` | `{target.manifest_output}` | `{', '.join(target.export_formats)}` |"
            )
        return "\n".join(lines)


class UpdatePlanBuilder:
    """Builds deterministic update plans for dataset-refresh PR workflows."""

    def default_plan(self, repo_path: str, repo_name: str, name: str = "peachtree-dataset-update") -> ScheduledUpdatePlan:
        safe_name = repo_name.replace("/", "__")
        target = DatasetUpdateTarget(
            name=safe_name,
            repo_path=repo_path,
            repo_name=repo_name,
            raw_output=f"data/raw/{safe_name}.jsonl",
            dataset_output=f"data/datasets/{safe_name}-instruct.jsonl",
            manifest_output=f"data/manifests/{safe_name}.json",
            domain=safe_name,
        )
        return ScheduledUpdatePlan(
            name=name,
            cron="17 3 * * 1",
            branch_prefix="peachtree/dataset-update",
            targets=(target,),
        )

    def write_plan(
        self,
        plan: ScheduledUpdatePlan,
        json_output: str | Path,
        markdown_output: str | Path | None = None,
    ) -> tuple[Path, Path | None]:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(plan.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(plan.to_markdown() + "\n", encoding="utf-8")
        return json_path, md_path

    def read_plan(self, path: str | Path) -> ScheduledUpdatePlan:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        targets = tuple(
            DatasetUpdateTarget(
                name=target["name"],
                repo_path=target["repo_path"],
                repo_name=target["repo_name"],
                raw_output=target["raw_output"],
                dataset_output=target["dataset_output"],
                manifest_output=target["manifest_output"],
                domain=target["domain"],
                export_formats=tuple(target.get("export_formats", ("chatml", "alpaca", "sharegpt"))),
            )
            for target in data.get("targets", [])
        )
        return ScheduledUpdatePlan(
            name=data["name"],
            cron=data["cron"],
            branch_prefix=data["branch_prefix"],
            targets=targets,
            review_required=bool(data.get("review_required", True)),
            open_pull_request=bool(data.get("open_pull_request", True)),
        )

    @staticmethod
    def command_preview(plan: ScheduledUpdatePlan) -> list[str]:
        commands: list[str] = []
        for target in plan.targets:
            commands.extend(
                [
                    f"peachtree ingest-local --repo {target.repo_path} --repo-name {target.repo_name} --output {target.raw_output}",
                    f"peachtree build --source {target.raw_output} --dataset {target.dataset_output} --manifest {target.manifest_output} --domain {target.domain}",
                    f"peachtree audit --dataset {target.dataset_output}",
                ]
            )
            for export_format in target.export_formats:
                commands.append(
                    f"peachtree export --source {target.dataset_output} --format {export_format} --output data/exports/{target.name}-{export_format}.jsonl"
                )
                commands.append(
                    f"peachtree validate-export --format {export_format} --path data/exports/{target.name}-{export_format}.jsonl"
                )
        return commands
