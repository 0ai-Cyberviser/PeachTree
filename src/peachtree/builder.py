from __future__ import annotations

from pathlib import Path
import json
import re

from .models import DatasetManifest, DatasetRecord, SourceDocument
from .safety import SafetyGate


class DatasetBuilder:
    def __init__(self, domain: str, safety_gate: SafetyGate | None = None) -> None:
        self.domain = domain
        self.safety_gate = safety_gate or SafetyGate()

    def records_from_documents(self, docs: list[SourceDocument]) -> list[DatasetRecord]:
        records: list[DatasetRecord] = []
        seen: set[str] = set()
        for doc in docs:
            decision = self.safety_gate.check_document(doc)
            if not decision.allowed:
                continue
            for idx, chunk in enumerate(self._chunks(self.safety_gate.sanitize(doc.content))):
                record = DatasetRecord(
                    instruction=self._instruction_for_path(doc.path),
                    input=f"Repository: {doc.repo_name}\nPath: {doc.path}\nChunk: {idx}\n\n{chunk}",
                    output=self._output_for_chunk(doc.path, chunk),
                    domain=self.domain,
                    source_repo=doc.repo_name,
                    source_path=doc.path,
                    source_digest=doc.digest,
                    license_id=doc.license_id,
                    quality_score=self._quality_score(doc.path, chunk),
                    safety_score=decision.score,
                )
                if record.id not in seen:
                    seen.add(record.id)
                    records.append(record)
        return records

    def write_jsonl(
        self,
        records: list[DatasetRecord],
        dataset_path: str | Path,
        manifest_path: str | Path,
        sources: list[SourceDocument],
    ) -> DatasetManifest:
        dataset = Path(dataset_path)
        manifest_file = Path(manifest_path)
        dataset.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        dataset.write_text("\n".join(record.to_jsonl() for record in records) + ("\n" if records else ""), encoding="utf-8")
        manifest = DatasetManifest(
            dataset_path=str(dataset),
            record_count=len(records),
            source_count=len(sources),
            domain=self.domain,
            builder_version="0.5.0",
            source_digests=tuple(sorted({source.digest for source in sources})),
            policy={"secret_filtering": True, "license_filtering": True, "provenance_required": True},
        )
        manifest_file.write_text(manifest.to_json() + "\n", encoding="utf-8")
        return manifest

    def audit_jsonl(self, dataset_path: str | Path) -> dict[str, object]:
        path = Path(dataset_path)
        records = []
        if path.exists():
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        ids = [record.get("id") for record in records]
        return {
            "dataset": str(path),
            "records": len(records),
            "unique_ids": len(set(ids)),
            "duplicates": len(ids) - len(set(ids)),
            "has_provenance": all(record.get("source_repo") and record.get("source_path") for record in records),
            "min_quality_score": min((record.get("quality_score", 0) for record in records), default=0),
        }

    @staticmethod
    def _chunks(text: str, max_chars: int = 2000) -> list[str]:
        text = text.strip()
        if not text:
            return []
        paragraphs = re.split(r"\n\s*\n", text)
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(current) + len(paragraph) + 2 <= max_chars:
                current = f"{current}\n\n{paragraph}".strip()
            else:
                if current:
                    chunks.append(current)
                current = paragraph[:max_chars]
        if current:
            chunks.append(current)
        return chunks[:20]

    @staticmethod
    def _instruction_for_path(path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            return "Explain the purpose, behavior, and testing value of this Python code."
        if suffix in {".md", ".txt"}:
            return "Summarize this project documentation into training knowledge."
        if suffix in {".json", ".yaml", ".yml", ".toml"}:
            return "Explain this configuration or structured data for an AI training dataset."
        return "Convert this repository content into safe AI training knowledge."

    @staticmethod
    def _output_for_chunk(path: str, chunk: str) -> str:
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        sample = " ".join(lines[:5])
        return f"Source `{path}` provides project-specific knowledge: {sample[:700]}"

    @staticmethod
    def _quality_score(path: str, chunk: str) -> float:
        score = 0.4
        if Path(path).suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml", ".toml"}:
            score += 0.2
        if len(chunk) > 300:
            score += 0.2
        if any(token in chunk.lower() for token in ("test", "safety", "usage", "example", "architecture")):
            score += 0.2
        return min(round(score, 2), 1.0)
