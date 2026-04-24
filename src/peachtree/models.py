from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


@dataclass(frozen=True)
class SourceDocument:
    repo_name: str
    path: str
    content: str
    source_type: str = "local-file"
    license_id: str = "unknown"
    commit_sha: str | None = None

    @property
    def digest(self) -> str:
        return sha256_text(f"{self.repo_name}:{self.path}:{self.content}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningNode:
    id: str
    goal: str
    project: str
    depth: int
    parent_id: str | None = None
    status: str = "planned"
    children: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetRecord:
    instruction: str
    input: str
    output: str
    domain: str
    source_repo: str
    source_path: str
    source_digest: str
    license_id: str
    record_type: str = "instruction"
    quality_score: float = 0.5
    safety_score: float = 1.0
    created_at: str = field(default_factory=utc_now)

    @property
    def id(self) -> str:
        return sha256_text(json.dumps(self.to_dict(include_id=False), sort_keys=True))

    def to_dict(self, include_id: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if include_id:
            data["id"] = self.id
        return data

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class DatasetManifest:
    dataset_path: str
    record_count: int
    source_count: int
    domain: str
    builder_version: str
    created_at: str = field(default_factory=utc_now)
    source_digests: tuple[str, ...] = field(default_factory=tuple)
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
