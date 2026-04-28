"""Tests for dataset_sampling module."""
from pathlib import Path
from datetime import datetime
import pytest
import json
import tempfile

from peachtree.dataset_sampling import (
    DatasetSampler,
    RandomSampler,
    StratifiedSampler,
    ReservoirSampler,
    SystematicSampler,
    WeightedSampler,
    SampleValidator,
    SampleComparator,
    SamplingConfig,
    SampleResult,
    SampleStatistics,
    SamplingStrategy,
    SampleValidationLevel,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample dataset for testing."""
    dataset = tmp_path / "dataset.jsonl"
    records = [
        {"id": i, "category": f"cat_{i % 3}", "value": i * 10, "text": f"text_{i}"}
        for i in range(100)
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


def test_sampling_strategy_enum():
    """Test SamplingStrategy enum."""
    assert SamplingStrategy.RANDOM.value == "random"
    assert SamplingStrategy.STRATIFIED.value == "stratified"
    assert SamplingStrategy.RESERVOIR.value == "reservoir"
    assert SamplingStrategy.SYSTEMATIC.value == "systematic"
    assert SamplingStrategy.WEIGHTED.value == "weighted"


def test_sample_validation_level_enum():
    """Test SampleValidationLevel enum."""
    assert SampleValidationLevel.NONE.value == "none"
    assert SampleValidationLevel.BASIC.value == "basic"
    assert SampleValidationLevel.FULL.value == "full"


def test_sampling_config_creation():
    """Test SamplingConfig creation."""
    config = SamplingConfig(
        strategy=SamplingStrategy.RANDOM,
        sample_size=10,
        random_seed=42,
    )
    assert config.strategy == SamplingStrategy.RANDOM
    assert config.sample_size == 10
    assert config.random_seed == 42


def test_sampling_config_to_dict():
    """Test SamplingConfig to_dict."""
    config = SamplingConfig(
        strategy=SamplingStrategy.STRATIFIED,
        sample_size=20,
        stratify_field="category",
    )
    d = config.to_dict()
    assert d["strategy"] == "stratified"
    assert d["sample_size"] == 20
    assert d["stratify_field"] == "category"


def test_sample_statistics_creation():
    """Test SampleStatistics creation."""
    stats = SampleStatistics(
        total_records=100,
        sampled_records=10,
        sample_ratio=0.1,
        strategy_used=SamplingStrategy.RANDOM,
        sampling_time_ms=150.5,
    )
    assert stats.total_records == 100
    assert stats.sampled_records == 10
    assert stats.sample_ratio == 0.1


def test_sample_statistics_to_dict():
    """Test SampleStatistics to_dict."""
    stats = SampleStatistics(
        total_records=100,
        sampled_records=20,
        sample_ratio=0.2,
        strategy_used=SamplingStrategy.SYSTEMATIC,
        sampling_time_ms=100.0,
    )
    d = stats.to_dict()
    assert d["total_records"] == 100
    assert d["sampled_records"] == 20
    assert d["strategy_used"] == "systematic"


def test_random_sampler_creation():
    """Test RandomSampler creation."""
    sampler = RandomSampler(seed=42)
    assert sampler.seed == 42


def test_random_sampler_sample(sample_dataset, tmp_path):
    """Test RandomSampler sampling."""
    sampler = RandomSampler(seed=42)
    output = tmp_path / "sample.jsonl"
    
    result = sampler.sample(sample_dataset, output, sample_size=10)
    
    assert result == 10
    assert output.exists()
    
    lines = output.read_text().strip().split("\n")
    assert len(lines) == 10


def test_stratified_sampler_creation():
    """Test StratifiedSampler creation."""
    sampler = StratifiedSampler(stratify_field="category")
    assert sampler.stratify_field == "category"


def test_stratified_sampler_sample(sample_dataset, tmp_path):
    """Test StratifiedSampler sampling."""
    sampler = StratifiedSampler(stratify_field="category", seed=42)
    output = tmp_path / "sample.jsonl"
    
    result = sampler.sample(sample_dataset, output, sample_size=30)
    
    assert result == 30
    assert output.exists()


def test_reservoir_sampler_creation():
    """Test ReservoirSampler creation."""
    sampler = ReservoirSampler(seed=42)
    assert sampler.seed == 42


def test_reservoir_sampler_sample(sample_dataset, tmp_path):
    """Test ReservoirSampler sampling."""
    sampler = ReservoirSampler(seed=42)
    output = tmp_path / "sample.jsonl"
    
    result = sampler.sample(sample_dataset, output, sample_size=15)
    
    assert result == 15
    assert output.exists()


def test_systematic_sampler_creation():
    """Test SystematicSampler creation."""
    sampler = SystematicSampler()
    assert sampler is not None


def test_systematic_sampler_sample(sample_dataset, tmp_path):
    """Test SystematicSampler sampling."""
    sampler = SystematicSampler()
    output = tmp_path / "sample.jsonl"
    
    result = sampler.sample(sample_dataset, output, sample_size=20)
    
    assert result == 20
    assert output.exists()


def test_weighted_sampler_creation():
    """Test WeightedSampler creation."""
    sampler = WeightedSampler(weights_field="value", seed=42)
    assert sampler.weights_field == "value"


def test_weighted_sampler_sample(sample_dataset, tmp_path):
    """Test WeightedSampler sampling."""
    sampler = WeightedSampler(weights_field="value", seed=42)
    output = tmp_path / "sample.jsonl"
    
    result = sampler.sample(sample_dataset, output, sample_size=25)
    
    assert result == 25
    assert output.exists()


def test_sample_validator_creation():
    """Test SampleValidator creation."""
    validator = SampleValidator(min_size=10, max_size=1000)
    assert validator.min_size == 10
    assert validator.max_size == 1000


def test_sample_validator_validate_size(tmp_path):
    """Test SampleValidator size validation."""
    validator = SampleValidator(min_size=5, max_size=50)
    
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text("\n".join(json.dumps({"id": i}) for i in range(10)))
    
    result = validator.validate(dataset)
    assert result["size_valid"] is True


def test_dataset_sampler_creation(tmp_path):
    """Test DatasetSampler creation."""
    sampler = DatasetSampler(output_dir=tmp_path)
    assert sampler.output_dir == tmp_path


def test_dataset_sampler_random(sample_dataset, tmp_path):
    """Test DatasetSampler with random strategy."""
    sampler = DatasetSampler(output_dir=tmp_path)
    
    config = SamplingConfig(
        strategy=SamplingStrategy.RANDOM,
        sample_size=15,
        random_seed=42,
    )
    
    result = sampler.create_sample(sample_dataset, config)
    
    assert result.validation_passed
    assert result.statistics.sampled_records == 15


def test_dataset_sampler_stratified(sample_dataset, tmp_path):
    """Test DatasetSampler with stratified strategy."""
    sampler = DatasetSampler(output_dir=tmp_path)
    
    config = SamplingConfig(
        strategy=SamplingStrategy.STRATIFIED,
        sample_size=30,
        stratify_field="category",
        random_seed=42,
    )
    
    result = sampler.create_sample(sample_dataset, config)
    
    assert result.validation_passed
    assert result.statistics.sampled_records == 30


def test_dataset_sampler_reservoir(sample_dataset, tmp_path):
    """Test DatasetSampler with reservoir strategy."""
    sampler = DatasetSampler(output_dir=tmp_path)
    
    config = SamplingConfig(
        strategy=SamplingStrategy.RESERVOIR,
        sample_size=20,
        random_seed=42,
    )
    
    result = sampler.create_sample(sample_dataset, config)
    
    assert result.validation_passed
    assert result.statistics.sampled_records == 20


def test_dataset_sampler_systematic(sample_dataset, tmp_path):
    """Test DatasetSampler with systematic strategy."""
    sampler = DatasetSampler(output_dir=tmp_path)
    
    config = SamplingConfig(
        strategy=SamplingStrategy.SYSTEMATIC,
        sample_size=25,
    )
    
    result = sampler.create_sample(sample_dataset, config)
    
    assert result.validation_passed
    assert result.statistics.sampled_records == 25


def test_dataset_sampler_weighted(sample_dataset, tmp_path):
    """Test DatasetSampler with weighted strategy."""
    sampler = DatasetSampler(output_dir=tmp_path)
    
    config = SamplingConfig(
        strategy=SamplingStrategy.WEIGHTED,
        sample_size=15,
        weights_field="value",
        random_seed=42,
    )
    
    result = sampler.create_sample(sample_dataset, config)
    
    assert result.validation_passed
    assert result.statistics.sampled_records == 15


def test_sample_result_to_dict(tmp_path):
    """Test SampleResult to_dict."""
    config = SamplingConfig(
        strategy=SamplingStrategy.RANDOM,
        sample_size=10,
    )
    
    stats = SampleStatistics(
        total_records=100,
        sampled_records=10,
        sample_ratio=0.1,
        strategy_used=SamplingStrategy.RANDOM,
        sampling_time_ms=50.0,
    )
    
    result = SampleResult(
        sample_id="test123",
        config=config,
        statistics=stats,
        sample_path=tmp_path / "sample.jsonl",
        created_at=datetime.now(),
        validation_passed=True,
    )
    
    d = result.to_dict()
    assert d["sample_id"] == "test123"
    assert d["validation_passed"] is True


def test_sample_comparator_creation():
    """Test SampleComparator creation."""
    comparator = SampleComparator()
    assert comparator is not None


def test_sample_comparator_compare_samples(tmp_path):
    """Test SampleComparator comparing two samples."""
    comparator = SampleComparator()
    
    sample1 = tmp_path / "sample1.jsonl"
    sample2 = tmp_path / "sample2.jsonl"
    
    records1 = [{"id": i, "value": i * 10} for i in range(10)]
    records2 = [{"id": i, "value": i * 10} for i in range(5, 15)]
    
    sample1.write_text("\n".join(json.dumps(r) for r in records1))
    sample2.write_text("\n".join(json.dumps(r) for r in records2))
    
    comparison = comparator.compare_samples(sample1, sample2)
    
    assert "overlap_ratio" in comparison
    assert comparison["sample1_size"] == 10
    assert comparison["sample2_size"] == 10


def test_random_sampler_deterministic(sample_dataset, tmp_path):
    """Test RandomSampler produces deterministic results with seed."""
    sampler1 = RandomSampler(seed=42)
    sampler2 = RandomSampler(seed=42)
    
    output1 = tmp_path / "sample1.jsonl"
    output2 = tmp_path / "sample2.jsonl"
    
    sampler1.sample(sample_dataset, output1, sample_size=10)
    sampler2.sample(sample_dataset, output2, sample_size=10)
    
    assert output1.read_text() == output2.read_text()
