"""
PeachTree Smart Sampling

Intelligent subset selection with stratified sampling, quality-based selection,
and representative sampling strategies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import random
import hashlib


@dataclass
class SampleResult:
    """Result of sampling operation"""
    source_dataset: str
    output_path: str
    sampling_strategy: str
    source_records: int
    sampled_records: int
    sampling_ratio: float
    sample_timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dataset": self.source_dataset,
            "output_path": self.output_path,
            "sampling_strategy": self.sampling_strategy,
            "source_records": self.source_records,
            "sampled_records": self.sampled_records,
            "sampling_ratio": self.sampling_ratio,
            "sample_timestamp": self.sample_timestamp,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_summary(self) -> str:
        """Generate markdown summary"""
        lines = [
            "# Dataset Sampling Result",
            "",
            f"**Strategy:** {self.sampling_strategy}",
            f"**Source:** {self.source_dataset}",
            f"**Output:** {self.output_path}",
            f"**Source Records:** {self.source_records:,}",
            f"**Sampled Records:** {self.sampled_records:,}",
            f"**Sampling Ratio:** {self.sampling_ratio:.1%}",
            f"**Timestamp:** {self.sample_timestamp}",
            "",
        ]
        
        if self.metadata:
            lines.extend(["## Parameters", ""])
            for key, value in self.metadata.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        return "\n".join(lines)


class SmartSampler:
    """Intelligent dataset sampling with multiple strategies"""
    
    def __init__(self, seed: int | None = None):
        """
        Initialize smart sampler
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.seed = seed
    
    def _calculate_quality_score(self, record: dict[str, Any]) -> float:
        """
        Calculate simple quality score for a record
        
        Args:
            record: Dataset record
        
        Returns:
            Quality score (0-100)
        """
        score = 50.0  # Base score
        
        content = record.get("content", "")
        
        # Length bonus
        if len(content) >= 100:
            score += 20
        elif len(content) >= 50:
            score += 10
        
        # Provenance bonus
        if record.get("source_repo") and record.get("source_path"):
            score += 15
        
        # Digest bonus
        if record.get("digest"):
            score += 15
        
        return min(score, 100.0)
    
    def random_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_size: int | None = None,
        sample_ratio: float | None = None,
    ) -> SampleResult:
        """
        Random sampling of dataset
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_size: Number of records to sample (mutually exclusive with sample_ratio)
            sample_ratio: Ratio of records to sample 0.0-1.0 (mutually exclusive with sample_size)
        
        Returns:
            SampleResult with sampling statistics
        """
        if sample_size is None and sample_ratio is None:
            raise ValueError("Must specify either sample_size or sample_ratio")
        if sample_size is not None and sample_ratio is not None:
            raise ValueError("Cannot specify both sample_size and sample_ratio")
        
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load all records
        records = []
        with open(source_path) as f:
            for line in f:
                if line.strip():
                    records.append(line)
        
        source_records = len(records)
        
        # Calculate sample size
        if sample_ratio is not None:
            sample_size = int(source_records * sample_ratio)
        
        # Sample
        sampled = random.sample(records, min(sample_size, source_records))
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in sampled:
                f.write(record)
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="random",
            source_records=source_records,
            sampled_records=len(sampled),
            sampling_ratio=len(sampled) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={"seed": self.seed},
        )
    
    def quality_based_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_size: int,
        min_quality_score: float = 0.0,
    ) -> SampleResult:
        """
        Sample highest quality records
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_size: Number of records to sample
            min_quality_score: Minimum quality score threshold
        
        Returns:
            SampleResult with sampling statistics
        """
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load records with quality scores
        records_with_scores: list[tuple[str, float]] = []
        
        with open(source_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                score = self._calculate_quality_score(record)
                
                if score >= min_quality_score:
                    records_with_scores.append((line, score))
        
        source_records = len(records_with_scores)
        
        # Sort by quality score (descending)
        records_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N
        sampled = [r[0] for r in records_with_scores[:sample_size]]
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in sampled:
                f.write(record)
        
        avg_quality = sum(r[1] for r in records_with_scores[:len(sampled)]) / len(sampled) if sampled else 0.0
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="quality_based",
            source_records=source_records,
            sampled_records=len(sampled),
            sampling_ratio=len(sampled) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={
                "min_quality_score": min_quality_score,
                "average_quality": avg_quality,
            },
        )
    
    def stratified_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_ratio: float,
        stratify_field: str = "source_repo",
    ) -> SampleResult:
        """
        Stratified sampling to maintain distribution of a field
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_ratio: Ratio of records to sample per stratum
            stratify_field: Field to stratify on
        
        Returns:
            SampleResult with sampling statistics
        """
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Group records by stratify field
        strata: dict[str, list[str]] = {}
        
        with open(source_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                stratum_value = record.get(stratify_field, "unknown")
                
                if stratum_value not in strata:
                    strata[stratum_value] = []
                
                strata[stratum_value].append(line)
        
        # Sample from each stratum
        sampled_records = []
        strata_info: dict[str, dict[str, int]] = {}
        
        for stratum_value, records in strata.items():
            stratum_sample_size = int(len(records) * sample_ratio)
            stratum_sample = random.sample(records, stratum_sample_size)
            sampled_records.extend(stratum_sample)
            
            strata_info[stratum_value] = {
                "total": len(records),
                "sampled": len(stratum_sample),
            }
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in sampled_records:
                f.write(record)
        
        source_records = sum(len(records) for records in strata.values())
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="stratified",
            source_records=source_records,
            sampled_records=len(sampled_records),
            sampling_ratio=len(sampled_records) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={
                "stratify_field": stratify_field,
                "strata_count": len(strata),
                "strata_info": strata_info,
            },
        )
    
    def reservoir_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_size: int,
    ) -> SampleResult:
        """
        Reservoir sampling for streaming/large datasets
        
        Memory-efficient sampling that doesn't require loading entire dataset
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_size: Number of records to sample
        
        Returns:
            SampleResult with sampling statistics
        """
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        reservoir: list[str] = []
        source_records = 0
        
        with open(source_path) as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                
                source_records += 1
                
                if i < sample_size:
                    # Fill reservoir
                    reservoir.append(line)
                else:
                    # Randomly replace elements with decreasing probability
                    j = random.randint(0, i)
                    if j < sample_size:
                        reservoir[j] = line
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in reservoir:
                f.write(record)
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="reservoir",
            source_records=source_records,
            sampled_records=len(reservoir),
            sampling_ratio=len(reservoir) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={"algorithm": "reservoir_sampling"},
        )
    
    def diversity_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_size: int,
        diversity_field: str = "content",
    ) -> SampleResult:
        """
        Sample diverse records to maximize variety
        
        Uses content hashing to select maximally different records
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_size: Number of records to sample
            diversity_field: Field to use for diversity calculation
        
        Returns:
            SampleResult with sampling statistics
        """
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load records with hash prefixes
        records_with_hashes: list[tuple[str, str]] = []
        
        with open(source_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = str(record.get(diversity_field, ""))
                hash_prefix = hashlib.sha256(content.encode()).hexdigest()[:8]
                
                records_with_hashes.append((line, hash_prefix))
        
        source_records = len(records_with_hashes)
        
        # Sort by hash to distribute across hash space
        records_with_hashes.sort(key=lambda x: x[1])
        
        # Sample evenly across sorted list
        step = len(records_with_hashes) / sample_size if sample_size > 0 else 1
        sampled = []
        
        for i in range(sample_size):
            idx = min(int(i * step), len(records_with_hashes) - 1)
            sampled.append(records_with_hashes[idx][0])
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in sampled:
                f.write(record)
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="diversity",
            source_records=source_records,
            sampled_records=len(sampled),
            sampling_ratio=len(sampled) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={"diversity_field": diversity_field},
        )
    
    def time_based_sample(
        self,
        source_dataset: Path | str,
        output_path: Path | str,
        sample_ratio: float,
        time_field: str = "timestamp",
        recent_first: bool = True,
    ) -> SampleResult:
        """
        Sample based on temporal ordering
        
        Args:
            source_dataset: Source dataset path
            output_path: Output sample path
            sample_ratio: Ratio of records to sample
            time_field: Field containing timestamp
            recent_first: Sample most recent records if True, oldest if False
        
        Returns:
            SampleResult with sampling statistics
        """
        source_path = Path(source_dataset)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load records with timestamps
        records_with_time: list[tuple[str, str]] = []
        
        with open(source_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                timestamp = record.get(time_field, "")
                
                records_with_time.append((line, timestamp))
        
        source_records = len(records_with_time)
        
        # Sort by timestamp
        records_with_time.sort(key=lambda x: x[1], reverse=recent_first)
        
        # Sample top N
        sample_size = int(source_records * sample_ratio)
        sampled = [r[0] for r in records_with_time[:sample_size]]
        
        # Write sample
        with open(output_path, 'w') as f:
            for record in sampled:
                f.write(record)
        
        return SampleResult(
            source_dataset=str(source_path),
            output_path=str(output_path),
            sampling_strategy="time_based",
            source_records=source_records,
            sampled_records=len(sampled),
            sampling_ratio=len(sampled) / source_records if source_records > 0 else 0.0,
            sample_timestamp=datetime.now().isoformat(),
            metadata={
                "time_field": time_field,
                "recent_first": recent_first,
            },
        )
