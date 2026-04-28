"""Advanced query engine for filtering and projecting datasets with SQL-like DSL."""

import json
import operator
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union


class QueryOperator(Enum):
    """Query operators."""
    
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"
    EXISTS = "exists"


class LogicalOperator(Enum):
    """Logical operators for combining conditions."""
    
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class QueryCondition:
    """Single query condition."""
    
    field: str
    operator: QueryOperator
    value: Any = None
    
    def evaluate(self, record: Dict[str, Any]) -> bool:
        """Evaluate condition against a record."""
        field_value = self._get_field_value(record, self.field)
        
        if self.operator == QueryOperator.EQ:
            return field_value == self.value
        
        elif self.operator == QueryOperator.NE:
            return field_value != self.value
        
        elif self.operator == QueryOperator.GT:
            return field_value > self.value
        
        elif self.operator == QueryOperator.GTE:
            return field_value >= self.value
        
        elif self.operator == QueryOperator.LT:
            return field_value < self.value
        
        elif self.operator == QueryOperator.LTE:
            return field_value <= self.value
        
        elif self.operator == QueryOperator.IN:
            return field_value in self.value
        
        elif self.operator == QueryOperator.NOT_IN:
            return field_value not in self.value
        
        elif self.operator == QueryOperator.CONTAINS:
            return self.value in str(field_value)
        
        elif self.operator == QueryOperator.STARTS_WITH:
            return str(field_value).startswith(str(self.value))
        
        elif self.operator == QueryOperator.ENDS_WITH:
            return str(field_value).endswith(str(self.value))
        
        elif self.operator == QueryOperator.MATCHES:
            return bool(re.match(str(self.value), str(field_value)))
        
        elif self.operator == QueryOperator.EXISTS:
            return self.field in record
        
        return False
    
    def _get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path (e.g., 'user.name')."""
        parts = field_path.split(".")
        value = record
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value


@dataclass
class Query:
    """Dataset query with conditions and operations."""
    
    conditions: List[QueryCondition]
    logical_op: LogicalOperator = LogicalOperator.AND
    projections: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: int = 0
    order_by: Optional[str] = None
    ascending: bool = True
    
    def evaluate(self, record: Dict[str, Any]) -> bool:
        """Evaluate query against a record."""
        if not self.conditions:
            return True
        
        results = [cond.evaluate(record) for cond in self.conditions]
        
        if self.logical_op == LogicalOperator.AND:
            return all(results)
        elif self.logical_op == LogicalOperator.OR:
            return any(results)
        elif self.logical_op == LogicalOperator.NOT:
            return not all(results)
        
        return False
    
    def project(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply projections to record."""
        if not self.projections:
            return record
        
        projected = {}
        for field in self.projections:
            parts = field.split(".")
            value = record
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            projected[field] = value
        
        return projected


class DatasetQueryEngine:
    """Execute queries on datasets."""
    
    def __init__(self):
        """Initialize query engine."""
        self.index_cache: Dict[str, Any] = {}
    
    def execute(
        self,
        dataset_path: Path,
        query: Query,
    ) -> List[Dict[str, Any]]:
        """Execute query on dataset."""
        results = []
        processed_count = 0
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Evaluate query
                if query.evaluate(record):
                    processed_count += 1
                    
                    # Skip offset records
                    if processed_count <= query.offset:
                        continue
                    
                    # Apply projections
                    projected = query.project(record)
                    results.append(projected)
                    
                    # Check limit
                    if query.limit and len(results) >= query.limit:
                        break
        
        # Apply ordering
        if query.order_by:
            results.sort(
                key=lambda r: r.get(query.order_by, ""),
                reverse=not query.ascending,
            )
        
        return results
    
    def count(self, dataset_path: Path, query: Query) -> int:
        """Count records matching query."""
        count = 0
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if query.evaluate(record):
                    count += 1
        
        return count
    
    def aggregate(
        self,
        dataset_path: Path,
        query: Query,
        agg_field: str,
        agg_func: str = "sum",
    ) -> Any:
        """Aggregate values matching query."""
        values = []
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if query.evaluate(record):
                    value = record.get(agg_field)
                    if value is not None:
                        values.append(value)
        
        if not values:
            return None
        
        if agg_func == "sum":
            return sum(values)
        elif agg_func == "avg":
            return sum(values) / len(values)
        elif agg_func == "min":
            return min(values)
        elif agg_func == "max":
            return max(values)
        elif agg_func == "count":
            return len(values)
        
        return None
    
    def group_by(
        self,
        dataset_path: Path,
        query: Query,
        group_field: str,
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """Group records by field value."""
        groups = {}
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if query.evaluate(record):
                    group_value = record.get(group_field)
                    
                    if group_value not in groups:
                        groups[group_value] = []
                    
                    projected = query.project(record)
                    groups[group_value].append(projected)
        
        return groups
    
    def distinct(
        self,
        dataset_path: Path,
        query: Query,
        field: str,
    ) -> List[Any]:
        """Get distinct values for a field."""
        distinct_values = set()
        
        with dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if query.evaluate(record):
                    value = record.get(field)
                    if value is not None:
                        # Convert unhashable types to strings
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value, sort_keys=True)
                        distinct_values.add(value)
        
        return sorted(list(distinct_values))


class QueryBuilder:
    """Builder for constructing queries."""
    
    def __init__(self):
        """Initialize query builder."""
        self.conditions: List[QueryCondition] = []
        self.logical_op = LogicalOperator.AND
        self.projections: Optional[List[str]] = None
        self.limit_val: Optional[int] = None
        self.offset_val: int = 0
        self.order_field: Optional[str] = None
        self.order_asc: bool = True
    
    def where(self, field: str, operator: QueryOperator, value: Any = None) -> "QueryBuilder":
        """Add a condition."""
        self.conditions.append(QueryCondition(field, operator, value))
        return self
    
    def and_(self) -> "QueryBuilder":
        """Use AND for combining conditions."""
        self.logical_op = LogicalOperator.AND
        return self
    
    def or_(self) -> "QueryBuilder":
        """Use OR for combining conditions."""
        self.logical_op = LogicalOperator.OR
        return self
    
    def select(self, *fields: str) -> "QueryBuilder":
        """Add projections."""
        self.projections = list(fields)
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Set limit."""
        self.limit_val = n
        return self
    
    def offset(self, n: int) -> "QueryBuilder":
        """Set offset."""
        self.offset_val = n
        return self
    
    def order_by(self, field: str, ascending: bool = True) -> "QueryBuilder":
        """Set ordering."""
        self.order_field = field
        self.order_asc = ascending
        return self
    
    def build(self) -> Query:
        """Build the query."""
        return Query(
            conditions=self.conditions,
            logical_op=self.logical_op,
            projections=self.projections,
            limit=self.limit_val,
            offset=self.offset_val,
            order_by=self.order_field,
            ascending=self.order_asc,
        )


class QueryParser:
    """Parse query strings into Query objects."""
    
    def __init__(self):
        """Initialize query parser."""
        pass
    
    def parse(self, query_string: str) -> Query:
        """Parse query string (simplified SQL-like syntax)."""
        # This is a simplified parser - production would use a proper parser
        builder = QueryBuilder()
        
        # Parse SELECT clause
        if "SELECT" in query_string:
            select_match = re.search(r"SELECT\s+(.+?)\s+FROM", query_string, re.IGNORECASE)
            if select_match:
                fields = [f.strip() for f in select_match.group(1).split(",")]
                if fields != ["*"]:
                    builder.select(*fields)
        
        # Parse WHERE clause
        if "WHERE" in query_string:
            where_match = re.search(r"WHERE\s+(.+?)(?:ORDER BY|LIMIT|$)", query_string, re.IGNORECASE)
            if where_match:
                conditions_str = where_match.group(1).strip()
                
                # Simple parsing - just handle basic equality
                if "=" in conditions_str and "!=" not in conditions_str:
                    field, value = conditions_str.split("=")
                    field = field.strip()
                    value = value.strip().strip("'\"")
                    
                    builder.where(field, QueryOperator.EQ, value)
        
        # Parse ORDER BY clause
        if "ORDER BY" in query_string:
            order_match = re.search(r"ORDER BY\s+(\w+)(?:\s+(ASC|DESC))?", query_string, re.IGNORECASE)
            if order_match:
                field = order_match.group(1)
                direction = order_match.group(2) or "ASC"
                builder.order_by(field, ascending=(direction.upper() == "ASC"))
        
        # Parse LIMIT clause
        if "LIMIT" in query_string:
            limit_match = re.search(r"LIMIT\s+(\d+)", query_string, re.IGNORECASE)
            if limit_match:
                builder.limit(int(limit_match.group(1)))
        
        return builder.build()
