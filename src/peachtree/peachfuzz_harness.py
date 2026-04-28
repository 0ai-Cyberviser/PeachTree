"""Enhanced PeachFuzz harness integration for PeachTree.

Provides advanced fuzzing corpus generation, crash triage workflows,
and harness configuration for PeachFuzz defensive fuzzing engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import json
from typing import Any

from .models import DatasetRecord, SourceDocument, sha256_text


@dataclass(frozen=True)
class FuzzTarget:
    """Represents a fuzzing target configuration."""
    
    name: str
    target_binary: str
    target_args: tuple[str, ...] = field(default_factory=tuple)
    dictionary: str | None = None
    max_len: int = 4096
    timeout: int = 1200  # 20 minutes
    memory_limit: int = 2048  # MB
    
    @property
    def target_id(self) -> str:
        """Generate unique target ID."""
        return sha256_text(f"{self.name}:{self.target_binary}")[:16]


@dataclass(frozen=True)
class CorpusItem:
    """Represents a single fuzzing corpus item."""
    
    content: str
    source: str
    crash_signature: str | None = None
    coverage_unique: bool = False
    minimized: bool = False
    interesting: bool = True
    
    @property
    def corpus_id(self) -> str:
        """Generate unique corpus item ID."""
        return sha256_text(self.content)[:16]


@dataclass
class PeachFuzzHarness:
    """Manages PeachFuzz harness generation and corpus optimization."""
    
    targets: list[FuzzTarget] = field(default_factory=list)
    corpus_items: list[CorpusItem] = field(default_factory=list)
    coverage_db: dict[str, set[str]] = field(default_factory=dict)
    
    def add_target(self, target: FuzzTarget) -> None:
        """Add a fuzzing target to the harness."""
        self.targets.append(target)
        self.coverage_db[target.target_id] = set()
    
    def add_corpus_item(
        self,
        content: str,
        source: str,
        crash_signature: str | None = None,
        coverage_unique: bool = False,
    ) -> CorpusItem:
        """Add a corpus item to the fuzzing corpus.
        
        Args:
            content: Corpus file content (input that triggers interesting behavior)
            source: Source description (e.g., "crash-report-123", "seed-file")
            crash_signature: Optional crash signature if this triggers a crash
            coverage_unique: Whether this input triggers unique coverage
            
        Returns:
            Created CorpusItem
        """
        item = CorpusItem(
            content=content,
            source=source,
            crash_signature=crash_signature,
            coverage_unique=coverage_unique,
            minimized=False,
            interesting=crash_signature is not None or coverage_unique,
        )
        self.corpus_items.append(item)
        return item
    
    def from_dataset(
        self,
        dataset_path: str | Path,
        extract_crashes: bool = True,
        extract_seeds: bool = True,
    ) -> int:
        """Build fuzzing corpus from PeachTree dataset.
        
        Args:
            dataset_path: Path to PeachTree JSONL dataset
            extract_crashes: Whether to extract crash reproducers
            extract_seeds: Whether to extract seed inputs
            
        Returns:
            Number of corpus items added
        """
        dataset_path = Path(dataset_path)
        records = []
        for line in dataset_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        
        added = 0
        for record in records:
            metadata = record.get("metadata", {})
            text = record.get("text", "")
            
            # Extract crash reproducers
            if extract_crashes and "crash_signature" in metadata:
                crash_sig = metadata["crash_signature"]
                # Look for reproducible input in text
                reproducer = self._extract_reproducer(text)
                if reproducer:
                    self.add_corpus_item(
                        content=reproducer,
                        source=f"crash:{crash_sig}",
                        crash_signature=crash_sig,
                        coverage_unique=False,
                    )
                    added += 1
            
            # Extract seed inputs
            if extract_seeds and self._is_seed_candidate(record):
                seed_content = self._extract_seed_content(text)
                if seed_content:
                    self.add_corpus_item(
                        content=seed_content,
                        source=record.get("source_path", "unknown"),
                        crash_signature=None,
                        coverage_unique=metadata.get("coverage_unique", False),
                    )
                    added += 1
        
        return added
    
    def _extract_reproducer(self, text: str) -> str | None:
        """Extract crash reproducer input from text content."""
        import re
        
        # Look for common reproducer patterns
        patterns = [
            r"Input:\s*(.+?)(?:\n\n|\Z)",
            r"Reproducer:\s*(.+?)(?:\n\n|\Z)",
            r"Crash input:\s*(.+?)(?:\n\n|\Z)",
            r"POC:\s*(.+?)(?:\n\n|\Z)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look for hex dumps
        hex_pattern = r"([0-9a-fA-F]{2}\s+){8,}"
        if re.search(hex_pattern, text):
            # Extract hex dump and convert to bytes
            hex_matches = re.findall(r"[0-9a-fA-F]{2}", text)
            if hex_matches:
                return " ".join(hex_matches[:256])  # Limit size
        
        return None
    
    def _is_seed_candidate(self, record: dict[str, Any]) -> bool:
        """Check if record is a good seed corpus candidate."""
        metadata = record.get("metadata", {})
        
        # High fuzzing relevance
        if metadata.get("fuzzing_relevance", 0) >= 0.5:
            return True
        
        # Has coverage information
        if "coverage_metrics" in metadata:
            return True
        
        # Tagged as seed
        tags = metadata.get("tags", [])
        if any(tag.startswith("seed:") for tag in tags):
            return True
        
        return False
    
    def _extract_seed_content(self, text: str) -> str | None:
        """Extract seed content from text."""
        import re
        
        # Look for file content sections
        patterns = [
            r"```([^`]+)```",  # Code blocks
            r"File content:\s*(.+?)(?:\n\n|\Z)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                if 10 <= len(content) <= 4096:  # Reasonable size
                    return content
        
        return None
    
    def optimize_corpus(
        self,
        minimize: bool = True,
        deduplicate: bool = True,
    ) -> dict[str, Any]:
        """Optimize fuzzing corpus by minimizing and deduplicating.
        
        Args:
            minimize: Whether to minimize corpus items
            deduplicate: Whether to remove duplicate coverage
            
        Returns:
            Optimization statistics
        """
        original_count = len(self.corpus_items)
        
        if minimize:
            self.corpus_items = [
                self._minimize_corpus_item(item) for item in self.corpus_items
            ]
        
        if deduplicate:
            self.corpus_items = self._deduplicate_corpus()
        
        optimized_count = len(self.corpus_items)
        
        return {
            "original_count": original_count,
            "optimized_count": optimized_count,
            "reduction_ratio": (original_count - optimized_count) / original_count if original_count > 0 else 0.0,
            "minimized": minimize,
            "deduplicated": deduplicate,
        }
    
    def _minimize_corpus_item(self, item: CorpusItem) -> CorpusItem:
        """Minimize a corpus item by removing unnecessary content."""
        if item.minimized:
            return item
        
        content = item.content
        
        # Simple minimization: remove whitespace, comments
        lines = content.splitlines()
        minimized_lines = []
        for line in lines:
            # Remove comments
            if line.strip().startswith("#"):
                continue
            # Remove trailing whitespace
            line = line.rstrip()
            if line:
                minimized_lines.append(line)
        
        minimized_content = "\n".join(minimized_lines)
        
        # If minimization achieved >10% reduction, use it
        if len(minimized_content) < len(content) * 0.9:
            return replace(item, content=minimized_content, minimized=True)
        
        return replace(item, minimized=True)
    
    def _deduplicate_corpus(self) -> list[CorpusItem]:
        """Remove duplicate corpus items based on content hash."""
        seen_hashes: set[str] = set()
        deduplicated: list[CorpusItem] = []
        
        # Prioritize crash-triggering and coverage-unique items
        sorted_items = sorted(
            self.corpus_items,
            key=lambda x: (
                x.crash_signature is not None,
                x.coverage_unique,
                x.interesting,
            ),
            reverse=True,
        )
        
        for item in sorted_items:
            content_hash = sha256_text(item.content)
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduplicated.append(item)
        
        return deduplicated
    
    def generate_harness_config(
        self,
        output_path: str | Path,
        format: str = "json",
    ) -> Path:
        """Generate PeachFuzz harness configuration file.
        
        Args:
            output_path: Path to write configuration
            format: Output format ('json' or 'yaml')
            
        Returns:
            Path to generated configuration file
        """
        output_path = Path(output_path)
        
        config = {
            "version": "1.0",
            "harness_type": "peachfuzz",
            "targets": [
                {
                    "name": target.name,
                    "target_binary": target.target_binary,
                    "target_args": list(target.target_args),
                    "dictionary": target.dictionary,
                    "max_len": target.max_len,
                    "timeout": target.timeout,
                    "memory_limit": target.memory_limit,
                    "target_id": target.target_id,
                }
                for target in self.targets
            ],
            "corpus": [
                {
                    "corpus_id": item.corpus_id,
                    "source": item.source,
                    "crash_signature": item.crash_signature,
                    "coverage_unique": item.coverage_unique,
                    "minimized": item.minimized,
                    "content_length": len(item.content),
                }
                for item in self.corpus_items
            ],
            "statistics": {
                "total_targets": len(self.targets),
                "total_corpus_items": len(self.corpus_items),
                "crash_reproducers": sum(1 for item in self.corpus_items if item.crash_signature),
                "coverage_unique": sum(1 for item in self.corpus_items if item.coverage_unique),
            },
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            output_path.write_text(
                json.dumps(config, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        elif format == "yaml":
            try:
                import yaml
                output_path.write_text(
                    yaml.dump(config, default_flow_style=False, sort_keys=True),
                    encoding="utf-8",
                )
            except ImportError:
                # Fallback to JSON if YAML not available
                output_path = output_path.with_suffix(".json")
                output_path.write_text(
                    json.dumps(config, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
        
        return output_path
    
    def export_corpus_directory(
        self,
        output_dir: str | Path,
    ) -> dict[str, Any]:
        """Export corpus items to individual files in a directory.
        
        Args:
            output_dir: Directory to write corpus files
            
        Returns:
            Export statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported = 0
        for item in self.corpus_items:
            filename = f"{item.corpus_id}.txt"
            file_path = output_dir / filename
            file_path.write_text(item.content, encoding="utf-8")
            exported += 1
        
        # Write metadata manifest
        manifest = {
            "version": "1.0",
            "total_items": len(self.corpus_items),
            "items": [
                {
                    "corpus_id": item.corpus_id,
                    "filename": f"{item.corpus_id}.txt",
                    "source": item.source,
                    "crash_signature": item.crash_signature,
                    "coverage_unique": item.coverage_unique,
                }
                for item in self.corpus_items
            ],
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        
        return {
            "output_directory": str(output_dir),
            "files_exported": exported,
            "manifest_path": str(output_dir / "manifest.json"),
        }


def build_peachfuzz_harness(
    dataset_path: str | Path,
    output_config: str | Path,
    output_corpus_dir: str | Path,
) -> dict[str, Any]:
    """Convenience function to build complete PeachFuzz harness from dataset.
    
    Args:
        dataset_path: Path to PeachTree JSONL dataset
        output_config: Path to write harness configuration
        output_corpus_dir: Directory to export corpus files
        
    Returns:
        Build summary with paths and statistics
    """
    harness = PeachFuzzHarness()
    
    # Build corpus from dataset
    items_added = harness.from_dataset(dataset_path)
    
    # Optimize corpus
    optimization = harness.optimize_corpus(minimize=True, deduplicate=True)
    
    # Generate configuration
    config_path = harness.generate_harness_config(output_config)
    
    # Export corpus directory
    export_stats = harness.export_corpus_directory(output_corpus_dir)
    
    return {
        "dataset_path": str(dataset_path),
        "corpus_items_extracted": items_added,
        "optimization": optimization,
        "config_path": str(config_path),
        "corpus_export": export_stats,
    }
