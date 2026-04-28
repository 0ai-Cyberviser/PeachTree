"""Tests for dataset_federation module."""
import pytest
from peachtree.dataset_federation import (
    EndpointRegistry,
    QueryPlanner,
    FederatedQueryExecutor,
    FederatedQuery,
    FederatedQueryResult,
    FederationStrategy,
    DatasetEndpoint,
    FederatedJoinEngine,
    FederationStatistics,
    FederationCatalog,
)


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary registry."""
    registry_path = tmp_path / "registry.json"
    return registry_path


@pytest.fixture
def registry(temp_registry):
    """Create endpoint registry."""
    return EndpointRegistry(temp_registry)


@pytest.fixture
def sample_endpoint(tmp_path):
    """Create sample endpoint."""
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text('{"id": 1, "value": "test"}\n{"id": 2, "value": "data"}')
    
    return DatasetEndpoint(
        endpoint_id="ep1",
        name="Test Endpoint",
        location=dataset_path,
    )


@pytest.fixture
def planner(registry):
    """Create query planner."""
    return QueryPlanner(registry)


@pytest.fixture
def executor(registry, planner):
    """Create query executor."""
    return FederatedQueryExecutor(registry, planner)


def test_dataset_endpoint_creation(sample_endpoint):
    """Test endpoint creation."""
    assert sample_endpoint.endpoint_id == "ep1"
    assert sample_endpoint.name == "Test Endpoint"
    assert sample_endpoint.is_available


def test_dataset_endpoint_to_dict(sample_endpoint):
    """Test endpoint serialization."""
    data = sample_endpoint.to_dict()
    assert data["endpoint_id"] == "ep1"
    assert data["name"] == "Test Endpoint"
    assert data["is_available"]


def test_registry_register_endpoint(registry, sample_endpoint):
    """Test endpoint registration."""
    registry.register_endpoint(sample_endpoint)
    
    assert sample_endpoint.endpoint_id in registry.endpoints
    endpoint = registry.get_endpoint("ep1")
    assert endpoint.name == "Test Endpoint"


def test_registry_unregister_endpoint(registry, sample_endpoint):
    """Test endpoint unregistration."""
    registry.register_endpoint(sample_endpoint)
    result = registry.unregister_endpoint("ep1")
    
    assert result is True
    assert "ep1" not in registry.endpoints


def test_registry_list_endpoints(registry, sample_endpoint):
    """Test listing endpoints."""
    registry.register_endpoint(sample_endpoint)
    
    endpoints = registry.list_endpoints()
    assert len(endpoints) == 1
    assert endpoints[0].endpoint_id == "ep1"


def test_registry_list_available_only(registry, sample_endpoint):
    """Test listing only available endpoints."""
    registry.register_endpoint(sample_endpoint)
    registry.mark_unavailable("ep1")
    
    available = registry.list_endpoints(available_only=True)
    assert len(available) == 0
    
    all_endpoints = registry.list_endpoints(available_only=False)
    assert len(all_endpoints) == 1


def test_registry_persistence(temp_registry, sample_endpoint):
    """Test registry persistence."""
    registry = EndpointRegistry(temp_registry)
    registry.register_endpoint(sample_endpoint)
    
    # Load from same file
    new_registry = EndpointRegistry(temp_registry)
    assert len(new_registry.endpoints) == 1
    assert "ep1" in new_registry.endpoints


def test_federated_query_creation():
    """Test query creation."""
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1", "ep2"],
        query_text="SELECT * FROM datasets",
        query_type="select",
    )
    
    assert query.query_id == "q1"
    assert len(query.endpoints) == 2


def test_federated_query_to_dict():
    """Test query serialization."""
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
        filters=[{"field": "id", "operator": "=", "value": 1}],
    )
    
    data = query.to_dict()
    assert data["query_id"] == "q1"
    assert len(data["filters"]) == 1


def test_query_planner_create_plan(planner, sample_endpoint, registry):
    """Test creating execution plan."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    plan = planner.create_plan(query)
    assert plan.query_id == "q1"
    assert len(plan.steps) > 0


def test_query_planner_optimize_plan(planner, sample_endpoint, registry):
    """Test plan optimization."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    plan = planner.create_plan(query)
    original_cost = plan.estimated_cost
    
    optimized = planner.optimize_plan(plan)
    assert optimized.estimated_cost <= original_cost


def test_executor_execute_simple_query(executor, sample_endpoint, registry):
    """Test executing simple query."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    result = executor.execute(query)
    assert result.query_id == "q1"
    assert result.total_records >= 0
    assert "ep1" in result.endpoints_queried


def test_executor_apply_filters(executor):
    """Test applying filters."""
    records = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30},
    ]
    
    filters = [{"field": "value", "operator": ">", "value": 15}]
    filtered = executor._apply_filters(records, filters)
    
    assert len(filtered) == 2
    assert all(r["value"] > 15 for r in filtered)


def test_executor_apply_aggregations(executor):
    """Test applying aggregations."""
    records = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30},
    ]
    
    aggregations = [
        {"function": "count"},
        {"function": "sum", "field": "value"},
        {"function": "avg", "field": "value"},
    ]
    
    results = executor._apply_aggregations(records, aggregations)
    assert len(results) == 3
    assert results[0]["result"] == 3
    assert results[1]["result"] == 60
    assert results[2]["result"] == 20


def test_join_engine_inner_join():
    """Test inner join."""
    engine = FederatedJoinEngine()
    
    left = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    
    right = [
        {"id": 1, "score": 90},
        {"id": 3, "score": 85},
    ]
    
    result = engine.inner_join(left, right, "id", "id")
    assert len(result) == 1
    assert result[0]["name"] == "Alice"
    assert result[0]["score"] == 90


def test_join_engine_left_join():
    """Test left join."""
    engine = FederatedJoinEngine()
    
    left = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    
    right = [
        {"id": 1, "score": 90},
    ]
    
    result = engine.left_join(left, right, "id", "id")
    assert len(result) == 2
    assert result[1]["name"] == "Bob"


def test_federation_statistics_record_query():
    """Test recording query statistics."""
    stats = FederationStatistics()
    
    result = FederatedQueryResult(
        query_id="q1",
        results=[],
        execution_time_ms=100.0,
        endpoints_queried=["ep1", "ep2"],
        total_records=50,
    )
    
    stats.record_query(result)
    
    assert stats.queries_executed == 1
    assert stats.total_execution_time_ms == 100.0
    assert stats.total_records_returned == 50
    assert stats.endpoints_accessed["ep1"] == 1


def test_federation_statistics_get_statistics():
    """Test getting statistics."""
    stats = FederationStatistics()
    
    for i in range(3):
        result = FederatedQueryResult(
            query_id=f"q{i}",
            results=[],
            execution_time_ms=100.0,
            endpoints_queried=["ep1"],
            total_records=10,
        )
        stats.record_query(result)
    
    summary = stats.get_statistics()
    assert summary["queries_executed"] == 3
    assert summary["avg_execution_time_ms"] == 100.0
    assert summary["avg_records_per_query"] == 10.0


def test_federation_catalog_index_endpoint(registry, sample_endpoint):
    """Test indexing endpoint."""
    registry.register_endpoint(sample_endpoint)
    catalog = FederationCatalog(registry)
    
    catalog.index_endpoint("ep1")
    
    assert "ep1" in catalog.catalog
    assert catalog.catalog["ep1"]["record_count"] >= 0


def test_federation_catalog_search(registry, sample_endpoint):
    """Test catalog search."""
    registry.register_endpoint(sample_endpoint)
    catalog = FederationCatalog(registry)
    
    catalog.index_endpoint("ep1")
    
    # Search for field
    results = catalog.search_catalog("id")
    assert "ep1" in results


def test_federation_catalog_get_info(registry, sample_endpoint):
    """Test getting catalog info."""
    registry.register_endpoint(sample_endpoint)
    catalog = FederationCatalog(registry)
    
    catalog.index_endpoint("ep1")
    
    info = catalog.get_catalog_info()
    assert info["total_endpoints"] == 1
    assert info["total_records"] >= 0


def test_query_execution_plan_to_dict(planner, sample_endpoint, registry):
    """Test execution plan serialization."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    plan = planner.create_plan(query)
    data = plan.to_dict()
    
    assert data["query_id"] == "q1"
    assert "steps" in data
    assert "estimated_cost" in data


def test_federated_query_result_to_dict():
    """Test query result serialization."""
    result = FederatedQueryResult(
        query_id="q1",
        results=[{"id": 1}],
        execution_time_ms=50.0,
        endpoints_queried=["ep1"],
        total_records=1,
    )
    
    data = result.to_dict()
    assert data["query_id"] == "q1"
    assert data["total_records"] == 1


def test_parallel_strategy(executor, sample_endpoint, registry):
    """Test parallel execution strategy."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    result = executor.execute(query, FederationStrategy.PARALLEL)
    assert result.query_id == "q1"


def test_sequential_strategy(executor, sample_endpoint, registry):
    """Test sequential execution strategy."""
    registry.register_endpoint(sample_endpoint)
    
    query = FederatedQuery(
        query_id="q1",
        endpoints=["ep1"],
        query_text="SELECT *",
        query_type="select",
    )
    
    result = executor.execute(query, FederationStrategy.SEQUENTIAL)
    assert result.query_id == "q1"


def test_read_endpoint_with_invalid_json(executor, tmp_path):
    """Test reading endpoint with invalid JSON."""
    dataset_path = tmp_path / "invalid.jsonl"
    dataset_path.write_text('{"id": 1}\ninvalid json\n{"id": 2}')
    
    endpoint = DatasetEndpoint(
        endpoint_id="ep1",
        name="Invalid",
        location=dataset_path,
    )
    
    records = executor._read_endpoint(endpoint)
    assert len(records) == 2  # Should skip invalid line


def test_empty_dataset(executor, tmp_path):
    """Test querying empty dataset."""
    dataset_path = tmp_path / "empty.jsonl"
    dataset_path.write_text("")
    
    endpoint = DatasetEndpoint(
        endpoint_id="ep1",
        name="Empty",
        location=dataset_path,
    )
    
    records = executor._read_endpoint(endpoint)
    assert len(records) == 0
