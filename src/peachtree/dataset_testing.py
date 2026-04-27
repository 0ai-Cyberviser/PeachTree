"""Automated testing framework for dataset pipelines.

This module provides comprehensive testing capabilities including:
- Synthetic test dataset generation
- Schema and structure validation
- Regression testing for pipelines
- Property-based testing
- Test fixtures and mocks
- Test result reporting
"""

import json
import random
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class TestCase:
    """A single test case definition."""
    
    test_id: str
    test_name: str
    test_type: str  # schema, regression, property, integration
    expected_result: Any
    actual_result: Optional[Any] = None
    passed: bool = False
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "passed": self.passed,
            "error_message": self.error_message,
        }


@dataclass
class TestSuite:
    """Collection of test cases."""
    
    suite_id: str
    suite_name: str
    test_cases: List[TestCase] = field(default_factory=list)
    
    def add_test(self, test_case: TestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
    
    def total_tests(self) -> int:
        """Get total number of tests."""
        return len(self.test_cases)
    
    def passed_tests(self) -> int:
        """Get number of passed tests."""
        return sum(1 for tc in self.test_cases if tc.passed)
    
    def failed_tests(self) -> int:
        """Get number of failed tests."""
        return sum(1 for tc in self.test_cases if not tc.passed)
    
    def pass_rate(self) -> float:
        """Get pass rate percentage."""
        if not self.test_cases:
            return 0.0
        return (self.passed_tests() / len(self.test_cases)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "total_tests": self.total_tests(),
            "passed_tests": self.passed_tests(),
            "failed_tests": self.failed_tests(),
            "pass_rate": self.pass_rate(),
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }


@dataclass
class TestResult:
    """Complete test execution result."""
    
    suite_id: str
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    test_suites: List[TestSuite] = field(default_factory=list)
    
    def to_json(self) -> str:
        return json.dumps({
            "suite_id": self.suite_id,
            "timestamp": self.timestamp,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": self.pass_rate,
            "test_suites": [ts.to_dict() for ts in self.test_suites],
        }, indent=2)


class SyntheticDataGenerator:
    """Generate synthetic test datasets."""
    
    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize the generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def generate_dataset(
        self,
        num_records: int,
        schema: Optional[Dict[str, str]] = None,
        output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a synthetic dataset.
        
        Args:
            num_records: Number of records to generate
            schema: Field schema (field_name -> field_type)
            output_path: Optional output file path
        
        Returns:
            List of generated records
        """
        if schema is None:
            schema = {
                "id": "id",
                "content": "text",
                "quality_score": "float",
                "metadata": "object",
            }
        
        records = []
        for i in range(num_records):
            record = {}
            for field, field_type in schema.items():
                record[field] = self._generate_field_value(field, field_type, i)
            records.append(record)
        
        if output_path:
            self._save_records(records, output_path)
        
        return records
    
    def _generate_field_value(self, field_name: str, field_type: str, index: int) -> Any:
        """Generate a field value based on type."""
        if field_type == "id":
            return f"record_{index:06d}"
        elif field_type == "text":
            return self._generate_text()
        elif field_type == "float":
            return round(random.uniform(0.0, 100.0), 2)
        elif field_type == "int":
            return random.randint(0, 1000)
        elif field_type == "bool":
            return random.choice([True, False])
        elif field_type == "object":
            return {"source": "synthetic", "index": index}
        elif field_type == "array":
            return [self._generate_text() for _ in range(random.randint(1, 5))]
        else:
            return f"{field_name}_{index}"
    
    def _generate_text(self, min_words: int = 10, max_words: int = 100) -> str:
        """Generate random text."""
        word_count = random.randint(min_words, max_words)
        words = []
        
        for _ in range(word_count):
            word_len = random.randint(3, 10)
            word = ''.join(random.choices(string.ascii_lowercase, k=word_len))
            words.append(word)
        
        return ' '.join(words)
    
    def _save_records(self, records: List[Dict[str, Any]], output_path: Path) -> None:
        """Save records to JSONL file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
    
    def generate_edge_cases(self) -> List[Dict[str, Any]]:
        """Generate edge case test records."""
        return [
            {"id": "empty_content", "content": "", "quality_score": 0.0},
            {"id": "very_long_content", "content": "x" * 100000, "quality_score": 50.0},
            {"id": "special_chars", "content": "!@#$%^&*()[]{}|\\;:'\"<>?,./", "quality_score": 75.0},
            {"id": "unicode", "content": "Hello 世界 мир 🌍", "quality_score": 85.0},
            {"id": "missing_fields", "quality_score": 60.0},
            {"id": "null_values", "content": None, "quality_score": None},
        ]


class SchemaValidator:
    """Validate dataset schema and structure."""
    
    def __init__(self) -> None:
        """Initialize the validator."""
        pass
    
    def validate_schema(
        self,
        dataset_path: Path,
        required_fields: List[str],
        optional_fields: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate dataset schema.
        
        Args:
            dataset_path: Path to dataset file
            required_fields: List of required field names
            optional_fields: List of optional field names
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            with open(dataset_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {e}")
                        continue
                    
                    # Check required fields
                    for field in required_fields:
                        if field not in record:
                            errors.append(f"Line {line_num}: Missing required field '{field}'")
                    
                    # Limit errors to first 10
                    if len(errors) >= 10:
                        errors.append("... (truncated)")
                        break
        except FileNotFoundError:
            errors.append(f"Dataset file not found: {dataset_path}")
        except Exception as e:
            errors.append(f"Error reading dataset: {e}")
        
        return (len(errors) == 0, errors)
    
    def validate_field_types(
        self,
        dataset_path: Path,
        field_types: Dict[str, type],
    ) -> Tuple[bool, List[str]]:
        """Validate field data types.
        
        Args:
            dataset_path: Path to dataset file
            field_types: Expected types for fields (field_name -> type)
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            with open(dataset_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    record = json.loads(line)
                    
                    for field, expected_type in field_types.items():
                        if field in record:
                            actual_value = record[field]
                            if actual_value is not None and not isinstance(actual_value, expected_type):
                                errors.append(
                                    f"Line {line_num}: Field '{field}' has type "
                                    f"{type(actual_value).__name__}, expected {expected_type.__name__}"
                                )
                    
                    if len(errors) >= 10:
                        errors.append("... (truncated)")
                        break
        except Exception as e:
            errors.append(f"Error validating types: {e}")
        
        return (len(errors) == 0, errors)


class RegressionTester:
    """Test for regressions in dataset pipelines."""
    
    def __init__(self) -> None:
        """Initialize the tester."""
        pass
    
    def compare_datasets(
        self,
        baseline_path: Path,
        current_path: Path,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare current dataset against baseline.
        
        Args:
            baseline_path: Path to baseline dataset
            current_path: Path to current dataset
        
        Returns:
            (no_regression, comparison_metrics)
        """
        baseline_records = self._load_records(baseline_path)
        current_records = self._load_records(current_path)
        
        metrics = {
            "baseline_count": len(baseline_records),
            "current_count": len(current_records),
            "count_diff": len(current_records) - len(baseline_records),
            "count_regression": len(current_records) < len(baseline_records),
        }
        
        # Compare quality scores
        baseline_quality = [r.get("quality_score", 0.0) for r in baseline_records if "quality_score" in r]
        current_quality = [r.get("quality_score", 0.0) for r in current_records if "quality_score" in r]
        
        if baseline_quality and current_quality:
            import statistics
            baseline_avg = statistics.mean(baseline_quality)
            current_avg = statistics.mean(current_quality)
            
            metrics["baseline_quality_avg"] = baseline_avg
            metrics["current_quality_avg"] = current_avg
            metrics["quality_diff"] = current_avg - baseline_avg
            metrics["quality_regression"] = current_avg < baseline_avg * 0.95  # 5% tolerance
        
        no_regression = not metrics.get("count_regression", False) and not metrics.get("quality_regression", False)
        
        return (no_regression, metrics)
    
    def _load_records(self, path: Path) -> List[Dict[str, Any]]:
        """Load records from JSONL file."""
        records = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records


class PropertyTester:
    """Property-based testing for datasets."""
    
    def __init__(self) -> None:
        """Initialize the tester."""
        pass
    
    def test_property(
        self,
        dataset_path: Path,
        property_name: str,
        property_func: Callable[[Dict[str, Any]], bool],
    ) -> Tuple[bool, int, int]:
        """Test a property across all dataset records.
        
        Args:
            dataset_path: Path to dataset file
            property_name: Name of the property being tested
            property_func: Function that returns True if property holds
        
        Returns:
            (all_passed, passed_count, failed_count)
        """
        passed = 0
        failed = 0
        
        with open(dataset_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                
                try:
                    if property_func(record):
                        passed += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
        
        return (failed == 0, passed, failed)


class DatasetTestFramework:
    """Comprehensive testing framework for datasets."""
    
    def __init__(self) -> None:
        """Initialize the framework."""
        self.generator = SyntheticDataGenerator()
        self.schema_validator = SchemaValidator()
        self.regression_tester = RegressionTester()
        self.property_tester = PropertyTester()
    
    def create_test_suite(
        self,
        suite_id: str,
        suite_name: str,
    ) -> TestSuite:
        """Create a new test suite."""
        return TestSuite(suite_id=suite_id, suite_name=suite_name)
    
    def run_schema_tests(
        self,
        dataset_path: Path,
        required_fields: List[str],
    ) -> TestCase:
        """Run schema validation tests."""
        is_valid, errors = self.schema_validator.validate_schema(dataset_path, required_fields)
        
        return TestCase(
            test_id="schema_validation",
            test_name="Schema Validation",
            test_type="schema",
            expected_result=True,
            actual_result=is_valid,
            passed=is_valid,
            error_message="; ".join(errors) if errors else "",
        )
    
    def run_regression_tests(
        self,
        baseline_path: Path,
        current_path: Path,
    ) -> TestCase:
        """Run regression tests."""
        no_regression, metrics = self.regression_tester.compare_datasets(baseline_path, current_path)
        
        return TestCase(
            test_id="regression_test",
            test_name="Regression Test",
            test_type="regression",
            expected_result=True,
            actual_result=no_regression,
            passed=no_regression,
            error_message="" if no_regression else f"Regression detected: {metrics}",
        )
    
    def run_property_tests(
        self,
        dataset_path: Path,
        property_name: str,
        property_func: Callable[[Dict[str, Any]], bool],
    ) -> TestCase:
        """Run property-based tests."""
        all_passed, passed_count, failed_count = self.property_tester.test_property(
            dataset_path,
            property_name,
            property_func,
        )
        
        return TestCase(
            test_id=f"property_{property_name}",
            test_name=f"Property: {property_name}",
            test_type="property",
            expected_result=True,
            actual_result=all_passed,
            passed=all_passed,
            error_message=f"Failed on {failed_count} records" if not all_passed else "",
        )
    
    def generate_test_dataset(
        self,
        num_records: int,
        output_path: Path,
    ) -> List[Dict[str, Any]]:
        """Generate a synthetic test dataset."""
        return self.generator.generate_dataset(num_records, output_path=output_path)
    
    def run_test_suite(self, suite: TestSuite) -> TestResult:
        """Execute a test suite and return results."""
        from datetime import datetime
        
        return TestResult(
            suite_id=suite.suite_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_tests=suite.total_tests(),
            passed_tests=suite.passed_tests(),
            failed_tests=suite.failed_tests(),
            pass_rate=suite.pass_rate(),
            test_suites=[suite],
        )
