"""Trainer handoff manifests for PeachTree.

This module prepares local review artifacts for downstream training systems.
It does not train models, upload datasets, or call external trainer APIs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .registry import sha256_file


@dataclass(frozen=True)
class HandoffArtifact:
    name: str
    path: str
    kind: str
    sha256: str
    size_bytes: int
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainerHandoffManifest:
    model_name: str
    base_model: str
    trainer_profile: str
    dataset_path: str
    dataset_format: str
    created_at: str
    artifacts: tuple[HandoffArtifact, ...]
    safety: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_model": self.base_model,
            "trainer_profile": self.trainer_profile,
            "dataset_path": self.dataset_path,
            "dataset_format": self.dataset_format,
            "created_at": self.created_at,
            "artifact_count": self.artifact_count,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "safety": self.safety,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Trainer Handoff Manifest",
            "",
            f"- Model name: `{self.model_name}`",
            f"- Base model: `{self.base_model}`",
            f"- Trainer profile: `{self.trainer_profile}`",
            f"- Dataset: `{self.dataset_path}`",
            f"- Dataset format: `{self.dataset_format}`",
            f"- Created: `{self.created_at}`",
            "",
            "## Artifacts",
            "",
            "| Name | Kind | Required | Size | SHA-256 | Path |",
            "|---|---|---|---:|---|---|",
        ]
        for artifact in self.artifacts:
            lines.append(
                f"| `{artifact.name}` | `{artifact.kind}` | `{'yes' if artifact.required else 'no'}` | {artifact.size_bytes} | `{artifact.sha256[:16]}...` | `{artifact.path}` |"
            )
        lines += ["", "## Safety", ""]
        for key, value in self.safety.items():
            lines.append(f"- {key}: `{value}`")
        return "\n".join(lines)


class TrainerHandoffBuilder:
    """Builds trainer handoff manifests from reviewed local artifacts."""

    artifact_kinds = {
        "dataset": "dataset",
        "registry": "registry",
        "sbom": "sbom",
        "model_card": "model-card",
        "quality_report": "quality-report",
        "policy_report": "policy-report",
        "license_report": "license-report",
        "release_bundle": "release-bundle",
    }

    def build(
        self,
        dataset_path: str | Path,
        model_name: str,
        base_model: str,
        trainer_profile: str = "unsloth",
        dataset_format: str = "chatml",
        registry_path: str | Path | None = None,
        sbom_path: str | Path | None = None,
        model_card_path: str | Path | None = None,
        quality_report_path: str | Path | None = None,
        policy_report_path: str | Path | None = None,
        license_report_path: str | Path | None = None,
        release_bundle_path: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TrainerHandoffManifest:
        artifacts = [
            self._artifact(dataset_path, "dataset", required=True),
        ]
        optional = {
            "registry": registry_path,
            "sbom": sbom_path,
            "model_card": model_card_path,
            "quality_report": quality_report_path,
            "policy_report": policy_report_path,
            "license_report": license_report_path,
            "release_bundle": release_bundle_path,
        }
        for kind, path in optional.items():
            if path:
                artifacts.append(self._artifact(path, kind, required=False))

        return TrainerHandoffManifest(
            model_name=model_name,
            base_model=base_model,
            trainer_profile=trainer_profile,
            dataset_path=str(dataset_path),
            dataset_format=dataset_format,
            created_at=datetime.now(timezone.utc).isoformat(),
            artifacts=tuple(artifact for artifact in artifacts if artifact is not None),
            safety=self.safety(),
            metadata=metadata or {},
        )

    def write(
        self,
        manifest: TrainerHandoffManifest,
        output_path: str | Path,
        markdown_output: str | Path | None = None,
    ) -> tuple[Path, Path | None]:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(manifest.to_json() + "\n", encoding="utf-8")
        md_path: Path | None = None
        if markdown_output:
            md_path = Path(markdown_output)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(manifest.to_markdown() + "\n", encoding="utf-8")
        return out, md_path

    @classmethod
    def _artifact(cls, path: str | Path, kind: str, required: bool) -> HandoffArtifact | None:
        p = Path(path)
        if not p.exists() or not p.is_file():
            if required:
                raise FileNotFoundError(str(p))
            return None
        return HandoffArtifact(
            name=p.name,
            path=str(p),
            kind=cls.artifact_kinds.get(kind, kind),
            sha256=sha256_file(p),
            size_bytes=p.stat().st_size,
            required=required,
        )

    @staticmethod
    def safety() -> dict[str, Any]:
        return {
            "dry_run_only": True,
            "does_not_train_models": True,
            "does_not_upload_datasets": True,
            "does_not_call_training_apis": True,
            "requires_human_approval_before_training": True,
        }
