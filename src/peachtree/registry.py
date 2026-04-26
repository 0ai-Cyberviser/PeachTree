"""Dataset registry for PeachTree release artifacts.

The registry is a local-only manifest of reviewed datasets, exports, reports,
model cards, SBOMs, and release bundles. It records SHA-256 digests and basic
metadata for reproducible release review.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RegistryArtifact:
    name: str
    path: str
    kind: str
    sha256: str
    size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetRegistry:
    name: str
    version: str
    created_at: str
    artifacts: tuple[RegistryArtifact, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "artifact_count": self.artifact_count,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Dataset Registry",
            "",
            f"- Name: `{self.name}`",
            f"- Version: `{self.version}`",
            f"- Created: `{self.created_at}`",
            f"- Artifacts: `{self.artifact_count}`",
            "",
            "| Name | Kind | Size | SHA-256 | Path |",
            "|---|---|---:|---|---|",
        ]
        for artifact in self.artifacts:
            lines.append(
                f"| `{artifact.name}` | `{artifact.kind}` | {artifact.size_bytes} | `{artifact.sha256[:16]}...` | `{artifact.path}` |"
            )
        return "\n".join(lines)


class DatasetRegistryBuilder:
    """Builds and reads registry manifests."""

    def build(
        self,
        artifact_paths: list[str | Path],
        name: str = "peachtree-release",
        version: str = "0.8.0",
        base_dir: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetRegistry:
        root = Path(base_dir).resolve() if base_dir else None
        artifacts: list[RegistryArtifact] = []
        for artifact_path in artifact_paths:
            path = Path(artifact_path)
            if not path.exists() or not path.is_file():
                continue
            artifact_name = path.name
            display_path = self._display_path(path, root)
            artifacts.append(
                RegistryArtifact(
                    name=artifact_name,
                    path=display_path,
                    kind=self._infer_kind(path),
                    sha256=sha256_file(path),
                    size_bytes=path.stat().st_size,
                    metadata={},
                )
            )
        return DatasetRegistry(
            name=name,
            version=version,
            created_at=datetime.now(timezone.utc).isoformat(),
            artifacts=tuple(sorted(artifacts, key=lambda item: (item.kind, item.path))),
            metadata=metadata or {},
        )

    def discover(
        self,
        roots: list[str | Path],
        name: str = "peachtree-release",
        version: str = "0.8.0",
        metadata: dict[str, Any] | None = None,
    ) -> DatasetRegistry:
        files: list[str | Path] = []
        root_paths = [Path(root) for root in roots]
        for root in root_paths:
            if root.is_file():
                files.append(root)
            elif root.exists():
                files.extend(path for path in root.rglob("*") if path.is_file() and not self._is_runtime_noise(path))
        base_dir = root_paths[0] if len(root_paths) == 1 and root_paths[0].is_dir() else None
        return self.build(files, name=name, version=version, base_dir=base_dir, metadata=metadata)

    def write(
        self,
        registry: DatasetRegistry,
        output_path: str | Path,
        markdown_output: str | Path | None = None,
    ) -> tuple[Path, Path | None]:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(registry.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(registry.to_markdown() + "\n", encoding="utf-8")
        return out, md_path

    def read(self, path: str | Path) -> DatasetRegistry:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        artifacts = tuple(RegistryArtifact(**artifact) for artifact in data.get("artifacts", []))
        return DatasetRegistry(
            name=data["name"],
            version=data["version"],
            created_at=data["created_at"],
            artifacts=artifacts,
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def _infer_kind(path: Path) -> str:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name.endswith(".jsonl") and "dataset" in str(path).lower():
            return "dataset"
        if name.endswith(".jsonl") and "export" in str(path).lower():
            return "export"
        if name.endswith(".json"):
            if "manifest" in str(path).lower():
                return "manifest"
            if "sbom" in name:
                return "sbom"
            if "signature" in name or name.endswith(".sig.json"):
                return "signature"
            return "json-report"
        if suffix in {".md", ".markdown"}:
            if "model-card" in name:
                return "model-card"
            return "markdown-report"
        if suffix in {".zip", ".tar", ".gz"}:
            return "release-bundle"
        return "artifact"

    @staticmethod
    def _display_path(path: Path, root: Path | None) -> str:
        try:
            return str(path.resolve().relative_to(root)) if root else str(path)
        except ValueError:
            return str(path)

    @staticmethod
    def _is_runtime_noise(path: Path) -> bool:
        noise_parts = {"__pycache__", ".pytest_cache", ".git"}
        return any(part in noise_parts for part in path.parts) or path.suffix == ".pyc"
