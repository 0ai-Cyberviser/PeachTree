"""Dataset sampling for creating representative subsets.

Provides multiple sampling strategies including random, stratified,
reservoir, and systematic sampling with validation and statistics.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import json
import random
import hashlib


class SamplingStrategy(Enum):
    """Sampling strategies."""
    RANDOM = "random"
    STRATIFIED = "stratified"
    RESERVOIR = "reservoir"
    SYSTEMATIC = "systematic"
    WEIGHTED = "weighted"


class SampleValidationLevel(Enum):
    """Sample validation strictness."""
    NONE = "none"
    BASIC = "basic"
    FULL = "full"


@dataclass
class SamplingConfig:
    """Sampling configuration."""
    strategy: SamplingStrategy
    sample_size: int
    stratify_field: Optional[str] = None
    weights_field: Optional[str] = None
    random_seed: Optional[int] = None
    validation_level: SampleValidationLevel = SampleValidationLevel.BASIC
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy": self.strategy.value,
            "sample_size": self.sample_size,
            "stratify_field": self.stratify_field,
            "weights_field": self.weights_field,
            "random_seed": self.random_seed,
            "validation_level": self.validation_level.value,
            "metadata": self.metadata,
        }


@dataclass
class SampleStatistics:
    """Sample statistics."""
    total_records: int
    sampled_records: int
    sample_ratio: float
    strategy_used: SamplingStrategy
    sampling_time_ms: float
    distribution: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_records": self.total_records,
            "sampled_records": self.sampled_records,
            "sample_ratio": self.sample_ratio,
            "strategy_used": self.strategy_used.value,
            "sampling_time_ms": self.sampling_time_ms,
            "distribution": self.distribution,
        }


@dataclass
class SampleResult:
    """Sampling result."""
    sample_id: str
    config: SamplingConfig
    statistics: SampleStatistics
    sample_path: Path
    created_at: datetime
    validation_passed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_id": self.sample_id,
            "config": self.config.to_dict(),
            "statistics": self.statistics.to_dict(),
            "sample_path": str(self.sample_path),
            "created_at": self.created_at.isoformat(),
            "validation_passed": self.validation_passed,
        }


class RandomSampler:
    """Random sampling without replacement."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize random sampler."""
        self.seed = seed
        self.random = random.Random(seed)
    
    def sample(
        self,
        dataset_path: Path,
        output_path: Path,
        sample_size: int,
    ) -> int:
        """Sample records randomly from dataset file."""
        records = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        if sample_size >= len(records):
            sampled = records.copy()
        else:
            sampled = self.random.sample(records, sample_size)
        
        with open(output_path, "w") as f:
            for record in sampled:
                f.write(json.dumps(record) + "\n")
        
        return len(sampled)


class StratifiedSampler:
    """Stratified sampling to maintain class distribution."""
    
    def __init__(self, stratify_field: str, seed: Optional[int] = None):
        """Initialize stratified sampler."""
        self.stratify_field = stratify_field
        self.seed = seed
        self.random = random.Random(seed)
    
    def sample(
        self,
        dataset_path: Path,
        output_path: Path,
        sample_size: int,
    ) -> int:
        """Sample records with stratification from dataset file."""
        records = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # Group by stratify field
        strata: Dict[Any, List[Dict[str, Any]]] = {}
        for record in records:
            key = record.get(self.stratify_field)
            if key not in strata:
                strata[key] = []
            strata[key].append(record)
        
        # Calculate samples per stratum
        total = len(records)
        samples = []
        
        for key, stratum_records in strata.items():
            stratum_size = len(stratum_records)
            stratum_sample_size = int((stratum_size / total) * sample_size)
            
            # Sample from this stratum
            if stratum_sample_size > 0:
                stratum_sample = self.random.sample(
                    stratum_records,
                    min(stratum_sample_size, stratum_size)
                )
                samples.extend(stratum_sample)
        
        # If we haven't reached sample_size, add more randomly
        if len(samples) < sample_size:
            remaining = [r for r in records if r not in samples]
            additional = self.random.sample(
                remaining,
                min(sample_size - len(samples), len(remaining))
            )
            samples.extend(additional)
        
        return samples


class ReservoirSampler:
    """Reservoir sampling for streaming data."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize reservoir sampler."""
        self.seed = seed
        self.random = random.Random(seed)
    
    def sample(
        self,
        records: List[Dict[str, Any]],
        sample_size: int,
    ) -> List[Dict[str, Any]]:
        """Sample using reservoir algorithm."""
        reservoir = []
        
        for i, record in enumerate(records):
            if i < sample_size:
                reservoir.append(record)
            else:
                # Randomly replace elements
                j = self.random.randint(0, i)
                if j < sample_size:
                    reservoir[j] = record
        
        return reservoir


class SystematicSampler:
    """Systematic sampling with fixed intervals."""
    
    def __init__(self):
        """Initialize systematic sampler."""
        pass
    
    def sample(
        self,
        records: List[Dict[str, Any]],
        sample_size: int,
    ) -> List[Dict[str, Any]]:
        """Sample at regular intervals."""
        if sample_size >= len(records):
            return records.copy()
        
        interval = len(records) / sample_size
        samples = []
        
        for i in range(sample_size):
            index = int(i * interval)
            if index < len(records):
                samples.append(records[index])
        
        return samples


class WeightedSampler:
    """Weighted sampling based on field values."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize weighted sampler."""
        self.random = random.Random(seed)
    
    def sample(
        self,
        records: List[Dict[str, Any]],
        sample_size: int,
        weights_field: str,
    ) -> List[Dict[str, Any]]:
        """Sample with weights."""
        # Get weights
        weights = [float(r.get(weights_field, 1.0)) for r in records]
        total_weight = sum(weights)
        
        # Normalize weights
        probabilities = [w / total_weight for w in weights]
        
        # Sample with replacement based on weights
        samples = []
        for _ in range(sample_size):
            r = self.random.random()
            cumulative = 0.0
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    samples.append(records[i])
                    break
        
        return samples


class SampleValidator:
    """Validate sample quality."""
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    def validate_sample(
        self,
        original_records: List[Dict[str, Any]],
        sample_records: List[Dict[str, Any]],
        config: SamplingConfig,
    ) -> Dict[str, Any]:
        """Validate sample against original."""
        issues = []
        
        # Basic checks
        if len(sample_records) > len(original_records):
            issues.append("Sample size exceeds original size")
        
        if config.sample_size != len(sample_records):
            issues.append(f"Expected {config.sample_size} samples, got {len(sample_records)}")
        
        # Check for duplicates
        if config.strategy != SamplingStrategy.WEIGHTED:
            sample_ids = [id(r) for r in sample_records]
            if len(sample_ids) != len(set(sample_ids)):
                issues.append("Duplicate records in sample")
        
        # Stratification check
        if config.strategy == SamplingStrategy.STRATIFIED and config.stratify_field:
            original_dist = self._get_distribution(original_records, config.stratify_field)
            sample_dist = self._get_distribution(sample_records, config.stratify_field)
            
            # Compare distributions
            for key in original_dist:
                original_ratio = original_dist[key] / len(original_records)
                sample_ratio = sample_dist.get(key, 0) / max(len(sample_records), 1)
                
                if abs(original_ratio - sample_ratio) > 0.1:  # 10% threshold
                    issues.append(f"Distribution mismatch for {key}: {original_ratio:.2f} vs {sample_ratio:.2f}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "sample_size": len(sample_records),
        }
    
    def _get_distribution(
        self,
        records: List[Dict[str, Any]],
        field: str,
    ) -> Dict[Any, int]:
        """Get distribution of field values."""
        dist: Dict[Any, int] = {}
        for record in records:
            value = record.get(field)
            dist[value] = dist.get(value, 0) + 1
        return dist


class DatasetSampler:
    """Main dataset sampler."""
    
    def __init__(self):
        """Initialize dataset sampler."""
        self.random_sampler = RandomSampler()
        self.stratified_sampler = StratifiedSampler()
        self.reservoir_sampler = ReservoirSampler()
        self.systematic_sampler = SystematicSampler()
        self.weighted_sampler = WeightedSampler()
        self.validator = SampleValidator()
    
    def sample_dataset(
        self,
        dataset_path: Path,
        output_path: Path,
        config: SamplingConfig,
    ) -> SampleResult:
        """Sample dataset and save result."""
        start_time = datetime.now()
        
        # Read dataset
        records = self._read_dataset(dataset_path)
        
        # Select sampler
        if config.strategy == SamplingStrategy.RANDOM:
            sampler = RandomSampler(config.random_seed)
            samples = sampler.sample(records, config.sample_size)
        elif config.strategy == SamplingStrategy.STRATIFIED:
            if not config.stratify_field:
                raise ValueError("stratify_field required for stratified sampling")
            sampler = StratifiedSampler(config.random_seed)
            samples = sampler.sample(records, config.sample_size, config.stratify_field)
        elif config.strategy == SamplingStrategy.RESERVOIR:
            sampler = ReservoirSampler(config.random_seed)
            samples = sampler.sample(records, config.sample_size)
        elif config.strategy == SamplingStrategy.SYSTEMATIC:
            sampler = SystematicSampler()
            samples = sampler.sample(records, config.sample_size)
        elif config.strategy == SamplingStrategy.WEIGHTED:
            if not config.weights_field:
                raise ValueError("weights_field required for weighted sampling")
            sampler = WeightedSampler(config.random_seed)
            samples = sampler.sample(records, config.sample_size, config.weights_field)
        else:
            raise ValueError(f"Unknown strategy: {config.strategy}")
        
        # Calculate statistics
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        distribution = {}
        if config.stratify_field:
            distribution = self.validator._get_distribution(samples, config.stratify_field)
        
        statistics = SampleStatistics(
            total_records=len(records),
            sampled_records=len(samples),
            sample_ratio=len(samples) / max(len(records), 1),
            strategy_used=config.strategy,
            sampling_time_ms=elapsed_ms,
            distribution=distribution,
        )
        
        # Validate
        validation_passed = True
        if config.validation_level != SampleValidationLevel.NONE:
            validation_result = self.validator.validate_sample(records, samples, config)
            validation_passed = validation_result["valid"]
        
        # Save sample
        self._write_dataset(output_path, samples)
        
        # Create result
        sample_id = hashlib.sha256(str(output_path).encode()).hexdigest()[:16]
        
        result = SampleResult(
            sample_id=sample_id,
            config=config,
            statistics=statistics,
            sample_path=output_path,
            created_at=datetime.now(),
            validation_passed=validation_passed,
        )
        
        return result
    
    def _read_dataset(self, path: Path) -> List[Dict[str, Any]]:
        """Read JSONL dataset."""
        records = []
        if not path.exists():
            return records
        
        content = path.read_text()
        for line in content.strip().split("\n"):
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return records
    
    def _write_dataset(self, path: Path, records: List[Dict[str, Any]]) -> None:
        """Write JSONL dataset."""
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(record) for record in records]
        path.write_text("\n".join(lines))


class SampleComparator:
    """Compare samples and analyze differences."""
    
    def __init__(self):
        """Initialize comparator."""
        pass
    
    def compare_samples(
        self,
        sample1_path: Path,
        sample2_path: Path,
    ) -> Dict[str, Any]:
        """Compare two samples."""
        # Read samples
        sampler = DatasetSampler()
        records1 = sampler._read_dataset(sample1_path)
        records2 = sampler._read_dataset(sample2_path)
        
        # Calculate overlap
        ids1 = {id(r) for r in records1}
        ids2 = {id(r) for r in records2}
        overlap = len(ids1 & ids2)
        
        return {
            "sample1_size": len(records1),
            "sample2_size": len(records2),
            "overlap": overlap,
            "overlap_ratio": overlap / max(len(records1), 1),
            "unique_to_sample1": len(ids1 - ids2),
            "unique_to_sample2": len(ids2 - ids1),
        }
