"""Dependency-free artifact signing metadata for PeachTree.

This module uses HMAC-SHA256 for local integrity signatures. It is useful for
review pipelines and reproducibility checks, but it is not a replacement for
hardware-backed signing, GPG, Sigstore, or organization PKI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hmac
import hashlib
import json
from pathlib import Path
from typing import Any

from .registry import sha256_file


@dataclass(frozen=True)
class SignatureEnvelope:
    artifact_path: str
    artifact_sha256: str
    signature: str
    algorithm: str
    key_id: str
    created_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class SignatureVerification:
    artifact_path: str
    signature_path: str
    expected_sha256: str
    actual_sha256: str
    signature_valid: bool
    digest_valid: bool

    @property
    def valid(self) -> bool:
        return self.signature_valid and self.digest_valid

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["valid"] = self.valid
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class ArtifactSigner:
    """Creates and verifies local HMAC-SHA256 artifact signatures."""

    algorithm = "HMAC-SHA256"

    def sign_file(
        self,
        artifact_path: str | Path,
        key: str,
        key_id: str = "local-dev-key",
        metadata: dict[str, Any] | None = None,
    ) -> SignatureEnvelope:
        path = Path(artifact_path)
        artifact_digest = sha256_file(path)
        signature = self._sign_digest(artifact_digest, key)
        return SignatureEnvelope(
            artifact_path=str(path),
            artifact_sha256=artifact_digest,
            signature=signature,
            algorithm=self.algorithm,
            key_id=key_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {"warning": "Local HMAC signature; verify with trusted key management before release."},
        )

    def write_signature(self, envelope: SignatureEnvelope, output_path: str | Path) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(envelope.to_json() + "\n", encoding="utf-8")
        return out

    def sign_file_to_path(
        self,
        artifact_path: str | Path,
        output_path: str | Path,
        key: str,
        key_id: str = "local-dev-key",
    ) -> Path:
        envelope = self.sign_file(artifact_path, key=key, key_id=key_id)
        return self.write_signature(envelope, output_path)

    def verify_file(self, artifact_path: str | Path, signature_path: str | Path, key: str) -> SignatureVerification:
        artifact = Path(artifact_path)
        sig_path = Path(signature_path)
        data = json.loads(sig_path.read_text(encoding="utf-8"))
        expected_sha = str(data["artifact_sha256"])
        actual_sha = sha256_file(artifact)
        expected_signature = str(data["signature"])
        actual_signature = self._sign_digest(expected_sha, key)
        return SignatureVerification(
            artifact_path=str(artifact),
            signature_path=str(sig_path),
            expected_sha256=expected_sha,
            actual_sha256=actual_sha,
            signature_valid=hmac.compare_digest(expected_signature, actual_signature),
            digest_valid=hmac.compare_digest(expected_sha, actual_sha),
        )

    @staticmethod
    def _sign_digest(digest: str, key: str) -> str:
        return hmac.new(key.encode("utf-8"), digest.encode("utf-8"), hashlib.sha256).hexdigest()
