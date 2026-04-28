"""Dataset federation for distributed query execution.

Provides federated query capabilities across multiple datasets
with query planning, optimization, and distributed execution.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class FederationStrategy(Enum):
    """Federation execution strategy."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    ADAPTIVE = "adaptive"
    DISTRIBUTED = "distributed"


class JoinType(Enum):
    """Join types for federated queries."""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    CROSS = "cross"


class AggregationFunction(Enum):
    """Aggregation functions."""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    DISTINCT = "distinct"


@dataclass
class DatasetEndpoint:
    """Dataset endpoint configuration."""
    endpoint_id: str
    name: str
    location: Path
    endpoint_type: str = "local"
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "endpoint_id": self.endpoint_id,
            "name": self.name,
            "location": str(self.location),
            "endpoint_type": self.endpoint_type,
            "metadata": self.metadata,
            "is_available": self.is_available,
        }


@dataclass
class FederatedQuery:
    """Federated query specification."""
    query_id: str
    endpoints: List[str]
    query_text: str
    query_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    join_conditions: List[Dict[str, Any]] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "endpoints": self.endpoints,
            "query_text": self.query_text,
            "query_type": self.query_type,
            "parameters": self.parameters,
            "join_conditions": self.join_conditions,
            "filters": self.filters,
            "aggregations": self.aggregations,
        }


@dataclass
class QueryExecutionPlan:
    """Query execution plan."""
    plan_id: str
    query_id: str
    steps: List[Dict[str, Any]]
    estimated_cost: float
    strategy: FederationStrategy
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "query_id": self.query_id,
            "steps": self.steps,
            "estimated_cost": self.estimated_cost,
            "strategy": self.strategy.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class FederatedQueryResult:
    """Federated query result."""
    query_id: str
    results: List[Dict[str, Any]]
    execution_time_ms: float
    endpoints_queried: List[str]
    total_records: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "results": self.results,
            "execution_time_ms": self.execution_time_ms,
            "endpoints_queried": self.endpoints_queried,
            "total_records": self.total_records,
            "metadata": self.metadata,
        }


class EndpointRegistry:
    """Registry for dataset endpoints."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize endpoint registry."""
        self.config_path = config_path
        self.endpoints: Dict[str, DatasetEndpoint] = {}
        
        if config_path and config_path.exists():
            self._load()
    
    def _load(self) -> None:
        """Load endpoints from config."""
        if not self.config_path or not self.config_path.exists():
            return
        
        data = json.loads(self.config_path.read_text())
        for ep_data in data.get("endpoints", []):
            endpoint = DatasetEndpoint(
                endpoint_id=ep_data["endpoint_id"],
                name=ep_data["name"],
                location=Path(ep_data["location"]),
                endpoint_type=ep_data.get("endpoint_type", "local"),
                metadata=ep_data.get("metadata", {}),
                is_available=ep_data.get("is_available", True),
            )
            self.endpoints[endpoint.endpoint_id] = endpoint
    
    def _save(self) -> None:
        """Save endpoints to config."""
        if not self.config_path:
            return
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "endpoints": [ep.to_dict() for ep in self.endpoints.values()],
            "updated_at": datetime.now().isoformat(),
        }
        self.config_path.write_text(json.dumps(data, indent=2))
    
    def register_endpoint(self, endpoint: DatasetEndpoint) -> None:
        """Register a dataset endpoint."""
        self.endpoints[endpoint.endpoint_id] = endpoint
        self._save()
    
    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister an endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            self._save()
            return True
        return False
    
    def get_endpoint(self, endpoint_id: str) -> Optional[DatasetEndpoint]:
        """Get endpoint by ID."""
        return self.endpoints.get(endpoint_id)
    
    def list_endpoints(self, available_only: bool = False) -> List[DatasetEndpoint]:
        """List all endpoints."""
        endpoints = list(self.endpoints.values())
        if available_only:
            endpoints = [ep for ep in endpoints if ep.is_available]
        return endpoints
    
    def mark_unavailable(self, endpoint_id: str) -> None:
        """Mark endpoint as unavailable."""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].is_available = False
            self._save()


class QueryPlanner:
    """Plan federated query execution."""
    
    def __init__(self, registry: EndpointRegistry):
        """Initialize query planner."""
        self.registry = registry
    
    def create_plan(
        self,
        query: FederatedQuery,
        strategy: FederationStrategy = FederationStrategy.PARALLEL,
    ) -> QueryExecutionPlan:
        """Create query execution plan."""
        steps = []
        
        # Step 1: Validate endpoints
        for endpoint_id in query.endpoints:
            endpoint = self.registry.get_endpoint(endpoint_id)
            if not endpoint or not endpoint.is_available:
                steps.append({
                    "step": "validate",
                    "endpoint": endpoint_id,
                    "status": "failed",
                    "reason": "endpoint_unavailable",
                })
                continue
            
            steps.append({
                "step": "validate",
                "endpoint": endpoint_id,
                "status": "success",
            })
        
        # Step 2: Plan data retrieval
        for endpoint_id in query.endpoints:
            steps.append({
                "step": "retrieve",
                "endpoint": endpoint_id,
                "operation": "scan",
                "filters": query.filters,
            })
        
        # Step 3: Plan joins if needed
        if query.join_conditions:
            steps.append({
                "step": "join",
                "join_type": "inner",
                "conditions": query.join_conditions,
            })
        
        # Step 4: Plan aggregations
        if query.aggregations:
            steps.append({
                "step": "aggregate",
                "functions": query.aggregations,
            })
        
        # Estimate cost
        cost = len(query.endpoints) * 1.0
        if query.join_conditions:
            cost *= 2.0
        if query.aggregations:
            cost *= 1.5
        
        plan_id = f"plan_{query.query_id}"
        
        return QueryExecutionPlan(
            plan_id=plan_id,
            query_id=query.query_id,
            steps=steps,
            estimated_cost=cost,
            strategy=strategy,
            created_at=datetime.now(),
        )
    
    def optimize_plan(self, plan: QueryExecutionPlan) -> QueryExecutionPlan:
        """Optimize execution plan."""
        # Simple optimization: reorder steps
        optimized_steps = []
        
        # Validation first
        optimized_steps.extend([s for s in plan.steps if s["step"] == "validate"])
        
        # Filters before retrieval
        optimized_steps.extend([s for s in plan.steps if s["step"] == "retrieve"])
        
        # Joins
        optimized_steps.extend([s for s in plan.steps if s["step"] == "join"])
        
        # Aggregations last
        optimized_steps.extend([s for s in plan.steps if s["step"] == "aggregate"])
        
        plan.steps = optimized_steps
        plan.estimated_cost *= 0.9  # 10% cost reduction from optimization
        
        return plan


class FederatedQueryExecutor:
    """Execute federated queries."""
    
    def __init__(self, registry: EndpointRegistry, planner: QueryPlanner):
        """Initialize executor."""
        self.registry = registry
        self.planner = planner
    
    def execute(
        self,
        query: FederatedQuery,
        strategy: FederationStrategy = FederationStrategy.PARALLEL,
    ) -> FederatedQueryResult:
        """Execute federated query."""
        start_time = datetime.now()
        
        # Create and optimize plan
        plan = self.planner.create_plan(query, strategy)
        plan = self.planner.optimize_plan(plan)
        
        # Execute plan
        results = []
        endpoints_queried = []
        
        for step in plan.steps:
            if step["step"] == "retrieve":
                endpoint_id = step["endpoint"]
                endpoint = self.registry.get_endpoint(endpoint_id)
                
                if endpoint and endpoint.is_available:
                    # Read dataset
                    data = self._read_endpoint(endpoint)
                    results.extend(data)
                    endpoints_queried.append(endpoint_id)
        
        # Apply filters
        if query.filters:
            results = self._apply_filters(results, query.filters)
        
        # Apply aggregations
        if query.aggregations:
            results = self._apply_aggregations(results, query.aggregations)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return FederatedQueryResult(
            query_id=query.query_id,
            results=results,
            execution_time_ms=execution_time,
            endpoints_queried=endpoints_queried,
            total_records=len(results),
        )
    
    def _read_endpoint(self, endpoint: DatasetEndpoint) -> List[Dict[str, Any]]:
        """Read data from endpoint."""
        if not endpoint.location.exists():
            return []
        
        content = endpoint.location.read_text()
        records = []
        for line in content.strip().split("\n"):
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return records
    
    def _apply_filters(
        self,
        records: List[Dict[str, Any]],
        filters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Apply filters to records."""
        filtered = records
        
        for filter_spec in filters:
            field = filter_spec.get("field")
            operator = filter_spec.get("operator")
            value = filter_spec.get("value")
            
            if operator == "=":
                filtered = [r for r in filtered if r.get(field) == value]
            elif operator == ">":
                filtered = [r for r in filtered if r.get(field, 0) > value]
            elif operator == "<":
                filtered = [r for r in filtered if r.get(field, 0) < value]
        
        return filtered
    
    def _apply_aggregations(
        self,
        records: List[Dict[str, Any]],
        aggregations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Apply aggregations to records."""
        results = []
        
        for agg_spec in aggregations:
            func = agg_spec.get("function")
            field = agg_spec.get("field")
            
            if func == "count":
                results.append({"function": "count", "result": len(records)})
            elif func == "sum":
                total = sum(r.get(field, 0) for r in records)
                results.append({"function": "sum", "field": field, "result": total})
            elif func == "avg":
                if records:
                    avg = sum(r.get(field, 0) for r in records) / len(records)
                    results.append({"function": "avg", "field": field, "result": avg})
        
        return results


class FederatedJoinEngine:
    """Execute federated joins."""
    
    def __init__(self):
        """Initialize join engine."""
        pass
    
    def inner_join(
        self,
        left_records: List[Dict[str, Any]],
        right_records: List[Dict[str, Any]],
        left_key: str,
        right_key: str,
    ) -> List[Dict[str, Any]]:
        """Perform inner join."""
        # Create index on right side
        right_index: Dict[Any, List[Dict[str, Any]]] = {}
        for record in right_records:
            key = record.get(right_key)
            if key not in right_index:
                right_index[key] = []
            right_index[key].append(record)
        
        # Join
        result = []
        for left_record in left_records:
            key = left_record.get(left_key)
            if key in right_index:
                for right_record in right_index[key]:
                    joined = {**left_record, **right_record}
                    result.append(joined)
        
        return result
    
    def left_join(
        self,
        left_records: List[Dict[str, Any]],
        right_records: List[Dict[str, Any]],
        left_key: str,
        right_key: str,
    ) -> List[Dict[str, Any]]:
        """Perform left join."""
        right_index: Dict[Any, List[Dict[str, Any]]] = {}
        for record in right_records:
            key = record.get(right_key)
            if key not in right_index:
                right_index[key] = []
            right_index[key].append(record)
        
        result = []
        for left_record in left_records:
            key = left_record.get(left_key)
            if key in right_index:
                for right_record in right_index[key]:
                    joined = {**left_record, **right_record}
                    result.append(joined)
            else:
                result.append(left_record)
        
        return result


class FederationStatistics:
    """Track federation statistics."""
    
    def __init__(self):
        """Initialize statistics tracker."""
        self.queries_executed = 0
        self.total_execution_time_ms = 0.0
        self.total_records_returned = 0
        self.endpoints_accessed: Dict[str, int] = {}
    
    def record_query(self, result: FederatedQueryResult) -> None:
        """Record query execution."""
        self.queries_executed += 1
        self.total_execution_time_ms += result.execution_time_ms
        self.total_records_returned += result.total_records
        
        for endpoint_id in result.endpoints_queried:
            self.endpoints_accessed[endpoint_id] = self.endpoints_accessed.get(endpoint_id, 0) + 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get federation statistics."""
        avg_time = self.total_execution_time_ms / max(self.queries_executed, 1)
        avg_records = self.total_records_returned / max(self.queries_executed, 1)
        
        return {
            "queries_executed": self.queries_executed,
            "avg_execution_time_ms": avg_time,
            "avg_records_per_query": avg_records,
            "total_records_returned": self.total_records_returned,
            "endpoints_accessed": self.endpoints_accessed,
        }


class FederationCatalog:
    """Catalog of federated datasets."""
    
    def __init__(self, registry: EndpointRegistry):
        """Initialize catalog."""
        self.registry = registry
        self.catalog: Dict[str, Dict[str, Any]] = {}
    
    def index_endpoint(self, endpoint_id: str) -> None:
        """Index an endpoint."""
        endpoint = self.registry.get_endpoint(endpoint_id)
        if not endpoint:
            return
        
        # Read and analyze dataset
        records = []
        if endpoint.location.exists():
            content = endpoint.location.read_text()
            for line in content.strip().split("\n"):
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Extract schema
        fields = set()
        for record in records:
            fields.update(record.keys())
        
        self.catalog[endpoint_id] = {
            "endpoint_id": endpoint_id,
            "record_count": len(records),
            "fields": list(fields),
            "indexed_at": datetime.now().isoformat(),
        }
    
    def search_catalog(self, field_name: str) -> List[str]:
        """Search catalog for endpoints with field."""
        matching_endpoints = []
        
        for endpoint_id, info in self.catalog.items():
            if field_name in info.get("fields", []):
                matching_endpoints.append(endpoint_id)
        
        return matching_endpoints
    
    def get_catalog_info(self) -> Dict[str, Any]:
        """Get catalog information."""
        return {
            "total_endpoints": len(self.catalog),
            "total_records": sum(info["record_count"] for info in self.catalog.values()),
            "endpoints": list(self.catalog.values()),
        }
