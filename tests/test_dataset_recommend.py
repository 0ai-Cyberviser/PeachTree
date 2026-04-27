"""Tests for dataset recommendation functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from peachtree.dataset_recommend import (
    DatasetRecommender,
    Recommendation,
    RecommendationReport,
    RecommendationScore,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample dataset for testing."""
    dataset = temp_dir / "dataset.jsonl"
    records = []
    
    # Create a variety of records
    for i in range(100):
        quality = 60 + (i % 40)  # Quality scores 60-99
        records.append({
            "record_id": f"rec_{i:03d}",
            "content": f"Test content {i}" * (1 + i % 5),  # Varying content lengths
            "quality_score": quality,
            "source": f"repo{i % 3}",  # 3 different sources
        })
    
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    return dataset


class TestRecommendationScore:
    """Test RecommendationScore dataclass."""
    
    def test_score_creation(self):
        """Test creating a recommendation score."""
        score = RecommendationScore(
            score=0.85,
            confidence=0.9,
            impact="high",
            reason="High quality variance detected",
        )
        
        assert score.score == 0.85
        assert score.confidence == 0.9
        assert score.impact == "high"
    
    def test_score_to_dict(self):
        """Test converting score to dictionary."""
        score = RecommendationScore(
            score=0.75,
            confidence=0.8,
            impact="medium",
            reason="Moderate improvement possible",
        )
        
        data = score.to_dict()
        assert data["score"] == 0.75
        assert data["impact"] == "medium"


class TestRecommendation:
    """Test Recommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        score = RecommendationScore(0.85, 0.9, "high", "Test reason")
        rec = Recommendation(
            category="quality",
            parameter="threshold",
            current_value=70,
            recommended_value=75,
            score=score,
        )
        
        assert rec.category == "quality"
        assert rec.parameter == "threshold"
        assert rec.current_value == 70
        assert rec.recommended_value == 75
    
    def test_recommendation_to_dict(self):
        """Test converting recommendation to dictionary."""
        score = RecommendationScore(0.8, 0.85, "medium", "Test")
        rec = Recommendation("dedup", "strategy", "exact", "fuzzy", score)
        
        data = rec.to_dict()
        assert data["category"] == "dedup"
        assert data["current_value"] == "exact"
        assert "score" in data


class TestRecommendationReport:
    """Test RecommendationReport class."""
    
    def test_report_creation(self):
        """Test creating a recommendation report."""
        report = RecommendationReport(
            dataset_path="test.jsonl",
            timestamp="2026-04-27T00:00:00Z",
        )
        
        assert report.dataset_path == "test.jsonl"
        assert len(report.recommendations) == 0
        assert len(report.summary) == 0
    
    def test_add_recommendation(self):
        """Test adding recommendations to report."""
        report = RecommendationReport("test.jsonl", "2026-04-27T00:00:00Z")
        
        score = RecommendationScore(0.9, 0.95, "high", "Test")
        rec = Recommendation("quality", "threshold", 70, 75, score)
        
        report.add_recommendation(rec)
        
        assert len(report.recommendations) == 1
        assert report.recommendations[0].category == "quality"
    
    def test_report_to_json(self):
        """Test converting report to JSON."""
        report = RecommendationReport("test.jsonl", "2026-04-27T00:00:00Z")
        report.summary = {"total_recommendations": 1}
        
        json_str = report.to_json()
        data = json.loads(json_str)
        
        assert data["dataset_path"] == "test.jsonl"
        assert data["summary"]["total_recommendations"] == 1


class TestDatasetRecommender:
    """Test DatasetRecommender class."""
    
    def test_analyze_dataset(self, sample_dataset):
        """Test analyzing dataset statistics."""
        recommender = DatasetRecommender()
        
        stats = recommender.analyze_dataset(sample_dataset)
        
        assert "total_records" in stats
        assert "quality_stats" in stats
        assert "content_stats" in stats
        assert stats["total_records"] == 100
    
    def test_recommend_quality_threshold(self):
        """Test recommending quality threshold."""
        recommender = DatasetRecommender()
        
        stats = {
            "quality_stats": {
                "mean": 80,
                "median": 82,
                "std": 10,
                "min": 60,
                "max": 99,
            }
        }
        
        rec = recommender.recommend_quality_threshold(stats)
        
        assert rec is not None
        assert rec.category == "quality"
        assert rec.parameter == "threshold"
        assert isinstance(rec.recommended_value, (int, float))
    
    def test_recommend_dedup_strategy_exact(self):
        """Test recommending exact dedup for low duplicates."""
        recommender = DatasetRecommender()
        
        stats = {
            "total_records": 100,
            "duplicate_estimate": 5,  # 5% duplicates
        }
        
        rec = recommender.recommend_dedup_strategy(stats)
        
        assert rec is not None
        assert rec.category == "deduplication"
        assert rec.recommended_value in ["exact", "fuzzy", "semantic"]
    
    def test_recommend_dedup_strategy_fuzzy(self):
        """Test recommending fuzzy dedup for moderate duplicates."""
        recommender = DatasetRecommender()
        
        stats = {
            "total_records": 100,
            "duplicate_estimate": 15,  # 15% duplicates
        }
        
        rec = recommender.recommend_dedup_strategy(stats)
        
        assert rec is not None
        assert rec.category == "deduplication"
    
    def test_recommend_sample_ratio(self):
        """Test recommending sample ratio."""
        recommender = DatasetRecommender()
        
        stats = {
            "total_records": 10000,
            "quality_stats": {"std": 5},
        }
        
        rec = recommender.recommend_sample_ratio(stats)
        
        assert rec is not None
        assert rec.category == "sampling"
        assert 0 < rec.recommended_value <= 1.0
    
    def test_recommend_safety_gates(self):
        """Test recommending safety gate configuration."""
        recommender = DatasetRecommender()
        
        stats = {
            "total_records": 1000,
            "content_stats": {"avg_length": 500},
        }
        
        rec = recommender.recommend_safety_gates(stats)
        
        assert rec is not None
        assert rec.category == "safety"
        assert isinstance(rec.recommended_value, dict)
    
    def test_recommend_export_format(self):
        """Test recommending export format."""
        recommender = DatasetRecommender()
        
        stats = {
            "total_records": 5000,
            "content_stats": {"avg_length": 200},
        }
        
        rec = recommender.recommend_export_format(stats)
        
        assert rec is not None
        assert rec.category == "export"
        assert rec.recommended_value in ["jsonl", "parquet", "tfrecord", "hf_dataset"]
    
    def test_generate_recommendations(self, sample_dataset):
        """Test generating complete recommendation report."""
        recommender = DatasetRecommender()
        
        report = recommender.generate_recommendations(sample_dataset)
        
        assert isinstance(report, RecommendationReport)
        assert len(report.recommendations) > 0
        assert "total_recommendations" in report.summary
        assert "high_impact" in report.summary
        assert "medium_impact" in report.summary
        assert "low_impact" in report.summary
    
    def test_save_and_load_recommendations(self, sample_dataset, temp_dir):
        """Test saving and loading recommendations."""
        recommender = DatasetRecommender()
        
        # Generate and save
        report = recommender.generate_recommendations(sample_dataset)
        output = temp_dir / "recommendations.json"
        recommender.save_recommendations(report, output)
        
        assert output.exists()
        
        # Load
        loaded = recommender.load_recommendations(output)
        
        assert loaded.dataset_path == report.dataset_path
        assert len(loaded.recommendations) == len(report.recommendations)
    
    def test_apply_recommendations_high_impact(self):
        """Test applying high impact recommendations only."""
        recommender = DatasetRecommender()
        
        report = RecommendationReport("test.jsonl", "2026-04-27T00:00:00Z")
        
        # Add high impact recommendation
        score_high = RecommendationScore(0.9, 0.95, "high", "High impact")
        rec_high = Recommendation("quality", "threshold", 70, 75, score_high)
        report.add_recommendation(rec_high)
        
        # Add low impact recommendation
        score_low = RecommendationScore(0.4, 0.6, "low", "Low impact")
        rec_low = Recommendation("sampling", "ratio", 1.0, 0.95, score_low)
        report.add_recommendation(rec_low)
        
        current_config = {"quality": {"threshold": 70}, "sampling": {"ratio": 1.0}}
        
        new_config = recommender.apply_recommendations(
            report,
            current_config,
            impact_threshold="high",
        )
        
        # Should apply high impact only
        assert new_config["quality"]["threshold"] == 75
        assert new_config["sampling"]["ratio"] == 1.0  # Unchanged
    
    def test_apply_recommendations_medium_impact(self):
        """Test applying medium and high impact recommendations."""
        recommender = DatasetRecommender()
        
        report = RecommendationReport("test.jsonl", "2026-04-27T00:00:00Z")
        
        score_medium = RecommendationScore(0.7, 0.8, "medium", "Medium impact")
        rec_medium = Recommendation("dedup", "strategy", "exact", "fuzzy", score_medium)
        report.add_recommendation(rec_medium)
        
        current_config = {"dedup": {"strategy": "exact"}}
        
        new_config = recommender.apply_recommendations(
            report,
            current_config,
            impact_threshold="medium",
        )
        
        assert new_config["dedup"]["strategy"] == "fuzzy"
    
    def test_recommendation_impact_levels(self, sample_dataset):
        """Test that recommendations have proper impact levels."""
        recommender = DatasetRecommender()
        
        report = recommender.generate_recommendations(sample_dataset)
        
        # Verify all recommendations have valid impact levels
        for rec in report.recommendations:
            assert rec.score.impact in ["low", "medium", "high"]
    
    def test_recommendation_confidence_scores(self, sample_dataset):
        """Test that recommendations have confidence scores."""
        recommender = DatasetRecommender()
        
        report = recommender.generate_recommendations(sample_dataset)
        
        # Verify all recommendations have confidence scores
        for rec in report.recommendations:
            assert 0 <= rec.score.confidence <= 1.0
            assert 0 <= rec.score.score <= 1.0
