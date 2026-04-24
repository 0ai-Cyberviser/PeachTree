"""Dataset lineage maps for PeachTree."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceLineage:
    source_repo: str
    source_path: str
    source_digest: str
    record_count: int
    record_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetLineage:
    dataset_path: str
    record_count: int
    source_repo_count: int
    source_file_count: int
    sources: tuple[SourceLineage, ...]
    manifest_path: str | None = None
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Dataset Lineage",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Records: `{self.record_count}`",
            f"- Source repositories: `{self.source_repo_count}`",
            f"- Source files: `{self.source_file_count}`",
        ]
        if self.manifest_path:
            lines.append(f"- Manifest: `{self.manifest_path}`")
        lines += ["", "## Top Sources", "", "| Source Repo | Source Path | Records | Digest |", "|---|---|---:|---|"]
        for source in sorted(self.sources, key=lambda s: (-s.record_count, s.source_repo, s.source_path))[:50]:
            lines.append(
                f"| `{source.source_repo}` | `{source.source_path}` | {source.record_count} | `{source.source_digest[:12]}` |"
            )
        return "\n".join(lines)


class DatasetLineageBuilder:
    """Build lineage maps from PeachTree JSONL datasets and manifests."""

    def from_dataset(
        self,
        dataset_path: str | Path,
        manifest_path: str | Path | None = None,
    ) -> DatasetLineage:
        path = Path(dataset_path)
        records = self._read_jsonl(path)
        manifest: dict[str, Any] = {}
        if manifest_path and Path(manifest_path).exists():
            try:
                manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {}

        grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        source_repos: set[str] = set()
        for record in records:
            repo = str(record.get("source_repo", "unknown"))
            source_path = str(record.get("source_path", "unknown"))
            digest = str(record.get("source_digest", "unknown"))
            record_id = str(record.get("id", ""))
            source_repos.add(repo)
            grouped[(repo, source_path, digest)].append(record_id)

        sources = tuple(
            SourceLineage(repo, source_path, digest, len(ids), tuple(sorted(filter(None, ids))))
            for (repo, source_path, digest), ids in grouped.items()
        )

        return DatasetLineage(
            dataset_path=str(path),
            record_count=len(records),
            source_repo_count=len(source_repos),
            source_file_count=len(sources),
            sources=sources,
            manifest_path=str(manifest_path) if manifest_path else None,
            manifest=manifest,
        )

    def summarize_directory(
        self,
        dataset_dir: str | Path,
        manifest_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        dataset_root = Path(dataset_dir)
        manifest_root = Path(manifest_dir) if manifest_dir else None
        lineages: list[DatasetLineage] = []

        if dataset_root.exists():
            for dataset in sorted(dataset_root.glob("*.jsonl")):
                manifest = self._matching_manifest(dataset, manifest_root)
                lineages.append(self.from_dataset(dataset, manifest))

        repo_counter: Counter[str] = Counter()
        total_records = 0
        for lineage in lineages:
            total_records += lineage.record_count
            for source in lineage.sources:
                repo_counter[source.source_repo] += source.record_count

        return {
            "dataset_count": len(lineages),
            "total_records": total_records,
            "source_repositories": len(repo_counter),
            "top_repositories": repo_counter.most_common(25),
            "datasets": [lineage.to_dict() for lineage in lineages],
        }

    @staticmethod
    def _matching_manifest(dataset_path: Path, manifest_dir: Path | None) -> Path | None:
        if not manifest_dir or not manifest_dir.exists():
            return None
        stem = dataset_path.name.replace("-instruct.jsonl", "").replace(".jsonl", "")
        candidates = [manifest_dir / f"{stem}.json", manifest_dir / f"{dataset_path.stem}.json"]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not path.exists():
            return records
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
