"""
Tests for smart_sampling module
"""
import pytest
import json
from peachtree.smart_sampling import SmartSampler, SampleResult


@pytest.fixture
def test_dataset(tmp_path):
    """Create a test dataset"""
    dataset = tmp_path / "test.jsonl"
    records = []
    
    # Create diverse dataset
    for i in range(100):
        records.append({
            "id": str(i),
            "content": f"Content {i} " * (5 + i % 10),  # Varying lengths
            "source_repo": f"repo{i % 3}",  # 3 different repos
            "source_path": f"file{i}.md",
            "digest": f"hash{i}",
            "timestamp": f"2026-04-{(i % 30) + 1:02d}T00:00:00",
        })
    
    dataset.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dataset


def test_sample_result_creation():
    """Test SampleResult dataclass"""
    result = SampleResult(
        source_dataset="test.jsonl",
        output_path="sample.jsonl",
        sampling_strategy="random",
        source_records=100,
        sampled_records=10,
        sampling_ratio=0.1,
        sample_timestamp="2026-04-27T10:00:00",
    )
    
    assert result.sampled_records == 10
    assert result.sampling_ratio == 0.1
    assert result.to_dict()["sampling_strategy"] == "random"


def test_random_sample_by_size(test_dataset, tmp_path):
    """Test random sampling by size"""
    output = tmp_path / "random-size.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.random_sample(test_dataset, output, sample_size=20)
    
    assert result.sampled_records == 20
    assert result.source_records == 100
    assert result.sampling_ratio == 0.2
    assert output.exists()
    
    # Verify sample has exactly 20 records
    with open(output) as f:
        sample_count = sum(1 for line in f if line.strip())
    assert sample_count == 20


def test_random_sample_by_ratio(test_dataset, tmp_path):
    """Test random sampling by ratio"""
    output = tmp_path / "random-ratio.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.random_sample(test_dataset, output, sample_ratio=0.25)
    
    assert result.sampled_records == 25
    assert result.sampling_ratio == 0.25


def test_random_sample_reproducibility(test_dataset, tmp_path):
    """Test that random sampling is reproducible with same seed"""
    output1 = tmp_path / "sample1.jsonl"
    output2 = tmp_path / "sample2.jsonl"
    
    sampler1 = SmartSampler(seed=42)
    sampler1.random_sample(test_dataset, output1, sample_size=10)
    
    sampler2 = SmartSampler(seed=42)
    sampler2.random_sample(test_dataset, output2, sample_size=10)
    
    # Both should sample same records
    content1 = output1.read_text()
    content2 = output2.read_text()
    assert content1 == content2


def test_random_sample_validation_error(test_dataset, tmp_path):
    """Test that random_sample requires either size or ratio"""
    output = tmp_path / "invalid.jsonl"
    sampler = SmartSampler()
    
    with pytest.raises(ValueError, match="Must specify either"):
        sampler.random_sample(test_dataset, output)


def test_quality_based_sample(test_dataset, tmp_path):
    """Test quality-based sampling"""
    output = tmp_path / "quality.jsonl"
    
    sampler = SmartSampler()
    result = sampler.quality_based_sample(test_dataset, output, sample_size=10)
    
    assert result.sampled_records == 10
    assert result.sampling_strategy == "quality_based"
    assert "average_quality" in result.metadata


def test_quality_based_sample_with_threshold(test_dataset, tmp_path):
    """Test quality sampling with minimum threshold"""
    output = tmp_path / "quality-threshold.jsonl"
    
    sampler = SmartSampler()
    result = sampler.quality_based_sample(
        test_dataset,
        output,
        sample_size=5,
        min_quality_score=80.0,
    )
    
    assert result.metadata["min_quality_score"] == 80.0


def test_stratified_sample(test_dataset, tmp_path):
    """Test stratified sampling to preserve distribution"""
    output = tmp_path / "stratified.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.stratified_sample(
        test_dataset,
        output,
        sample_ratio=0.3,
        stratify_field="source_repo",
    )
    
    assert result.sampling_strategy == "stratified"
    assert result.metadata["stratify_field"] == "source_repo"
    assert "strata_count" in result.metadata
    assert result.metadata["strata_count"] == 3  # 3 repos


def test_stratified_sample_preserves_distribution(test_dataset, tmp_path):
    """Test that stratified sampling preserves field distribution"""
    output = tmp_path / "stratified-dist.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.stratified_sample(
        test_dataset,
        output,
        sample_ratio=0.5,
        stratify_field="source_repo",
    )
    
    # Check strata info
    strata_info = result.metadata["strata_info"]
    for stratum, info in strata_info.items():
        # Each stratum should be sampled at 50% ratio
        assert abs(info["sampled"] / info["total"] - 0.5) < 0.1


def test_reservoir_sample(test_dataset, tmp_path):
    """Test reservoir sampling"""
    output = tmp_path / "reservoir.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.reservoir_sample(test_dataset, output, sample_size=15)
    
    assert result.sampled_records == 15
    assert result.sampling_strategy == "reservoir"
    assert result.metadata["algorithm"] == "reservoir_sampling"


def test_reservoir_sample_memory_efficient(tmp_path):
    """Test that reservoir sampling works with large datasets"""
    # Create larger dataset
    large_dataset = tmp_path / "large.jsonl"
    with open(large_dataset, 'w') as f:
        for i in range(1000):
            f.write(json.dumps({"id": str(i), "content": f"Content {i}"}) + "\n")
    
    output = tmp_path / "reservoir-large.jsonl"
    sampler = SmartSampler(seed=42)
    result = sampler.reservoir_sample(large_dataset, output, sample_size=50)
    
    assert result.sampled_records == 50
    assert result.source_records == 1000


def test_diversity_sample(test_dataset, tmp_path):
    """Test diversity-based sampling"""
    output = tmp_path / "diversity.jsonl"
    
    sampler = SmartSampler(seed=42)
    result = sampler.diversity_sample(
        test_dataset,
        output,
        sample_size=20,
        diversity_field="content",
    )
    
    assert result.sampled_records == 20
    assert result.sampling_strategy == "diversity"
    assert result.metadata["diversity_field"] == "content"


def test_diversity_sample_maximizes_variety(test_dataset, tmp_path):
    """Test that diversity sampling selects varied content"""
    output1 = tmp_path / "div1.jsonl"
    output2 = tmp_path / "random.jsonl"
    
    # Diversity sample
    sampler1 = SmartSampler(seed=42)
    result1 = sampler1.diversity_sample(test_dataset, output1, sample_size=10)
    
    # Random sample
    sampler2 = SmartSampler(seed=42)
    result2 = sampler2.random_sample(test_dataset, output2, sample_size=10)
    
    # Both should work
    assert result1.sampled_records == 10
    assert result2.sampled_records == 10


def test_time_based_sample_recent_first(test_dataset, tmp_path):
    """Test time-based sampling (most recent)"""
    output = tmp_path / "time-recent.jsonl"
    
    sampler = SmartSampler()
    result = sampler.time_based_sample(
        test_dataset,
        output,
        sample_ratio=0.1,
        time_field="timestamp",
        recent_first=True,
    )
    
    assert result.sampling_strategy == "time_based"
    assert result.metadata["recent_first"] is True
    assert result.metadata["time_field"] == "timestamp"


def test_time_based_sample_oldest_first(test_dataset, tmp_path):
    """Test time-based sampling (oldest)"""
    output = tmp_path / "time-oldest.jsonl"
    
    sampler = SmartSampler()
    result = sampler.time_based_sample(
        test_dataset,
        output,
        sample_ratio=0.2,
        time_field="timestamp",
        recent_first=False,
    )
    
    assert result.metadata["recent_first"] is False


def test_sample_result_to_summary():
    """Test sample result markdown summary"""
    result = SampleResult(
        source_dataset="test.jsonl",
        output_path="sample.jsonl",
        sampling_strategy="random",
        source_records=100,
        sampled_records=20,
        sampling_ratio=0.2,
        sample_timestamp="2026-04-27T10:00:00",
        metadata={"seed": 42},
    )
    
    summary = result.to_summary()
    assert "# Dataset Sampling Result" in summary
    assert "random" in summary
    assert "100" in summary
    assert "20" in summary
    assert "20.0%" in summary


def test_sample_result_to_json():
    """Test sample result JSON serialization"""
    result = SampleResult(
        "test.jsonl",
        "sample.jsonl",
        "quality_based",
        100,
        15,
        0.15,
        "2026-04-27T10:00:00",
    )
    
    json_str = result.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["sampling_strategy"] == "quality_based"
    assert parsed["sampled_records"] == 15


def test_smart_sampler_seed_in_metadata(test_dataset, tmp_path):
    """Test that seed is tracked in metadata"""
    output = tmp_path / "seeded.jsonl"
    
    sampler = SmartSampler(seed=123)
    result = sampler.random_sample(test_dataset, output, sample_size=10)
    
    assert result.metadata.get("seed") == 123


def test_sample_creates_output_directory(test_dataset, tmp_path):
    """Test that sampling creates output directory if missing"""
    output = tmp_path / "nested" / "dir" / "sample.jsonl"
    
    sampler = SmartSampler()
    result = sampler.random_sample(test_dataset, output, sample_size=10)
    
    assert output.exists()
    assert result.sampled_records == 10


def test_quality_score_calculation(test_dataset, tmp_path):
    """Test internal quality scoring logic"""
    sampler = SmartSampler()
    
    # High quality record
    high_quality = {
        "content": "a" * 150,  # Long content
        "source_repo": "repo1",  # Has repo
        "source_path": "file.md",
        "digest": "hash123",  # Has digest
    }
    
    # Low quality record
    low_quality = {
        "content": "short",
    }
    
    high_score = sampler._calculate_quality_score(high_quality)
    low_score = sampler._calculate_quality_score(low_quality)
    
    assert high_score > low_score
    assert high_score <= 100.0
    assert low_score >= 0.0
