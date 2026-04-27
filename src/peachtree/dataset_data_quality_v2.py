"""
PeachTree Advanced Data Quality V2

Advanced data quality assessment with anomaly detection, statistical validation,
quality scoring, and automated quality improvement suggestions.

Features:
- Statistical anomaly detection
- Multi-dimensional quality scoring
- Data drift detection
- Outlier identification
- Quality trend analysis
- Automated quality improvement recommendations
- Schema validation and evolution
- Data profiling and statistics
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import json
import hashlib
from pathlib import Path


class AnomalyType(Enum):
    """Types of data anomalies"""
    STATISTICAL_OUTLIER = "statistical_outlier"
    SCHEMA_VIOLATION = "schema_violation"
    MISSING_VALUE = "missing_value"
    DUPLICATE = "duplicate"
    FORMAT_ERROR = "format_error"
    RANGE_VIOLATION = "range_violation"
    PATTERN_MISMATCH = "pattern_mismatch"
    DATA_DRIFT = "data_drift"


class QualityDimension(Enum):
    """Quality assessment dimensions"""
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"


@dataclass
class QualityMetric:
    """Individual quality metric"""
    dimension: QualityDimension
    score: float  # 0.0 to 100.0
    weight: float = 1.0
    issues_found: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def weighted_score(self) -> float:
        """Calculate weighted score"""
        return self.score * self.weight


@dataclass
class Anomaly:
    """Detected data anomaly"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    field: str
    record_id: Optional[str]
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "anomaly_id": self.anomaly_id,
            "type": self.anomaly_type.value,
            "severity": self.severity,
            "field": self.field,
            "record_id": self.record_id,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    dataset_id: str
    total_records: int
    metrics: List[QualityMetric] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted overall quality score"""
        if not self.metrics:
            return 0.0
        
        total_weight = sum(m.weight for m in self.metrics)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(m.weighted_score() for m in self.metrics)
        self.overall_score = weighted_sum / total_weight
        return self.overall_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset_id": self.dataset_id,
            "total_records": self.total_records,
            "overall_score": self.overall_score,
            "metrics": [
                {
                    "dimension": m.dimension.value,
                    "score": m.score,
                    "weight": m.weight,
                    "issues_found": m.issues_found,
                    "details": m.details
                }
                for m in self.metrics
            ],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }


class StatisticalAnalyzer:
    """Statistical analysis for anomaly detection"""
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics"""
        if not values:
            return {}
        
        n = len(values)
        mean = sum(values) / n
        
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = variance ** 0.5
        
        sorted_values = sorted(values)
        median = sorted_values[n // 2]
        
        return {
            "count": n,
            "mean": mean,
            "std_dev": std_dev,
            "median": median,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values)
        }
    
    @staticmethod
    def detect_outliers_iqr(values: List[float], multiplier: float = 1.5) -> List[int]:
        """Detect outliers using IQR method"""
        if len(values) < 4:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    @staticmethod
    def detect_outliers_zscore(values: List[float], threshold: float = 3.0) -> List[int]:
        """Detect outliers using Z-score method"""
        if len(values) < 2:
            return []
        
        stats = StatisticalAnalyzer.calculate_statistics(values)
        mean = stats["mean"]
        std_dev = stats["std_dev"]
        
        if std_dev == 0:
            return []
        
        outlier_indices = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold:
                outlier_indices.append(i)
        
        return outlier_indices


class DataQualityAnalyzer:
    """Advanced data quality analyzer"""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.records: List[Dict[str, Any]] = []
        self.schema: Dict[str, Set[type]] = defaultdict(set)
        self._load_dataset()
    
    def _load_dataset(self) -> None:
        """Load dataset and infer schema"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    self.records.append(record)
                    
                    # Infer schema
                    for key, value in record.items():
                        self.schema[key].add(type(value))
    
    def analyze(self) -> QualityReport:
        """Perform comprehensive quality analysis"""
        report = QualityReport(
            dataset_id=self.dataset_path.name,
            total_records=len(self.records)
        )
        
        # Calculate all quality metrics
        report.metrics.append(self._assess_completeness())
        report.metrics.append(self._assess_consistency())
        report.metrics.append(self._assess_uniqueness())
        report.metrics.append(self._assess_validity())
        
        # Detect anomalies
        report.anomalies.extend(self._detect_schema_violations())
        report.anomalies.extend(self._detect_duplicates())
        report.anomalies.extend(self._detect_statistical_outliers())
        
        # Calculate overall score
        report.calculate_overall_score()
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)
        
        return report
    
    def _assess_completeness(self) -> QualityMetric:
        """Assess data completeness"""
        if not self.records:
            return QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                score=0.0,
                issues_found=0
            )
        
        total_fields = len(self.schema)
        total_values = total_fields * len(self.records)
        missing_count = 0
        
        for record in self.records:
            for field in self.schema.keys():
                if field not in record or record[field] is None or record[field] == "":
                    missing_count += 1
        
        completeness_score = ((total_values - missing_count) / total_values * 100) if total_values > 0 else 0.0
        
        return QualityMetric(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            weight=1.5,
            issues_found=missing_count,
            details={
                "total_fields": total_fields,
                "total_values": total_values,
                "missing_values": missing_count,
                "completeness_rate": completeness_score / 100
            }
        )
    
    def _assess_consistency(self) -> QualityMetric:
        """Assess data type consistency"""
        inconsistencies = 0
        total_checks = 0
        
        for field, expected_types in self.schema.items():
            if len(expected_types) > 1:
                # Field has multiple types - inconsistent
                inconsistencies += len(self.records)
            
            total_checks += len(self.records)
        
        consistency_score = ((total_checks - inconsistencies) / total_checks * 100) if total_checks > 0 else 100.0
        
        return QualityMetric(
            dimension=QualityDimension.CONSISTENCY,
            score=consistency_score,
            weight=1.0,
            issues_found=inconsistencies,
            details={
                "fields_with_mixed_types": sum(1 for types in self.schema.values() if len(types) > 1),
                "total_type_checks": total_checks
            }
        )
    
    def _assess_uniqueness(self) -> QualityMetric:
        """Assess record uniqueness"""
        seen = set()
        duplicates = 0
        
        for record in self.records:
            record_hash = hashlib.md5(json.dumps(record, sort_keys=True).encode()).hexdigest()
            if record_hash in seen:
                duplicates += 1
            else:
                seen.add(record_hash)
        
        uniqueness_score = ((len(self.records) - duplicates) / len(self.records) * 100) if self.records else 100.0
        
        return QualityMetric(
            dimension=QualityDimension.UNIQUENESS,
            score=uniqueness_score,
            weight=1.0,
            issues_found=duplicates,
            details={
                "duplicate_records": duplicates,
                "unique_records": len(seen),
                "duplicate_rate": duplicates / len(self.records) if self.records else 0.0
            }
        )
    
    def _assess_validity(self) -> QualityMetric:
        """Assess data validity"""
        invalid_count = 0
        total_validations = 0
        
        for record in self.records:
            for field, value in record.items():
                total_validations += 1
                
                # Check for common validity issues
                if isinstance(value, str):
                    if len(value) == 0:
                        invalid_count += 1
                    elif len(value) > 10000:  # Suspiciously long string
                        invalid_count += 1
                elif isinstance(value, (int, float)):
                    if value < -1e10 or value > 1e10:  # Suspicious range
                        invalid_count += 1
        
        validity_score = ((total_validations - invalid_count) / total_validations * 100) if total_validations > 0 else 100.0
        
        return QualityMetric(
            dimension=QualityDimension.VALIDITY,
            score=validity_score,
            weight=1.2,
            issues_found=invalid_count,
            details={
                "invalid_values": invalid_count,
                "total_validations": total_validations
            }
        )
    
    def _detect_schema_violations(self) -> List[Anomaly]:
        """Detect schema violations"""
        anomalies = []
        expected_fields = set(self.schema.keys())
        
        for idx, record in enumerate(self.records):
            record_fields = set(record.keys())
            
            # Missing fields
            missing = expected_fields - record_fields
            if missing:
                anomalies.append(Anomaly(
                    anomaly_id=f"schema_missing_{idx}",
                    anomaly_type=AnomalyType.SCHEMA_VIOLATION,
                    severity="medium",
                    field=", ".join(missing),
                    record_id=str(idx),
                    description=f"Missing fields: {missing}",
                    metadata={"missing_fields": list(missing)}
                ))
            
            # Extra fields
            extra = record_fields - expected_fields
            if extra:
                anomalies.append(Anomaly(
                    anomaly_id=f"schema_extra_{idx}",
                    anomaly_type=AnomalyType.SCHEMA_VIOLATION,
                    severity="low",
                    field=", ".join(extra),
                    record_id=str(idx),
                    description=f"Unexpected fields: {extra}",
                    metadata={"extra_fields": list(extra)}
                ))
        
        return anomalies
    
    def _detect_duplicates(self) -> List[Anomaly]:
        """Detect duplicate records"""
        anomalies = []
        seen = {}
        
        for idx, record in enumerate(self.records):
            record_hash = hashlib.md5(json.dumps(record, sort_keys=True).encode()).hexdigest()
            
            if record_hash in seen:
                anomalies.append(Anomaly(
                    anomaly_id=f"duplicate_{idx}",
                    anomaly_type=AnomalyType.DUPLICATE,
                    severity="medium",
                    field="*",
                    record_id=str(idx),
                    description=f"Duplicate of record {seen[record_hash]}",
                    metadata={"original_record_id": seen[record_hash]}
                ))
            else:
                seen[record_hash] = idx
        
        return anomalies
    
    def _detect_statistical_outliers(self) -> List[Anomaly]:
        """Detect statistical outliers in numeric fields"""
        anomalies = []
        
        for field in self.schema.keys():
            # Extract numeric values
            values = []
            indices = []
            
            for idx, record in enumerate(self.records):
                if field in record and isinstance(record[field], (int, float)):
                    values.append(float(record[field]))
                    indices.append(idx)
            
            if len(values) < 10:  # Need sufficient data
                continue
            
            # Detect outliers using IQR method
            outlier_positions = StatisticalAnalyzer.detect_outliers_iqr(values)
            
            for pos in outlier_positions:
                idx = indices[pos]
                value = values[pos]
                
                anomalies.append(Anomaly(
                    anomaly_id=f"outlier_{field}_{idx}",
                    anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                    severity="low",
                    field=field,
                    record_id=str(idx),
                    description=f"Statistical outlier: {value}",
                    metadata={"value": value, "field": field}
                ))
        
        return anomalies
    
    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Check completeness
        completeness_metric = next((m for m in report.metrics if m.dimension == QualityDimension.COMPLETENESS), None)
        if completeness_metric and completeness_metric.score < 95:
            recommendations.append(
                f"Completeness is {completeness_metric.score:.1f}%. "
                f"Fill in {completeness_metric.issues_found} missing values to improve quality."
            )
        
        # Check uniqueness
        uniqueness_metric = next((m for m in report.metrics if m.dimension == QualityDimension.UNIQUENESS), None)
        if uniqueness_metric and uniqueness_metric.score < 100:
            recommendations.append(
                f"Remove {uniqueness_metric.issues_found} duplicate records to achieve 100% uniqueness."
            )
        
        # Check consistency
        consistency_metric = next((m for m in report.metrics if m.dimension == QualityDimension.CONSISTENCY), None)
        if consistency_metric and consistency_metric.score < 95:
            recommendations.append(
                "Standardize data types across all fields to improve consistency."
            )
        
        # Check anomalies
        critical_anomalies = [a for a in report.anomalies if a.severity == "critical"]
        if critical_anomalies:
            recommendations.append(
                f"Address {len(critical_anomalies)} critical anomalies immediately."
            )
        
        if report.overall_score < 80:
            recommendations.append(
                "Overall quality score is below 80%. Prioritize data cleaning and validation."
            )
        
        return recommendations


# Export public API
__all__ = [
    'AnomalyType',
    'QualityDimension',
    'QualityMetric',
    'Anomaly',
    'QualityReport',
    'StatisticalAnalyzer',
    'DataQualityAnalyzer'
]
