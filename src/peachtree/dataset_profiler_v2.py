"""Enhanced dataset profiling with advanced statistics.

Provides comprehensive dataset profiling including distributions,
correlations, anomalies, and quality metrics.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import statistics


class ProfileDepth(Enum):
    """Profiling depth levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class DataType(Enum):
    """Data type classification."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    MIXED = "mixed"


@dataclass
class FieldProfile:
    """Profile for a single field."""
    field_name: str
    data_type: DataType
    total_count: int
    null_count: int
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field_name": self.field_name,
            "data_type": self.data_type.value,
            "total_count": self.total_count,
            "null_count": self.null_count,
            "unique_count": self.unique_count,
            "null_percentage": (self.null_count / max(self.total_count, 1)) * 100,
            "unique_percentage": (self.unique_count / max(self.total_count, 1)) * 100,
            "sample_values": self.sample_values[:10],
            "statistics": self.statistics,
        }


@dataclass
class DatasetProfile:
    """Complete dataset profile."""
    profile_id: str
    dataset_path: Path
    total_records: int
    total_fields: int
    field_profiles: List[FieldProfile]
    created_at: datetime
    profile_depth: ProfileDepth
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "dataset_path": str(self.dataset_path),
            "total_records": self.total_records,
            "total_fields": self.total_fields,
            "field_profiles": [fp.to_dict() for fp in self.field_profiles],
            "created_at": self.created_at.isoformat(),
            "profile_depth": self.profile_depth.value,
            "quality_score": self.quality_score,
        }


class EnhancedDatasetProfiler:
    """Enhanced dataset profiler with advanced analytics."""
    
    def __init__(self, depth: ProfileDepth = ProfileDepth.STANDARD):
        """Initialize profiler."""
        self.depth = depth
    
    def profile_dataset(self, dataset_path: Path) -> DatasetProfile:
        """Generate comprehensive dataset profile."""
        import hashlib
        
        # Load dataset
        records = []
        with open(dataset_path) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        if not records:
            profile_id = hashlib.sha256(
                f"{dataset_path}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            return DatasetProfile(
                profile_id=profile_id,
                dataset_path=dataset_path,
                total_records=0,
                total_fields=0,
                field_profiles=[],
                created_at=datetime.now(),
                profile_depth=self.depth,
            )
        
        # Get all fields
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        # Profile each field
        field_profiles = []
        for field_name in sorted(all_fields):
            field_profile = self._profile_field(records, field_name)
            field_profiles.append(field_profile)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(field_profiles, len(records))
        
        profile_id = hashlib.sha256(
            f"{dataset_path}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return DatasetProfile(
            profile_id=profile_id,
            dataset_path=dataset_path,
            total_records=len(records),
            total_fields=len(all_fields),
            field_profiles=field_profiles,
            created_at=datetime.now(),
            profile_depth=self.depth,
            quality_score=quality_score,
        )
    
    def _profile_field(
        self,
        records: List[Dict[str, Any]],
        field_name: str,
    ) -> FieldProfile:
        """Profile a single field."""
        values = []
        null_count = 0
        
        for record in records:
            value = record.get(field_name)
            if value is None:
                null_count += 1
            else:
                values.append(value)
        
        # Determine data type
        data_type = self._infer_data_type(values)
        
        # Get unique values
        unique_values = set()
        for v in values:
            if isinstance(v, (list, dict)):
                unique_values.add(str(v))
            else:
                unique_values.add(v)
        
        # Calculate statistics
        stats = {}
        if data_type == DataType.NUMERIC:
            stats = self._calculate_numeric_stats(values)
        elif data_type == DataType.TEXT:
            stats = self._calculate_text_stats(values)
        elif data_type == DataType.CATEGORICAL:
            stats = self._calculate_categorical_stats(values)
        
        return FieldProfile(
            field_name=field_name,
            data_type=data_type,
            total_count=len(records),
            null_count=null_count,
            unique_count=len(unique_values),
            sample_values=list(unique_values)[:10],
            statistics=stats,
        )
    
    def _infer_data_type(self, values: List[Any]) -> DataType:
        """Infer field data type."""
        if not values:
            return DataType.MIXED
        
        # Sample values to determine type
        sample = values[:100]
        
        numeric_count = sum(1 for v in sample if isinstance(v, (int, float)))
        boolean_count = sum(1 for v in sample if isinstance(v, bool))
        string_count = sum(1 for v in sample if isinstance(v, str))
        
        if numeric_count == len(sample):
            return DataType.NUMERIC
        elif boolean_count == len(sample):
            return DataType.BOOLEAN
        elif string_count == len(sample):
            # Distinguish categorical from text
            unique_ratio = len(set(sample)) / len(sample)
            if unique_ratio < 0.5:
                return DataType.CATEGORICAL
            else:
                return DataType.TEXT
        
        return DataType.MIXED
    
    def _calculate_numeric_stats(self, values: List[Any]) -> Dict[str, Any]:
        """Calculate statistics for numeric fields."""
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        
        if not numeric_values:
            return {}
        
        stats = {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
        }
        
        if len(numeric_values) > 1:
            stats["median"] = statistics.median(numeric_values)
            stats["stdev"] = statistics.stdev(numeric_values)
        
        if self.depth == ProfileDepth.COMPREHENSIVE:
            # Additional statistics
            stats["q1"] = statistics.quantiles(numeric_values, n=4)[0] if len(numeric_values) >= 4 else None
            stats["q3"] = statistics.quantiles(numeric_values, n=4)[2] if len(numeric_values) >= 4 else None
        
        return stats
    
    def _calculate_text_stats(self, values: List[Any]) -> Dict[str, Any]:
        """Calculate statistics for text fields."""
        text_values = [str(v) for v in values if v is not None]
        
        if not text_values:
            return {}
        
        lengths = [len(t) for t in text_values]
        
        stats = {
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": statistics.mean(lengths),
        }
        
        if self.depth in [ProfileDepth.STANDARD, ProfileDepth.COMPREHENSIVE]:
            # Word count statistics
            word_counts = [len(t.split()) for t in text_values]
            stats["avg_word_count"] = statistics.mean(word_counts)
        
        return stats
    
    def _calculate_categorical_stats(self, values: List[Any]) -> Dict[str, Any]:
        """Calculate statistics for categorical fields."""
        # Count frequencies
        frequencies: Dict[Any, int] = {}
        for v in values:
            frequencies[v] = frequencies.get(v, 0) + 1
        
        # Get top categories
        sorted_freq = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        
        stats = {
            "num_categories": len(frequencies),
            "top_categories": [
                {"value": k, "count": v}
                for k, v in sorted_freq[:5]
            ],
        }
        
        return stats
    
    def _calculate_quality_score(
        self,
        field_profiles: List[FieldProfile],
        total_records: int,
    ) -> float:
        """Calculate overall dataset quality score."""
        if not field_profiles:
            return 0.0
        
        score = 100.0
        
        # Penalize for null values
        total_nulls = sum(fp.null_count for fp in field_profiles)
        total_cells = total_records * len(field_profiles)
        null_ratio = total_nulls / max(total_cells, 1)
        score -= null_ratio * 50
        
        # Penalize for low uniqueness in text fields
        text_fields = [fp for fp in field_profiles if fp.data_type == DataType.TEXT]
        for fp in text_fields:
            unique_ratio = fp.unique_count / max(fp.total_count, 1)
            if unique_ratio < 0.1:
                score -= 5
        
        return max(0.0, min(100.0, score))


class DistributionAnalyzer:
    """Analyze value distributions."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def analyze_distribution(
        self,
        values: List[Any],
        num_bins: int = 10,
    ) -> Dict[str, Any]:
        """Analyze value distribution."""
        if not values:
            return {}
        
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        
        if not numeric_values:
            return {}
        
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        
        # Create histogram bins
        if min_val == max_val:
            bins = [min_val]
            counts = [len(numeric_values)]
        else:
            bin_size = (max_val - min_val) / num_bins
            bins = [min_val + i * bin_size for i in range(num_bins + 1)]
            counts = [0] * num_bins
            
            for value in numeric_values:
                bin_idx = min(int((value - min_val) / bin_size), num_bins - 1)
                counts[bin_idx] += 1
        
        return {
            "bins": bins,
            "counts": counts,
            "min": min_val,
            "max": max_val,
        }


class CorrelationAnalyzer:
    """Analyze correlations between fields."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def calculate_correlation(
        self,
        values1: List[float],
        values2: List[float],
    ) -> float:
        """Calculate correlation coefficient."""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        # Simple Pearson correlation
        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        
        numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
        denominator1 = sum((v1 - mean1) ** 2 for v1 in values1)
        denominator2 = sum((v2 - mean2) ** 2 for v2 in values2)
        
        if denominator1 == 0 or denominator2 == 0:
            return 0.0
        
        return numerator / (denominator1 * denominator2) ** 0.5


class ProfileComparator:
    """Compare dataset profiles."""
    
    def __init__(self):
        """Initialize comparator."""
        pass
    
    def compare_profiles(
        self,
        profile1: DatasetProfile,
        profile2: DatasetProfile,
    ) -> Dict[str, Any]:
        """Compare two dataset profiles."""
        comparison = {
            "records_diff": profile2.total_records - profile1.total_records,
            "fields_diff": profile2.total_fields - profile1.total_fields,
            "quality_diff": profile2.quality_score - profile1.quality_score,
            "new_fields": [],
            "removed_fields": [],
            "modified_fields": [],
        }
        
        fields1 = {fp.field_name for fp in profile1.field_profiles}
        fields2 = {fp.field_name for fp in profile2.field_profiles}
        
        comparison["new_fields"] = list(fields2 - fields1)
        comparison["removed_fields"] = list(fields1 - fields2)
        comparison["modified_fields"] = list(fields1 & fields2)
        
        return comparison
