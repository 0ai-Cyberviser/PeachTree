"""Dataset recommendation engine for optimal configuration.

This module provides recommendations for:
- Quality thresholds and scoring parameters
- Deduplication strategies and settings
- Sampling ratios and techniques
- Safety gate configurations
- Policy pack selection
- Export format optimization
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationScore:
    """Score for a recommendation."""
    
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class Recommendation:
    """A single configuration recommendation."""
    
    category: str
    parameter: str
    recommended_value: Any
    current_value: Optional[Any]
    score: RecommendationScore
    impact: str  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "parameter": self.parameter,
            "recommended_value": self.recommended_value,
            "current_value": self.current_value,
            "score": self.score.to_dict(),
            "impact": self.impact,
        }


@dataclass
class RecommendationReport:
    """Full recommendation report."""
    
    dataset_path: str
    recommendations: List[Recommendation] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    
    def add_recommendation(self, rec: Recommendation) -> None:
        """Add a recommendation to the report."""
        self.recommendations.append(rec)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "summary": self.summary,
            "timestamp": self.timestamp,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DatasetRecommender:
    """Generate recommendations for dataset configuration."""
    
    def __init__(self) -> None:
        """Initialize the recommender."""
        self.default_thresholds = {
            "quality_score_min": 70.0,
            "quality_score_target": 85.0,
            "dedup_similarity": 0.85,
            "safety_gate_strictness": "medium",
            "sample_ratio": 1.0,
        }
    
    def analyze_dataset(self, dataset_path: Path) -> Dict[str, Any]:
        """Analyze dataset characteristics.
        
        Args:
            dataset_path: Path to dataset file
        
        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            "total_records": 0,
            "avg_content_length": 0,
            "quality_distribution": {},
            "source_diversity": 0,
            "has_duplicates": False,
        }
        
        try:
            total_length = 0
            quality_scores = []
            sources = set()
            
            with open(dataset_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    record = json.loads(line)
                    stats["total_records"] += 1
                    
                    # Analyze content length
                    content = record.get("content", "")
                    total_length += len(content)
                    
                    # Collect quality scores
                    quality = record.get("quality_score", 0)
                    quality_scores.append(quality)
                    
                    # Track source diversity
                    source = record.get("source_repo", "unknown")
                    sources.add(source)
            
            if stats["total_records"] > 0:
                stats["avg_content_length"] = total_length // stats["total_records"]
                
                # Quality distribution
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    stats["quality_distribution"] = {
                        "avg": avg_quality,
                        "min": min(quality_scores),
                        "max": max(quality_scores),
                    }
                
                stats["source_diversity"] = len(sources)
        
        except Exception:
            pass
        
        return stats
    
    def recommend_quality_threshold(
        self,
        stats: Dict[str, Any],
    ) -> Recommendation:
        """Recommend optimal quality score threshold.
        
        Args:
            stats: Dataset statistics
        
        Returns:
            Quality threshold recommendation
        """
        avg_quality = stats.get("quality_distribution", {}).get("avg", 70.0)
        
        # Recommend threshold slightly below average to retain good data
        recommended = max(60.0, avg_quality - 10.0)
        
        score = RecommendationScore(
            score=0.85,
            confidence=0.9,
            reason=f"Based on average quality score of {avg_quality:.1f}",
        )
        
        return Recommendation(
            category="quality",
            parameter="min_quality_score",
            recommended_value=recommended,
            current_value=self.default_thresholds["quality_score_min"],
            score=score,
            impact="high",
        )
    
    def recommend_dedup_strategy(
        self,
        stats: Dict[str, Any],
    ) -> Recommendation:
        """Recommend deduplication strategy.
        
        Args:
            stats: Dataset statistics
        
        Returns:
            Deduplication recommendation
        """
        total = stats.get("total_records", 0)
        
        if total < 1000:
            strategy = "exact"
            reason = "Small dataset - use exact deduplication"
        elif total < 10000:
            strategy = "fuzzy"
            reason = "Medium dataset - use fuzzy deduplication"
        else:
            strategy = "minhash"
            reason = "Large dataset - use MinHash for efficiency"
        
        score = RecommendationScore(
            score=0.9,
            confidence=0.85,
            reason=reason,
        )
        
        return Recommendation(
            category="deduplication",
            parameter="strategy",
            recommended_value=strategy,
            current_value="exact",
            score=score,
            impact="medium",
        )
    
    def recommend_sample_ratio(
        self,
        stats: Dict[str, Any],
    ) -> Recommendation:
        """Recommend sampling ratio.
        
        Args:
            stats: Dataset statistics
        
        Returns:
            Sampling recommendation
        """
        total = stats.get("total_records", 0)
        
        if total < 5000:
            ratio = 1.0
            reason = "Small dataset - use all records"
            impact = "low"
        elif total < 50000:
            ratio = 0.8
            reason = "Medium dataset - sample 80% for training"
            impact = "medium"
        else:
            ratio = 0.6
            reason = "Large dataset - sample 60% to reduce training time"
            impact = "high"
        
        score = RecommendationScore(
            score=0.8,
            confidence=0.75,
            reason=reason,
        )
        
        return Recommendation(
            category="sampling",
            parameter="sample_ratio",
            recommended_value=ratio,
            current_value=self.default_thresholds["sample_ratio"],
            score=score,
            impact=impact,
        )
    
    def recommend_safety_gates(
        self,
        stats: Dict[str, Any],
    ) -> Recommendation:
        """Recommend safety gate configuration.
        
        Args:
            stats: Dataset statistics
        
        Returns:
            Safety gate recommendation
        """
        source_diversity = stats.get("source_diversity", 0)
        
        if source_diversity <= 1:
            strictness = "low"
            reason = "Single source - use relaxed safety gates"
        elif source_diversity <= 5:
            strictness = "medium"
            reason = "Few sources - use standard safety gates"
        else:
            strictness = "high"
            reason = "Many sources - use strict safety gates"
        
        score = RecommendationScore(
            score=0.85,
            confidence=0.8,
            reason=reason,
        )
        
        return Recommendation(
            category="safety",
            parameter="gate_strictness",
            recommended_value=strictness,
            current_value=self.default_thresholds["safety_gate_strictness"],
            score=score,
            impact="high",
        )
    
    def recommend_export_format(
        self,
        stats: Dict[str, Any],
    ) -> Recommendation:
        """Recommend export format.
        
        Args:
            stats: Dataset statistics
        
        Returns:
            Export format recommendation
        """
        avg_length = stats.get("avg_content_length", 0)
        
        if avg_length < 500:
            format_name = "sharegpt"
            reason = "Short content - ShareGPT format suitable"
        elif avg_length < 2000:
            format_name = "chatml"
            reason = "Medium content - ChatML format recommended"
        else:
            format_name = "completion"
            reason = "Long content - completion format preferred"
        
        score = RecommendationScore(
            score=0.75,
            confidence=0.7,
            reason=reason,
        )
        
        return Recommendation(
            category="export",
            parameter="format",
            recommended_value=format_name,
            current_value="jsonl",
            score=score,
            impact="medium",
        )
    
    def generate_recommendations(
        self,
        dataset_path: Path,
    ) -> RecommendationReport:
        """Generate full recommendation report.
        
        Args:
            dataset_path: Path to dataset
        
        Returns:
            Complete recommendation report
        """
        from datetime import datetime
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Analyze dataset
        stats = self.analyze_dataset(dataset_path)
        
        # Create report
        report = RecommendationReport(
            dataset_path=str(dataset_path),
            timestamp=timestamp,
        )
        
        # Generate recommendations
        report.add_recommendation(self.recommend_quality_threshold(stats))
        report.add_recommendation(self.recommend_dedup_strategy(stats))
        report.add_recommendation(self.recommend_sample_ratio(stats))
        report.add_recommendation(self.recommend_safety_gates(stats))
        report.add_recommendation(self.recommend_export_format(stats))
        
        # Add summary
        report.summary = {
            "total_recommendations": len(report.recommendations),
            "high_impact": sum(1 for r in report.recommendations if r.impact == "high"),
            "medium_impact": sum(1 for r in report.recommendations if r.impact == "medium"),
            "low_impact": sum(1 for r in report.recommendations if r.impact == "low"),
            "avg_confidence": sum(r.score.confidence for r in report.recommendations) / len(report.recommendations) if report.recommendations else 0,
        }
        
        return report
    
    def save_recommendations(
        self,
        report: RecommendationReport,
        output_path: Path,
    ) -> None:
        """Save recommendations to file.
        
        Args:
            report: Recommendation report
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report.to_json())
    
    def load_recommendations(
        self,
        report_path: Path,
    ) -> RecommendationReport:
        """Load recommendations from file.
        
        Args:
            report_path: Report file path
        
        Returns:
            RecommendationReport
        """
        with open(report_path) as f:
            data = json.load(f)
        
        report = RecommendationReport(
            dataset_path=data["dataset_path"],
            timestamp=data.get("timestamp", ""),
        )
        
        report.summary = data.get("summary", {})
        
        for rec_data in data.get("recommendations", []):
            score = RecommendationScore(
                score=rec_data["score"]["score"],
                confidence=rec_data["score"]["confidence"],
                reason=rec_data["score"]["reason"],
            )
            
            rec = Recommendation(
                category=rec_data["category"],
                parameter=rec_data["parameter"],
                recommended_value=rec_data["recommended_value"],
                current_value=rec_data.get("current_value"),
                score=score,
                impact=rec_data["impact"],
            )
            
            report.add_recommendation(rec)
        
        return report
    
    def apply_recommendations(
        self,
        report: RecommendationReport,
        config: Dict[str, Any],
        impact_threshold: str = "medium",
    ) -> Dict[str, Any]:
        """Apply recommendations to configuration.
        
        Args:
            report: Recommendation report
            config: Current configuration
            impact_threshold: Minimum impact level to apply (low/medium/high)
        
        Returns:
            Updated configuration
        """
        impact_levels = {"low": 1, "medium": 2, "high": 3}
        threshold = impact_levels.get(impact_threshold, 2)
        
        new_config = config.copy()
        
        for rec in report.recommendations:
            rec_impact = impact_levels.get(rec.impact, 1)
            
            if rec_impact >= threshold:
                # Apply recommendation
                if rec.category == "quality":
                    new_config["min_quality_score"] = rec.recommended_value
                elif rec.category == "deduplication":
                    new_config["dedup_strategy"] = rec.recommended_value
                elif rec.category == "sampling":
                    new_config["sample_ratio"] = rec.recommended_value
                elif rec.category == "safety":
                    new_config["safety_strictness"] = rec.recommended_value
                elif rec.category == "export":
                    new_config["export_format"] = rec.recommended_value
        
        return new_config
