from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from .builder import DatasetBuilder
from .models import SourceDocument
from .repo_ingest import iter_local_documents
from .safety import SafetyGate


@dataclass(frozen=True)
class WorkspaceRepo:
    name: str
    path: str
    domain: str
    license: str = "unknown"


@dataclass(frozen=True)
class WorkspaceOutputs:
    raw: str = "data/raw"
    datasets: str = "data/datasets"
    manifests: str = "data/manifests"
    reports: str = "reports"
    exports: str = "data/exports"
    bundles: str = "dist"


@dataclass(frozen=True)
class WorkspacePolicy:
    public_github_collection: bool = False
    review_required_before_training: bool = True
    allow_unknown_license: bool = False
    max_file_bytes: int = 256_000


@dataclass(frozen=True)
class PeachWorkspace:
    workspace: str = "cyberviser-peach"
    repos: tuple[WorkspaceRepo, ...] = field(default_factory=tuple)
    outputs: WorkspaceOutputs = field(default_factory=WorkspaceOutputs)
    policy: WorkspacePolicy = field(default_factory=WorkspacePolicy)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PeachWorkspace":
        outputs = WorkspaceOutputs(**data.get("outputs", {}))
        policy = WorkspacePolicy(**data.get("policy", {}))
        repos = tuple(WorkspaceRepo(**item) for item in data.get("repos", []))
        return cls(
            workspace=data.get("workspace", "cyberviser-peach"),
            repos=repos,
            outputs=outputs,
            policy=policy,
        )

    @classmethod
    def read(cls, path: str | Path) -> "PeachWorkspace":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def validate(self, root: str | Path = ".") -> dict[str, Any]:
        base = Path(root).resolve()
        findings: list[dict[str, str]] = []
        if self.policy.public_github_collection:
            findings.append({"severity": "fail", "message": "public_github_collection must remain false by default"})
        if not self.policy.review_required_before_training:
            findings.append({"severity": "fail", "message": "review_required_before_training must be true"})
        for repo in self.repos:
            repo_path = Path(repo.path)
            if not repo_path.is_absolute():
                repo_path = base / repo_path
            if not repo_path.exists():
                findings.append({"severity": "warn", "message": f"repo path does not exist: {repo.path}"})
            if not repo.name:
                findings.append({"severity": "fail", "message": "repo name cannot be empty"})
            if not repo.domain:
                findings.append({"severity": "fail", "message": f"repo {repo.name} has empty domain"})
        return {
            "ok": not any(item["severity"] == "fail" for item in findings),
            "workspace": self.workspace,
            "repos": len(self.repos),
            "findings": findings,
            "safety": {
                "public_github_collection": self.policy.public_github_collection,
                "review_required_before_training": self.policy.review_required_before_training,
                "allow_unknown_license": self.policy.allow_unknown_license,
            },
        }


def default_workspace() -> PeachWorkspace:
    return PeachWorkspace(
        repos=(
            WorkspaceRepo(name="hancock", path="../Hancock", domain="hancock", license="apache-2.0"),
            WorkspaceRepo(name="peachfuzz", path="../peachfuzz", domain="peachfuzz", license="apache-2.0"),
        )
    )


def write_default_workspace(path: str | Path = "peach.json", *, force: bool = False) -> Path:
    out = Path(path)
    if out.exists() and not force:
        raise FileExistsError(f"{out} already exists; pass force=True to overwrite")
    out.write_text(default_workspace().to_json() + "\n", encoding="utf-8")
    return out


def build_workspace(config_path: str | Path = "peach.json", root: str | Path = ".") -> dict[str, Any]:
    workspace = PeachWorkspace.read(config_path)
    base = Path(root).resolve()
    raw_dir = base / workspace.outputs.raw
    dataset_dir = base / workspace.outputs.datasets
    manifest_dir = base / workspace.outputs.manifests
    raw_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    gate = SafetyGate(allow_unknown_license=workspace.policy.allow_unknown_license)
    for repo in workspace.repos:
        repo_path = Path(repo.path)
        if not repo_path.is_absolute():
            repo_path = base / repo_path
        docs: list[SourceDocument] = []
        if repo_path.exists():
            docs = iter_local_documents(
                repo_path,
                repo.name,
                license_id=repo.license,
                max_file_bytes=workspace.policy.max_file_bytes,
            )
        raw_path = raw_dir / f"{repo.name}.jsonl"
        raw_path.write_text(
            "\n".join(json.dumps(doc.to_dict(), sort_keys=True) for doc in docs) + ("\n" if docs else ""),
            encoding="utf-8",
        )
        builder = DatasetBuilder(repo.domain, gate)
        records = builder.records_from_documents(docs)
        dataset_path = dataset_dir / f"{repo.name}-instruct.jsonl"
        manifest_path = manifest_dir / f"{repo.name}.json"
        manifest = builder.write_jsonl(records, dataset_path, manifest_path, docs)
        results.append(
            {
                "repo": repo.name,
                "raw": str(raw_path),
                "dataset": str(dataset_path),
                "manifest": str(manifest_path),
                "documents": len(docs),
                "records": manifest.record_count,
                "policy": manifest.policy,
            }
        )
    return {"workspace": workspace.workspace, "repos": results}


def workspace_report(config_path: str | Path = "peach.json") -> str:
    workspace = PeachWorkspace.read(config_path)
    validation = workspace.validate(Path(config_path).parent or ".")
    lines = [
        "# Peach Workspace Report",
        "",
        f"Workspace: `{workspace.workspace}`",
        f"Repos: {len(workspace.repos)}",
        f"Status: {'OK' if validation['ok'] else 'NEEDS ATTENTION'}",
        "",
        "## Repositories",
    ]
    for repo in workspace.repos:
        lines.append(f"- `{repo.name}` -> `{repo.path}` ({repo.domain}, {repo.license})")
    lines.extend(["", "## Policy", ""])
    lines.append(f"- Public GitHub collection: `{workspace.policy.public_github_collection}`")
    lines.append(f"- Review required before training: `{workspace.policy.review_required_before_training}`")
    lines.append(f"- Allow unknown license: `{workspace.policy.allow_unknown_license}`")
    if validation["findings"]:
        lines.extend(["", "## Findings"])
        for finding in validation["findings"]:
            lines.append(f"- **{finding['severity']}**: {finding['message']}")
    return "\n".join(lines)
