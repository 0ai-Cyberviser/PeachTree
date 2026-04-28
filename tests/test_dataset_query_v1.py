"""Tests for dataset_query module."""
import json
import pytest
from peachtree.dataset_query import (
    DatasetQueryEngine,
    QueryBuilder,
    QueryCondition,
    QueryOperator,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample JSONL dataset."""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": 1, "name": "Alice", "age": 25, "city": "NYC"},
        {"id": 2, "name": "Bob", "age": 30, "city": "LA"},
        {"id": 3, "name": "Charlie", "age": 25, "city": "NYC"},
        {"id": 4, "name": "Diana", "age": 35, "city": "SF"},
        {"id": 5, "name": "Eve", "age": 30, "city": "NYC"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


def test_query_engine_init():
    """Test query engine initialization."""
    engine = DatasetQueryEngine()
    assert engine is not None


def test_execute_simple_query(sample_dataset):
    """Test executing a simple query."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("age", QueryOperator.EQ, 25).build()
    
    results = engine.execute(sample_dataset, query)
    
    assert len(results) == 2
    assert all(r["age"] == 25 for r in results)


def test_execute_with_limit(sample_dataset):
    """Test query with limit."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().limit(2).build()
    
    results = engine.execute(sample_dataset, query)
    
    assert len(results) == 2


def test_execute_with_offset(sample_dataset):
    """Test query with offset."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().offset(2).build()
    
    results = engine.execute(sample_dataset, query)
    
    assert len(results) == 3


def test_execute_with_select(sample_dataset):
    """Test query with field selection."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().select("name", "age").build()
    
    results = engine.execute(sample_dataset, query)
    
    assert all("name" in r and "age" in r for r in results)
    assert all("city" not in r for r in results)


def test_count_query(sample_dataset):
    """Test counting records."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("city", QueryOperator.EQ, "NYC").build()
    
    count = engine.count(sample_dataset, query)
    
    assert count == 3


def test_aggregate_sum(sample_dataset):
    """Test sum aggregation."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    result = engine.aggregate(sample_dataset, query, "age", "sum")
    
    assert result == 145  # 25 + 30 + 25 + 35 + 30


def test_aggregate_avg(sample_dataset):
    """Test average aggregation."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    result = engine.aggregate(sample_dataset, query, "age", "avg")
    
    assert result == 29.0


def test_aggregate_min(sample_dataset):
    """Test min aggregation."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    result = engine.aggregate(sample_dataset, query, "age", "min")
    
    assert result == 25


def test_aggregate_max(sample_dataset):
    """Test max aggregation."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    result = engine.aggregate(sample_dataset, query, "age", "max")
    
    assert result == 35


def test_group_by(sample_dataset):
    """Test grouping records."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    groups = engine.group_by(sample_dataset, query, "city")
    
    assert len(groups) == 3
    assert len(groups["NYC"]) == 3
    assert len(groups["LA"]) == 1
    assert len(groups["SF"]) == 1


def test_distinct_values(sample_dataset):
    """Test getting distinct values."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    values = engine.distinct(sample_dataset, query, "age")
    
    assert set(values) == {25, 30, 35}


def test_query_builder_where(sample_dataset):
    """Test query builder where clause."""
    builder = QueryBuilder()
    query = builder.where("age", QueryOperator.GT, 25).build()
    
    assert len(query.conditions) == 1
    assert query.conditions[0].field == "age"
    assert query.conditions[0].operator == QueryOperator.GT


def test_query_builder_select():
    """Test query builder select."""
    builder = QueryBuilder()
    query = builder.select("name", "age").build()
    
    assert query.fields == ["name", "age"]


def test_query_builder_limit():
    """Test query builder limit."""
    builder = QueryBuilder()
    query = builder.limit(10).build()
    
    assert query.limit == 10


def test_query_builder_offset():
    """Test query builder offset."""
    builder = QueryBuilder()
    query = builder.offset(5).build()
    
    assert query.offset == 5


def test_query_builder_order_by():
    """Test query builder order by."""
    builder = QueryBuilder()
    query = builder.order_by("age", ascending=False).build()
    
    assert query.order_by == "age"
    assert not query.ascending


def test_query_operator_eq(sample_dataset):
    """Test EQ operator."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("age", QueryOperator.EQ, 25).build()
    
    results = engine.execute(sample_dataset, query)
    assert len(results) == 2


def test_query_operator_ne(sample_dataset):
    """Test NE operator."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("age", QueryOperator.NE, 25).build()
    
    results = engine.execute(sample_dataset, query)
    assert len(results) == 3


def test_query_operator_gt(sample_dataset):
    """Test GT operator."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("age", QueryOperator.GT, 25).build()
    
    results = engine.execute(sample_dataset, query)
    assert all(r["age"] > 25 for r in results)


def test_query_operator_lt(sample_dataset):
    """Test LT operator."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().where("age", QueryOperator.LT, 30).build()
    
    results = engine.execute(sample_dataset, query)
    assert all(r["age"] < 30 for r in results)


def test_query_condition_creation():
    """Test query condition creation."""
    condition = QueryCondition("age", QueryOperator.EQ, 25)
    
    assert condition.field == "age"
    assert condition.operator == QueryOperator.EQ
    assert condition.value == 25


def test_empty_query_returns_all(sample_dataset):
    """Test empty query returns all records."""
    engine = DatasetQueryEngine()
    query = QueryBuilder().build()
    
    results = engine.execute(sample_dataset, query)
    
    assert len(results) == 5


def test_multiple_conditions(sample_dataset):
    """Test query with multiple conditions."""
    engine = DatasetQueryEngine()
    query = (QueryBuilder()
             .where("age", QueryOperator.EQ, 25)
             .where("city", QueryOperator.EQ, "NYC")
             .build())
    
    results = engine.execute(sample_dataset, query)
    assert len(results) <= 2


def test_query_serialization():
    """Test query serialization."""
    query = QueryBuilder().where("age", QueryOperator.EQ, 25).build()
    data = query.to_dict()
    
    assert "conditions" in data
