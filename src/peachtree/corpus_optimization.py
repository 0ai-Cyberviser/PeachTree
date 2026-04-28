"""Corpus optimization utilities for fuzzing datasets.

Provides advanced corpus minimization, prioritization, and selection
strategies for efficient fuzzing campaigns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any

from .models import sha256_text


@dataclass(frozen=True)
class CorpusSeed:
    """Represents an optimized corpus seed with metadata."""
    
    seed_id: str
    content: str
    source: str
    priority: float  # 0.0-1.0, higher is more important
    size_bytes: int
    coverage_score: float  # Estimated unique coverage (0.0-1.0)
    crash_potential: float  # Likelihood to find crashes (0.0-1.0)
    minimized: bool = False
    
    @property
    def quality_score(self) -> float:
        """Calculate overall quality score for seed selection."""
        return (
            self.priority * 0.3 +
            self.coverage_score * 0.4 +
            self.crash_potential * 0.3
        )


@dataclass
class CorpusOptimizer:
    """Optimizes fuzzing corpus for maximum efficiency."""
    
    seeds: list[CorpusSeed] = field(default_factory=list)
    target_corpus_size: int = 1000  # Target number of seeds
    max_seed_size: int = 10240  # Maximum seed size in bytes
    min_seed_size: int = 1  # Minimum seed size in bytes
    
    def add_seed_from_record(
        self,
        record: dict[str, Any],
        priority_boost: float = 0.0,
    ) -> CorpusSeed | None:
        """Add a seed from a dataset record.
        
        Args:
            record: Dataset record containing seed content
            priority_boost: Additional priority boost (0.0-1.0)
            
        Returns:
            Created CorpusSeed or None if unsuitable
        """
        text = record.get("text", "")
        metadata = record.get("metadata", {})
        
        # Extract actual seed content (prefer code blocks)
        import re
        code_match = re.search(r"```([^`]+)```", text)
        if code_match:
            content = code_match.group(1).strip()
        else:
            content = text[:self.max_seed_size]
        
        size = len(content.encode("utf-8"))
        
        # Skip if size is out of bounds
        if size < self.min_seed_size or size > self.max_seed_size:
            return None
        
        # Calculate priority
        priority = self._calculate_priority(record, metadata)
        priority = min(1.0, priority + priority_boost)
        
        # Estimate coverage score
        coverage_score = metadata.get("fuzzing_relevance", 0.5)
        if "coverage_metrics" in metadata:
            cov = metadata["coverage_metrics"]
            coverage_score = max(coverage_score, cov.get("block_coverage", 0) / 100.0)
        
        # Estimate crash potential
        crash_potential = 0.3  # Default
        if "crash_signature" in metadata:
            severity = metadata.get("crash_severity", "low")
            crash_potential = {
                "critical": 0.9,
                "high": 0.7,
                "medium": 0.5,
                "low": 0.3,
            }.get(severity, 0.3)
        
        seed_id = sha256_text(content)[:16]
        
        seed = CorpusSeed(
            seed_id=seed_id,
            content=content,
            source=record.get("source_path", "unknown"),
            priority=priority,
            size_bytes=size,
            coverage_score=coverage_score,
            crash_potential=crash_potential,
            minimized=False,
        )
        
        self.seeds.append(seed)
        return seed
    
    def _calculate_priority(self, record: dict[str, Any], metadata: dict[str, Any]) -> float:
        """Calculate priority score for a seed."""
        priority = 0.5  # Base priority
        
        # Boost for crash-triggering inputs
        if "crash_signature" in metadata:
            priority += 0.3
        
        # Boost for coverage-unique inputs
        if metadata.get("coverage_unique", False):
            priority += 0.2
        
        # Boost for high fuzzing relevance
        fuzzing_relevance = float(metadata.get("fuzzing_relevance", 0.0))
        priority += fuzzing_relevance * 0.2
        
        # Boost for high quality score
        quality_score = float(record.get("quality_score", 0.5))
        priority += quality_score * 0.1
        
        return min(1.0, priority)
    
    def optimize(
        self,
        strategy: str = "balanced",
        deduplicate: bool = True,
        minimize: bool = True,
    ) -> dict[str, Any]:
        """Optimize corpus using specified strategy.
        
        Args:
            strategy: Optimization strategy:
                - "balanced": Balance coverage, crashes, and diversity
                - "coverage": Maximize code coverage
                - "crashes": Maximize crash potential
                - "diverse": Maximize input diversity
            deduplicate: Whether to remove duplicate seeds
            minimize: Whether to minimize seed sizes
            
        Returns:
            Optimization statistics
        """
        original_count = len(self.seeds)
        original_size = sum(seed.size_bytes for seed in self.seeds)
        
        # Deduplicate seeds
        if deduplicate:
            self.seeds = self._deduplicate_seeds()
        
        # Minimize seed sizes
        if minimize:
            self.seeds = [self._minimize_seed(seed) for seed in self.seeds]
        
        # Apply selection strategy
        if strategy == "coverage":
            self.seeds = self._select_by_coverage()
        elif strategy == "crashes":
            self.seeds = self._select_by_crash_potential()
        elif strategy == "diverse":
            self.seeds = self._select_by_diversity()
        else:  # balanced
            self.seeds = self._select_balanced()
        
        optimized_count = len(self.seeds)
        optimized_size = sum(seed.size_bytes for seed in self.seeds)
        
        return {
            "original_count": original_count,
            "optimized_count": optimized_count,
            "reduction_ratio": (original_count - optimized_count) / original_count if original_count > 0 else 0.0,
            "original_size_bytes": original_size,
            "optimized_size_bytes": optimized_size,
            "size_reduction_ratio": (original_size - optimized_size) / original_size if original_size > 0 else 0.0,
            "strategy": strategy,
            "deduplicated": deduplicate,
            "minimized": minimize,
        }
    
    def _deduplicate_seeds(self) -> list[CorpusSeed]:
        """Remove duplicate seeds by content hash."""
        seen_ids: set[str] = set()
        deduplicated: list[CorpusSeed] = []
        
        # Sort by quality score (keep highest quality duplicates)
        sorted_seeds = sorted(self.seeds, key=lambda s: s.quality_score, reverse=True)
        
        for seed in sorted_seeds:
            if seed.seed_id not in seen_ids:
                seen_ids.add(seed.seed_id)
                deduplicated.append(seed)
        
        return deduplicated
    
    def _minimize_seed(self, seed: CorpusSeed) -> CorpusSeed:
        """Minimize a single seed by removing unnecessary content."""
        if seed.minimized:
            return seed
        
        content = seed.content
        
        # Remove comments and whitespace
        lines = content.splitlines()
        minimized_lines = []
        for line in lines:
            # Remove inline comments
            if "#" in line:
                line = line[:line.index("#")]
            if "//" in line:
                line = line[:line.index("//")]
            # Remove trailing whitespace
            line = line.rstrip()
            if line:
                minimized_lines.append(line)
        
        minimized_content = "\n".join(minimized_lines)
        
        # Only use minimized version if it's significantly smaller
        if len(minimized_content) < len(content) * 0.8:
            from dataclasses import replace
            return replace(
                seed,
                content=minimized_content,
                size_bytes=len(minimized_content.encode("utf-8")),
                minimized=True,
            )
        
        from dataclasses import replace
        return replace(seed, minimized=True)
    
    def _select_by_coverage(self) -> list[CorpusSeed]:
        """Select seeds prioritizing code coverage."""
        sorted_seeds = sorted(
            self.seeds,
            key=lambda s: (s.coverage_score, s.quality_score),
            reverse=True,
        )
        return sorted_seeds[:self.target_corpus_size]
    
    def _select_by_crash_potential(self) -> list[CorpusSeed]:
        """Select seeds prioritizing crash potential."""
        sorted_seeds = sorted(
            self.seeds,
            key=lambda s: (s.crash_potential, s.quality_score),
            reverse=True,
        )
        return sorted_seeds[:self.target_corpus_size]
    
    def _select_by_diversity(self) -> list[CorpusSeed]:
        """Select seeds prioritizing input diversity."""
        if not self.seeds:
            return []
        
        selected: list[CorpusSeed] = []
        remaining = list(self.seeds)
        
        # Start with highest quality seed
        remaining.sort(key=lambda s: s.quality_score, reverse=True)
        selected.append(remaining.pop(0))
        
        # Iteratively select most diverse seeds
        while remaining and len(selected) < self.target_corpus_size:
            # Find seed most different from existing selection
            best_seed = max(
                remaining,
                key=lambda s: self._diversity_score(s, selected),
            )
            selected.append(best_seed)
            remaining.remove(best_seed)
        
        return selected
    
    def _diversity_score(self, seed: CorpusSeed, selected: list[CorpusSeed]) -> float:
        """Calculate diversity score for a seed compared to selected seeds."""
        if not selected:
            return seed.quality_score
        
        # Simple diversity measure: average Jaccard distance of content
        seed_tokens = set(seed.content.split())
        
        total_distance = 0.0
        for existing in selected:
            existing_tokens = set(existing.content.split())
            intersection = len(seed_tokens & existing_tokens)
            union = len(seed_tokens | existing_tokens)
            jaccard = intersection / union if union > 0 else 0.0
            distance = 1.0 - jaccard
            total_distance += distance
        
        avg_distance = total_distance / len(selected)
        
        # Combine diversity with quality
        return avg_distance * 0.7 + seed.quality_score * 0.3
    
    def _select_balanced(self) -> list[CorpusSeed]:
        """Select seeds using balanced strategy."""
        sorted_seeds = sorted(
            self.seeds,
            key=lambda s: s.quality_score,
            reverse=True,
        )
        return sorted_seeds[:self.target_corpus_size]
    
    def export_optimized_corpus(
        self,
        output_dir: str | Path,
    ) -> dict[str, Any]:
        """Export optimized corpus to directory.
        
        Args:
            output_dir: Directory to write corpus files
            
        Returns:
            Export statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write individual seed files
        for i, seed in enumerate(self.seeds):
            filename = f"seed_{i:06d}_{seed.seed_id}.txt"
            (output_dir / filename).write_text(seed.content, encoding="utf-8")
        
        # Write corpus manifest
        manifest = {
            "version": "1.0",
            "total_seeds": len(self.seeds),
            "target_corpus_size": self.target_corpus_size,
            "seeds": [
                {
                    "seed_id": seed.seed_id,
                    "filename": f"seed_{i:06d}_{seed.seed_id}.txt",
                    "priority": seed.priority,
                    "size_bytes": seed.size_bytes,
                    "coverage_score": seed.coverage_score,
                    "crash_potential": seed.crash_potential,
                    "quality_score": seed.quality_score,
                    "minimized": seed.minimized,
                }
                for i, seed in enumerate(self.seeds)
            ],
        }
        
        (output_dir / "corpus_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        
        return {
            "output_directory": str(output_dir),
            "seeds_exported": len(self.seeds),
            "manifest_path": str(output_dir / "corpus_manifest.json"),
            "total_size_bytes": sum(seed.size_bytes for seed in self.seeds),
        }


def optimize_fuzzing_corpus(
    dataset_path: str | Path,
    output_dir: str | Path,
    target_size: int = 1000,
    strategy: str = "balanced",
) -> dict[str, Any]:
    """Convenience function to optimize a fuzzing corpus from dataset.
    
    Args:
        dataset_path: Path to PeachTree JSONL dataset
        output_dir: Directory to write optimized corpus
        target_size: Target number of corpus seeds
        strategy: Optimization strategy (balanced, coverage, crashes, diverse)
        
    Returns:
        Optimization and export statistics
    """
    optimizer = CorpusOptimizer(target_corpus_size=target_size)
    
    # Load dataset
    dataset_path = Path(dataset_path)
    for line in dataset_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            optimizer.add_seed_from_record(record)
    
    # Optimize
    opt_stats = optimizer.optimize(
        strategy=strategy,
        deduplicate=True,
        minimize=True,
    )
    
    # Export
    export_stats = optimizer.export_optimized_corpus(output_dir)
    
    return {
        "optimization": opt_stats,
        "export": export_stats,
        "strategy": strategy,
    }
