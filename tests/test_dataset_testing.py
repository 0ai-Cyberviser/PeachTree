"""Tests for dataset_testing module"""
import json
import pytest

from peachtree.dataset_testing import (
    DatasetTestFramework,
    SyntheticDataGenerator,
    SchemaValidator,
    RegressionTester,
    PropertyTester,
    TestCase,
    TestSuite,
    TestResult,
)


@pytest.fixture
def framework():
    return DatasetTestFramework()


@pytest.fixture
def generator():
    return SyntheticDataGenerator(seed=42)


@pytest.fixture
def validator():
    return SchemaValidator()


@pytest.fixture
def regression_tester():
    return RegressionTester()


@pytest.fixture
def property_tester():
    return PropertyTester()


@pytest.fixture
def sample_dataset(tmp_path):
    dataset = tmp_path / "sample.jsonl"
    records = [
        {"id": "1", "content": "Test content", "quality_score": 85.0},
        {"id": "2", "content": "More content", "quality_score": 90.0},
        {"id": "3", "content": "Final content", "quality_score": 75.0},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


def test_test_case_creation():
    test_case = TestCase(
        test_id="test_1",
        test_name="Test One",
        test_type="schema",
        expected_result=True,
        actual_result=True,
        passed=True,
    )
    assert test_case.test_id == "test_1"
    assert test_case.passed is True


def test_test_case_to_dict():
    test_case = TestCase(
        test_id="test_1",
        test_name="Test One",
        test_type="schema",
        expected_result=True,
        actual_result=False,
        passed=False,
        error_message="Failed validation",
    )
    d = test_case.to_dict()
    assert d["test_id"] == "test_1"
    assert d["passed"] is False
    assert d["error_message"] == "Failed validation"


def test_test_suite_creation():
    suite = TestSuite(suite_id="suite_1", suite_name="Test Suite")
    assert suite.suite_id == "suite_1"
    assert len(suite.test_cases) == 0


def test_test_suite_add_test():
    suite = TestSuite(suite_id="suite_1", suite_name="Test Suite")
    test_case = TestCase("test_1", "Test One", "schema", True, True, True)
    
    suite.add_test(test_case)
    
    assert suite.total_tests() == 1
    assert suite.passed_tests() == 1


def test_test_suite_pass_rate():
    suite = TestSuite(suite_id="suite_1", suite_name="Test Suite")
    suite.add_test(TestCase("t1", "T1", "schema", True, True, True))
    suite.add_test(TestCase("t2", "T2", "schema", True, False, False))
    suite.add_test(TestCase("t3", "T3", "schema", True, True, True))
    
    assert suite.total_tests() == 3
    assert suite.passed_tests() == 2
    assert suite.failed_tests() == 1
    assert suite.pass_rate() == pytest.approx(66.67, rel=0.1)


def test_test_suite_to_dict():
    suite = TestSuite(suite_id="suite_1", suite_name="Test Suite")
    suite.add_test(TestCase("t1", "T1", "schema", True, True, True))
    
    d = suite.to_dict()
    assert d["suite_id"] == "suite_1"
    assert d["total_tests"] == 1
    assert d["pass_rate"] == 100.0


def test_test_result_to_json():
    result = TestResult(
        suite_id="suite_1",
        timestamp="2024-01-01T00:00:00Z",
        total_tests=10,
        passed_tests=8,
        failed_tests=2,
        pass_rate=80.0,
    )
    json_str = result.to_json()
    data = json.loads(json_str)
    
    assert data["total_tests"] == 10
    assert data["pass_rate"] == 80.0


def test_generate_dataset(generator, tmp_path):
    output = tmp_path / "generated.jsonl"
    
    records = generator.generate_dataset(
        num_records=10,
        output_path=output,
    )
    
    assert len(records) == 10
    assert output.exists()
    
    # Verify structure
    assert "id" in records[0]
    assert "content" in records[0]
    assert "quality_score" in records[0]


def test_generate_dataset_with_schema(generator):
    schema = {
        "id": "id",
        "name": "text",
        "age": "int",
        "active": "bool",
    }
    
    records = generator.generate_dataset(num_records=5, schema=schema)
    
    assert len(records) == 5
    assert "id" in records[0]
    assert "name" in records[0]
    assert "age" in records[0]
    assert "active" in records[0]
    assert isinstance(records[0]["age"], int)
    assert isinstance(records[0]["active"], bool)


def test_generate_edge_cases(generator):
    edge_cases = generator.generate_edge_cases()
    
    assert len(edge_cases) > 0
    assert any(r["id"] == "empty_content" for r in edge_cases)
    assert any(r["id"] == "very_long_content" for r in edge_cases)
    assert any(r["id"] == "unicode" for r in edge_cases)


def test_validate_schema_success(validator, sample_dataset):
    is_valid, errors = validator.validate_schema(
        sample_dataset,
        required_fields=["id", "content"],
    )
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_schema_failure(validator, tmp_path):
    dataset = tmp_path / "invalid.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "test"}) + "\n")
        f.write(json.dumps({"content": "missing id"}) + "\n")  # Missing id
    
    is_valid, errors = validator.validate_schema(
        dataset,
        required_fields=["id", "content"],
    )
    
    assert is_valid is False
    assert len(errors) > 0


def test_validate_schema_invalid_json(validator, tmp_path):
    dataset = tmp_path / "invalid.jsonl"
    with open(dataset, 'w') as f:
        f.write("invalid json\n")
    
    is_valid, errors = validator.validate_schema(
        dataset,
        required_fields=["id"],
    )
    
    assert is_valid is False
    assert len(errors) > 0


def test_validate_field_types_success(validator, sample_dataset):
    is_valid, errors = validator.validate_field_types(
        sample_dataset,
        field_types={"id": str, "content": str, "quality_score": float},
    )
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_field_types_failure(validator, tmp_path):
    dataset = tmp_path / "invalid.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "count": "not_a_number"}) + "\n")
    
    is_valid, errors = validator.validate_field_types(
        dataset,
        field_types={"count": int},
    )
    
    assert is_valid is False
    assert len(errors) > 0


def test_compare_datasets_no_regression(regression_tester, tmp_path):
    # Baseline dataset
    baseline = tmp_path / "baseline.jsonl"
    with open(baseline, 'w') as f:
        for i in range(100):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 75.0}) + "\n")
    
    # Current dataset (improved)
    current = tmp_path / "current.jsonl"
    with open(current, 'w') as f:
        for i in range(110):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 80.0}) + "\n")
    
    no_regression, metrics = regression_tester.compare_datasets(baseline, current)
    
    assert no_regression is True
    assert metrics["count_diff"] == 10
    assert metrics["quality_diff"] == 5.0


def test_compare_datasets_with_regression(regression_tester, tmp_path):
    # Baseline dataset
    baseline = tmp_path / "baseline.jsonl"
    with open(baseline, 'w') as f:
        for i in range(100):
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 80.0}) + "\n")
    
    # Current dataset (degraded)
    current = tmp_path / "current.jsonl"
    with open(current, 'w') as f:
        for i in range(50):  # Fewer records
            f.write(json.dumps({"id": str(i), "content": "test", "quality_score": 65.0}) + "\n")  # Lower quality
    
    no_regression, metrics = regression_tester.compare_datasets(baseline, current)
    
    assert no_regression is False
    assert metrics["count_regression"] is True


def test_property_test_success(property_tester, sample_dataset):
    # Test property: all records have content
    all_passed, passed, failed = property_tester.test_property(
        sample_dataset,
        "has_content",
        lambda r: bool(r.get("content", "").strip()),
    )
    
    assert all_passed is True
    assert passed == 3
    assert failed == 0


def test_property_test_failure(property_tester, tmp_path):
    dataset = tmp_path / "test.jsonl"
    with open(dataset, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "test"}) + "\n")
        f.write(json.dumps({"id": "2", "content": ""}) + "\n")  # Empty content
    
    all_passed, passed, failed = property_tester.test_property(
        dataset,
        "has_content",
        lambda r: bool(r.get("content", "").strip()),
    )
    
    assert all_passed is False
    assert passed == 1
    assert failed == 1


def test_framework_create_test_suite(framework):
    suite = framework.create_test_suite("suite_1", "Test Suite")
    
    assert suite.suite_id == "suite_1"
    assert suite.suite_name == "Test Suite"


def test_framework_run_schema_tests(framework, sample_dataset):
    test_case = framework.run_schema_tests(
        sample_dataset,
        required_fields=["id", "content"],
    )
    
    assert test_case.test_id == "schema_validation"
    assert test_case.passed is True


def test_framework_run_regression_tests(framework, tmp_path):
    baseline = tmp_path / "baseline.jsonl"
    with open(baseline, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "test", "quality_score": 75.0}) + "\n")
    
    current = tmp_path / "current.jsonl"
    with open(current, 'w') as f:
        f.write(json.dumps({"id": "1", "content": "test", "quality_score": 80.0}) + "\n")
    
    test_case = framework.run_regression_tests(baseline, current)
    
    assert test_case.test_id == "regression_test"
    assert test_case.passed is True


def test_framework_run_property_tests(framework, sample_dataset):
    test_case = framework.run_property_tests(
        sample_dataset,
        "has_id",
        lambda r: "id" in r,
    )
    
    assert test_case.test_type == "property"
    assert test_case.passed is True


def test_framework_generate_test_dataset(framework, tmp_path):
    output = tmp_path / "test.jsonl"
    
    records = framework.generate_test_dataset(50, output)
    
    assert len(records) == 50
    assert output.exists()


def test_framework_run_test_suite(framework):
    suite = framework.create_test_suite("suite_1", "Test Suite")
    suite.add_test(TestCase("t1", "T1", "schema", True, True, True))
    suite.add_test(TestCase("t2", "T2", "schema", True, True, True))
    
    result = framework.run_test_suite(suite)
    
    assert result.total_tests == 2
    assert result.passed_tests == 2
    assert result.pass_rate == 100.0


def test_synthetic_data_field_types(generator):
    records = generator.generate_dataset(5)
    
    record = records[0]
    assert isinstance(record["id"], str)
    assert isinstance(record["content"], str)
    assert isinstance(record["quality_score"], float)
    assert isinstance(record["metadata"], dict)
