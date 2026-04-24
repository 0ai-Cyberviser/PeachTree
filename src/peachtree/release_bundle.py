"""Release bundle builder for PeachTree reviewed dataset artifacts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile
from typing import Any

from .registry import DatasetRegistry, DatasetRegistryBuilder, sha256_file
from .sbom import SBOMGenerator
from .signing import ArtifactSigner


@dataclass(frozen=True)
class ReleaseBundleReport:
    bundle_path: str
    bundle_sha256: str
    artifact_count: int
    registry_path: str
    sbom_path: str
    signature_path: str | None
    created_at: str
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Release Bundle Report",
            "",
            f"- Bundle: `{self.bundle_path}`",
            f"- SHA-256: `{self.bundle_sha256}`",
            f"- Artifacts: `{self.artifact_count}`",
            f"- Registry: `{self.registry_path}`",
            f"- SBOM: `{self.sbom_path}`",
            f"- Signature: `{self.signature_path or 'not generated'}`",
            f"- Created: `{self.created_at}`",
            "",
            "## Safety",
            "",
        ]
        for key, value in self.safety.items():
            lines.append(f"- {key}: `{value}`")
        return "\n".join(lines)


class ReleaseBundleBuilder:
    """Builds deterministic zip bundles with registry, SBOM, and optional signature."""

    def build(
        self,
        artifact_paths: list[str | Path],
        output_path: str | Path,
        name: str = "peachtree-release",
        version: str = "0.8.0",
        signing_key: str | None = None,
        signing_key_id: str = "local-dev-key",
        work_dir: str | Path | None = None,
    ) -> ReleaseBundleReport:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(work_dir) if work_dir else out.parent / f"{out.stem}-staging"
        staging.mkdir(parents=True, exist_ok=True)

        registry = DatasetRegistryBuilder().build(
            artifact_paths,
            name=name,
            version=version,
            metadata={"bundle": str(out), "release_review_required": True},
        )
        registry_path = staging / "registry.json"
        registry_path.write_text(registry.to_json() + "\n", encoding="utf-8")

        sbom = SBOMGenerator().from_registry(registry, source_registry=str(registry_path))
        sbom_path = staging / "sbom.json"
        sbom_path.write_text(sbom.to_json() + "\n", encoding="utf-8")

        manifest = {
            "name": name,
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "registry": "registry.json",
            "sbom": "sbom.json",
            "artifacts": [artifact.to_dict() for artifact in registry.artifacts],
            "safety": self._safety(),
        }
        manifest_path = staging / "release-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            self._write_file(bundle, registry_path, "registry.json")
            self._write_file(bundle, sbom_path, "sbom.json")
            self._write_file(bundle, manifest_path, "release-manifest.json")
            for artifact in registry.artifacts:
                artifact_path = Path(artifact.path)
                if artifact_path.exists():
                    arcname = f"artifacts/{artifact.name}"
                else:
                    matching = [Path(path) for path in artifact_paths if Path(path).name == artifact.name]
                    artifact_path = matching[0] if matching else Path(artifact.path)
                    arcname = f"artifacts/{artifact.name}"
                if artifact_path.exists():
                    self._write_file(bundle, artifact_path, arcname)

        signature_path: Path | None = None
        if signing_key:
            signer = ArtifactSigner()
            signature_path = out.with_suffix(out.suffix + ".sig.json")
            signer.sign_file_to_path(out, signature_path, key=signing_key, key_id=signing_key_id)

        bundle_digest = sha256_file(out)
        report = ReleaseBundleReport(
            bundle_path=str(out),
            bundle_sha256=bundle_digest,
            artifact_count=registry.artifact_count,
            registry_path=str(registry_path),
            sbom_path=str(sbom_path),
            signature_path=str(signature_path) if signature_path else None,
            created_at=datetime.now(timezone.utc).isoformat(),
            safety=self._safety(),
        )
        return report

    @staticmethod
    def _write_file(bundle: zipfile.ZipFile, path: Path, arcname: str) -> None:
        info = zipfile.ZipInfo(arcname)
        info.external_attr = (0o644 & 0xFFFF) << 16
        bundle.writestr(info, path.read_bytes())

    @staticmethod
    def _safety() -> dict[str, Any]:
        return {
            "local_only": True,
            "does_not_train_models": True,
            "does_not_upload_datasets": True,
            "does_not_scrape_public_github": True,
            "requires_human_review": True,
        }
