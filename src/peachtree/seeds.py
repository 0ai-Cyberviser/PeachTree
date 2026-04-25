from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Literal

from .models import sha256_text, utc_now
from .safety import SafetyGate

SeedTarget = Literal["json", "graphql", "openapi", "webhook", "yaml", "xml", "http", "log"]

ALLOWED_TARGETS: set[str] = {"json", "graphql", "openapi", "webhook", "yaml", "xml", "http", "log"}
UNSAFE_SEED_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password|cookie)\s*[:=]"),
    re.compile(r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"(?i)169\.254\.169\.254"),
    re.compile(r"(?i)authorization:\s*bearer\s+[a-z0-9._-]{12,}"),
)


@dataclass(frozen=True)
class SeedRecord:
    id: str
    target: str
    path: str
    source_record_id: str
    source_digest: str
    bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SeedExportManifest:
    target: str
    source_dataset: str
    source_dataset_digest: str
    generated_at: str
    write_enabled: bool
    seeds: tuple[SeedRecord, ...] = field(default_factory=tuple)
    skipped: int = 0
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["seeds"] = [seed.to_dict() for seed in self.seeds]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# PeachTree Seed Export",
            "",
            f"Target: `{self.target}`",
            f"Source dataset: `{self.source_dataset}`",
            f"Source digest: `{self.source_dataset_digest}`",
            f"Write enabled: `{self.write_enabled}`",
            f"Seeds: {len(self.seeds)}",
            f"Skipped: {self.skipped}",
            "",
            "| Seed | Source record | Bytes |",
            "|---|---|---|",
        ]
        for seed in self.seeds:
            lines.append(f"| `{seed.path}` | `{seed.source_record_id}` | {seed.bytes} |")
        return "\n".join(lines)


class PeachSeedExporter:
    """Export reviewed PeachTree dataset records into local PeachFuzz seed corpora."""

    def __init__(self, safety_gate: SafetyGate | None = None) -> None:
        self.safety_gate = safety_gate or SafetyGate(allow_unknown_license=False)

    def export(
        self,
        dataset: str | Path,
        target: str,
        output: str | Path,
        *,
        write: bool = False,
        limit: int | None = None,
    ) -> SeedExportManifest:
        if target not in ALLOWED_TARGETS:
            raise ValueError(f"unsupported seed target: {target}")

        dataset_path = Path(dataset)
        dataset_text = dataset_path.read_text(encoding="utf-8")
        dataset_digest = hashlib.sha256(dataset_text.encode("utf-8")).hexdigest()
        output_path = Path(output)
        records = self._read_records(dataset_path)
        seeds: list[SeedRecord] = []
        skipped = 0

        if write:
            output_path.mkdir(parents=True, exist_ok=True)

        for index, record in enumerate(records):
            if limit is not None and len(seeds) >= limit:
                break
            payload = self._payload_for_record(record, target)
            if not payload or self._unsafe(payload):
                skipped += 1
                continue
            payload = self.safety_gate.sanitize(payload)
            suffix = self._suffix_for_target(target)
            source_id = str(record.get("id") or sha256_text(json.dumps(record, sort_keys=True)))
            seed_id = sha256_text(f"{target}:{source_id}:{payload}")[:16]
            relative_path = f"{target}-{index:05d}-{seed_id}{suffix}"
            if write:
                (output_path / relative_path).write_text(payload, encoding="utf-8")
            seeds.append(
                SeedRecord(
                    id=seed_id,
                    target=target,
                    path=relative_path,
                    source_record_id=source_id,
                    source_digest=str(record.get("source_digest") or ""),
                    bytes=len(payload.encode("utf-8")),
                )
            )

        return SeedExportManifest(
            target=target,
            source_dataset=str(dataset_path),
            source_dataset_digest=dataset_digest,
            generated_at=utc_now(),
            write_enabled=write,
            seeds=tuple(seeds),
            skipped=skipped,
            policy={
                "local_only": True,
                "dry_run_by_default": True,
                "sanitized": True,
                "no_network": True,
                "no_execution": True,
                "unsafe_patterns_blocked": True,
            },
        )

    @staticmethod
    def _read_records(dataset: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in dataset.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    @staticmethod
    def _payload_for_record(record: dict[str, Any], target: str) -> str:
        text = "\n".join(
            str(record.get(key, ""))
            for key in ("instruction", "input", "output")
            if record.get(key)
        ).strip()
        if not text:
            return ""
        if target in {"json", "webhook", "openapi"}:
            return json.dumps(
                {
                    "instruction": record.get("instruction", ""),
                    "input": record.get("input", ""),
                    "output": record.get("output", ""),
                    "source_path": record.get("source_path", ""),
                },
                indent=2,
                sort_keys=True,
            )
        if target == "graphql":
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", str(record.get("source_path", "seed")))[:80]
            escaped = text[:1000].replace('"', '\\"')
            return f'query PeachTreeSeed_{safe_name} {{\n  peachtreeSeed(note: "{escaped}")\n}}\n'
        if target == "yaml":
            return "---\n" + "\n".join(f"# {line}" for line in text.splitlines()[:80]) + "\n"
        if target == "xml":
            escaped = text[:4000].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return f"<peachtree-seed>{escaped}</peachtree-seed>\n"
        if target == "http":
            escaped = text[:2000].replace("\r", " ").replace("\n", " ")
            return f"POST /peachtree/local-seed HTTP/1.1\nHost: localhost\nContent-Type: text/plain\n\n{escaped}\n"
        return text[:4000] + "\n"

    @staticmethod
    def _suffix_for_target(target: str) -> str:
        return {
            "json": ".json",
            "openapi": ".json",
            "webhook": ".json",
            "graphql": ".graphql",
            "yaml": ".yaml",
            "xml": ".xml",
            "http": ".http",
            "log": ".log",
        }[target]

    @staticmethod
    def _unsafe(payload: str) -> bool:
        return any(pattern.search(payload) for pattern in UNSAFE_SEED_PATTERNS)


def write_seed_manifest(manifest: SeedExportManifest, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(manifest.to_json() + "\n", encoding="utf-8")
    return out
