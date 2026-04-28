"""Fuzzing-specific dataset enrichment for PeachTree.

Enhances datasets with fuzzing metadata, crash signatures, coverage metrics,
and triage information for training security-focused LLMs and fuzzing agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Any



@dataclass(frozen=True)
class CrashSignature:
    """Represents a crash or vulnerability signature."""
    
    crash_type: str  # segfault, assertion, heap-overflow, etc.
    severity: str  # critical, high, medium, low
    signal: str | None = None  # SIGSEGV, SIGABRT, etc.
    address: str | None = None  # Crash address if available
    stack_trace_hash: str | None = None  # Hash of stack trace for dedup
    sanitizer_output: str | None = None  # ASAN, MSAN, UBSAN output
    
    @property
    def signature(self) -> str:
        """Generate unique signature for crash deduplication."""
        parts = [self.crash_type, self.severity]
        if self.signal:
            parts.append(self.signal)
        if self.stack_trace_hash:
            parts.append(self.stack_trace_hash[:16])
        return "-".join(parts)


@dataclass(frozen=True)
class CoverageMetrics:
    """Code coverage metrics for fuzzing corpus."""
    
    total_blocks: int
    covered_blocks: int
    total_edges: int
    covered_edges: int
    total_functions: int
    covered_functions: int
    
    @property
    def block_coverage(self) -> float:
        """Calculate block coverage percentage."""
        return (self.covered_blocks / self.total_blocks * 100) if self.total_blocks > 0 else 0.0
    
    @property
    def edge_coverage(self) -> float:
        """Calculate edge coverage percentage."""
        return (self.covered_edges / self.total_edges * 100) if self.total_edges > 0 else 0.0
    
    @property
    def function_coverage(self) -> float:
        """Calculate function coverage percentage."""
        return (self.covered_functions / self.total_functions * 100) if self.total_functions > 0 else 0.0


@dataclass
class FuzzingEnrichment:
    """Enriches dataset records with fuzzing-specific metadata."""
    
    crash_patterns: dict[str, list[str]] = field(default_factory=dict)
    coverage_database: dict[str, CoverageMetrics] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize default crash patterns."""
        if not self.crash_patterns:
            self.crash_patterns = {
                "segfault": [
                    r"SIGSEGV",
                    r"Segmentation fault",
                    r"signal 11",
                    r"access violation",
                ],
                "heap-overflow": [
                    r"heap-buffer-overflow",
                    r"AddressSanitizer.*heap-buffer-overflow",
                    r"heap overflow",
                ],
                "use-after-free": [
                    r"use-after-free",
                    r"AddressSanitizer.*heap-use-after-free",
                ],
                "assertion": [
                    r"assertion failed",
                    r"assert\(",
                    r"SIGABRT",
                ],
                "timeout": [
                    r"timeout",
                    r"hung",
                    r"slow-unit",
                ],
            }
    
    def enrich_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Enrich a dataset record with fuzzing metadata.
        
        Args:
            record: Original dataset record
            
        Returns:
            Enriched record with fuzzing metadata added
        """
        text = record.get("text", "")
        metadata = record.get("metadata", {})
        
        # Detect crash signatures
        crash_sig = self._detect_crash_signature(text)
        if crash_sig:
            metadata["crash_signature"] = crash_sig.signature
            metadata["crash_type"] = crash_sig.crash_type
            metadata["crash_severity"] = crash_sig.severity
            if crash_sig.signal:
                metadata["crash_signal"] = crash_sig.signal
        
        # Extract coverage metrics
        coverage = self._extract_coverage(text)
        if coverage:
            metadata["coverage_metrics"] = {
                "block_coverage": coverage.block_coverage,
                "edge_coverage": coverage.edge_coverage,
                "function_coverage": coverage.function_coverage,
            }
        
        # Classify fuzzing relevance
        metadata["fuzzing_relevance"] = self._calculate_fuzzing_relevance(text, crash_sig, coverage)
        
        # Add fuzzing tags
        tags = metadata.get("tags", [])
        tags.extend(self._generate_fuzzing_tags(text, crash_sig))
        metadata["tags"] = list(set(tags))  # Deduplicate
        
        # Update record
        enriched = record.copy()
        enriched["metadata"] = metadata
        
        # Boost quality score for high-value fuzzing content
        if crash_sig and crash_sig.severity in ("critical", "high"):
            original_score = enriched.get("quality_score", 0.5)
            enriched["quality_score"] = min(1.0, original_score * 1.3)
        
        return enriched
    
    def _detect_crash_signature(self, text: str) -> CrashSignature | None:
        """Detect crash signature from text content."""
        crash_type = None
        severity = "low"
        signal = None
        address = None
        sanitizer_output = None
        
        # Detect crash type (prioritize specific types over generic)
        # Order matters - check heap-overflow before segfault
        priority_order = ["heap-overflow", "use-after-free", "assertion", "timeout", "segfault"]
        for crash_name in priority_order:
            if crash_name not in self.crash_patterns:
                continue
            for pattern in self.crash_patterns[crash_name]:
                if re.search(pattern, text, re.IGNORECASE):
                    crash_type = crash_name
                    break
            if crash_type:
                break
        
        if not crash_type:
            return None
        
        # Extract signal
        signal_match = re.search(r"(SIGSEGV|SIGABRT|SIGILL|SIGFPE|SIGBUS)", text)
        if signal_match:
            signal = signal_match.group(1)
        
        # Extract crash address
        addr_match = re.search(r"0x[0-9a-fA-F]{8,16}", text)
        if addr_match:
            address = addr_match.group(0)
        
        # Extract sanitizer output
        asan_match = re.search(r"(AddressSanitizer|MemorySanitizer|UndefinedBehaviorSanitizer).*", text)
        if asan_match:
            sanitizer_output = asan_match.group(0)[:200]
        
        # Determine severity
        if crash_type in ("heap-overflow", "use-after-free"):
            severity = "critical"
        elif crash_type == "segfault":
            severity = "high"
        elif crash_type == "assertion":
            severity = "medium"
        elif crash_type == "timeout":
            severity = "low"
        
        # Generate stack trace hash for deduplication
        stack_trace_hash = None
        if sanitizer_output:
            # Simple hash based on sanitizer output
            import hashlib
            stack_trace_hash = hashlib.sha256(sanitizer_output.encode()).hexdigest()
        
        return CrashSignature(
            crash_type=crash_type,
            severity=severity,
            signal=signal,
            address=address,
            stack_trace_hash=stack_trace_hash,
            sanitizer_output=sanitizer_output,
        )
    
    def _extract_coverage(self, text: str) -> CoverageMetrics | None:
        """Extract coverage metrics from text content."""
        # Match common coverage report formats
        # Example: "coverage: 1234/5678 blocks (21.7%)"
        block_match = re.search(r"(\d+)/(\d+)\s+blocks", text)
        edge_match = re.search(r"(\d+)/(\d+)\s+edges", text)
        func_match = re.search(r"(\d+)/(\d+)\s+functions", text)
        
        if not any([block_match, edge_match, func_match]):
            return None
        
        def extract_counts(match: re.Match[str] | None, default: tuple[int, int] = (0, 0)) -> tuple[int, int]:
            if match:
                return int(match.group(1)), int(match.group(2))
            return default
        
        covered_blocks, total_blocks = extract_counts(block_match)
        covered_edges, total_edges = extract_counts(edge_match)
        covered_funcs, total_funcs = extract_counts(func_match)
        
        return CoverageMetrics(
            total_blocks=total_blocks,
            covered_blocks=covered_blocks,
            total_edges=total_edges,
            covered_edges=covered_edges,
            total_functions=total_funcs,
            covered_functions=covered_funcs,
        )
    
    def _calculate_fuzzing_relevance(
        self,
        text: str,
        crash_sig: CrashSignature | None,
        coverage: CoverageMetrics | None,
    ) -> float:
        """Calculate fuzzing relevance score (0.0-1.0)."""
        score = 0.0
        
        # Crash information is highly relevant
        if crash_sig:
            if crash_sig.severity == "critical":
                score += 0.5
            elif crash_sig.severity == "high":
                score += 0.4
            elif crash_sig.severity == "medium":
                score += 0.3
            else:
                score += 0.2
        
        # Coverage information is valuable
        if coverage and coverage.block_coverage > 0:
            score += 0.2
        
        # Fuzzing-related keywords
        fuzzing_keywords = [
            "fuzzing", "fuzz", "crash", "sanitizer", "coverage",
            "corpus", "seed", "mutation", "harness", "target",
            "afl", "libfuzzer", "reproducer", "poc",
        ]
        keyword_count = sum(1 for kw in fuzzing_keywords if kw.lower() in text.lower())
        score += min(0.4, keyword_count * 0.06)
        
        return min(1.0, score)
    
    def _generate_fuzzing_tags(
        self,
        text: str,
        crash_sig: CrashSignature | None,
    ) -> list[str]:
        """Generate fuzzing-related tags for the record."""
        tags = []
        
        if crash_sig:
            tags.append(f"crash:{crash_sig.crash_type}")
            tags.append(f"severity:{crash_sig.severity}")
            if crash_sig.signal:
                tags.append(f"signal:{crash_sig.signal}")
        
        # Detect fuzzing frameworks
        frameworks = {
            "AFL++": r"afl-fuzz|AFL\+\+",
            "libFuzzer": r"libFuzzer",
            "Honggfuzz": r"honggfuzz",
            "PeachFuzz": r"peachfuzz",
        }
        for framework, pattern in frameworks.items():
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(f"framework:{framework}")
        
        # Detect sanitizers
        if "AddressSanitizer" in text:
            tags.append("sanitizer:ASAN")
        if "MemorySanitizer" in text:
            tags.append("sanitizer:MSAN")
        if "UndefinedBehaviorSanitizer" in text:
            tags.append("sanitizer:UBSAN")
        
        return tags
    
    def enrich_dataset(
        self,
        dataset_path: str | Path,
        output_path: str | Path,
    ) -> dict[str, Any]:
        """Enrich entire dataset with fuzzing metadata.
        
        Args:
            dataset_path: Path to input JSONL dataset
            output_path: Path to write enriched JSONL dataset
            
        Returns:
            Summary statistics of enrichment
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        
        records = []
        for line in dataset_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        
        enriched_records = []
        crash_count = 0
        coverage_count = 0
        high_relevance_count = 0
        
        for record in records:
            enriched = self.enrich_record(record)
            enriched_records.append(enriched)
            
            metadata = enriched.get("metadata", {})
            if "crash_signature" in metadata:
                crash_count += 1
            if "coverage_metrics" in metadata:
                coverage_count += 1
            if metadata.get("fuzzing_relevance", 0) >= 0.7:
                high_relevance_count += 1
        
        # Write enriched dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in enriched_records) + "\n",
            encoding="utf-8",
        )
        
        return {
            "total_records": len(records),
            "enriched_records": len(enriched_records),
            "crash_signatures_detected": crash_count,
            "coverage_metrics_extracted": coverage_count,
            "high_relevance_records": high_relevance_count,
            "output_path": str(output_path),
        }


def enrich_fuzzing_corpus(
    source_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Convenience function to enrich a fuzzing corpus dataset.
    
    Args:
        source_path: Path to source JSONL dataset
        output_path: Path to write enriched dataset
        
    Returns:
        Enrichment summary statistics
    """
    enricher = FuzzingEnrichment()
    return enricher.enrich_dataset(source_path, output_path)
