"""
Advanced Data Lineage Tracking and Analysis

Provides comprehensive data lineage tracking with:
- Multi-level lineage graph construction
- Impact analysis and dependency mapping
- Lineage visualization and export
- Column-level lineage tracking
- Transformation provenance
- Compliance and audit trail integration

Example:
    >>> from peachtree.dataset_lineage_v2 import LineageTracker, LineageGraph
    >>> 
    >>> # Initialize tracker
    >>> tracker = LineageTracker()
    >>> 
    >>> # Track transformation
    >>> tracker.track_transformation(
    ...     source="raw_data.csv",
    ...     target="cleaned_data.csv",
    ...     operation="clean_nulls"
    ... )
    >>> 
    >>> # Analyze impact
    >>> impact = tracker.analyze_impact("raw_data.csv")
    >>> print(f"Affected datasets: {len(impact.downstream)}")
"""

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import hashlib


class LineageType(Enum):
    """Types of lineage relationships"""
    DERIVED_FROM = "derived_from"
    TRANSFORMED_TO = "transformed_to"
    MERGED_WITH = "merged_with"
    SPLIT_INTO = "split_into"
    AGGREGATED_FROM = "aggregated_from"
    FILTERED_FROM = "filtered_from"


class EntityType(Enum):
    """Types of lineage entities"""
    DATASET = "dataset"
    TABLE = "table"
    COLUMN = "column"
    FIELD = "field"
    TRANSFORMATION = "transformation"
    OPERATION = "operation"


@dataclass
class LineageEntity:
    """Represents an entity in the lineage graph"""
    
    entity_id: str
    entity_type: EntityType
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    
    def get_hash(self) -> str:
        """Generate unique hash for entity"""
        content = f"{self.entity_id}:{self.entity_type.value}:{self.name}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'tags': list(self.tags),
            'hash': self.get_hash()
        }


@dataclass
class LineageRelationship:
    """Represents a relationship between lineage entities"""
    
    source_id: str
    target_id: str
    relationship_type: LineageType
    operation: Optional[str] = None
    transformation_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type.value,
            'operation': self.operation,
            'transformation_code': self.transformation_code,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'confidence': self.confidence
        }


class LineageGraph:
    """Graph structure for lineage tracking"""
    
    def __init__(self):
        self.entities: Dict[str, LineageEntity] = {}
        self.relationships: List[LineageRelationship] = []
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
    
    def add_entity(self, entity: LineageEntity) -> None:
        """Add entity to graph"""
        self.entities[entity.entity_id] = entity
        if entity.entity_id not in self.adjacency_list:
            self.adjacency_list[entity.entity_id] = []
        if entity.entity_id not in self.reverse_adjacency:
            self.reverse_adjacency[entity.entity_id] = []
    
    def add_relationship(self, relationship: LineageRelationship) -> None:
        """Add relationship to graph"""
        self.relationships.append(relationship)
        self.adjacency_list[relationship.source_id].append(relationship.target_id)
        self.reverse_adjacency[relationship.target_id].append(relationship.source_id)
    
    def get_descendants(self, entity_id: str, max_depth: int = -1) -> Set[str]:
        """Get all descendant entities (downstream)"""
        descendants = set()
        queue = deque([(entity_id, 0)])
        visited = {entity_id}
        
        while queue:
            current_id, depth = queue.popleft()
            
            if max_depth >= 0 and depth >= max_depth:
                continue
            
            for child_id in self.adjacency_list.get(current_id, []):
                if child_id not in visited:
                    visited.add(child_id)
                    descendants.add(child_id)
                    queue.append((child_id, depth + 1))
        
        return descendants
    
    def get_ancestors(self, entity_id: str, max_depth: int = -1) -> Set[str]:
        """Get all ancestor entities (upstream)"""
        ancestors = set()
        queue = deque([(entity_id, 0)])
        visited = {entity_id}
        
        while queue:
            current_id, depth = queue.popleft()
            
            if max_depth >= 0 and depth >= max_depth:
                continue
            
            for parent_id in self.reverse_adjacency.get(current_id, []):
                if parent_id not in visited:
                    visited.add(parent_id)
                    ancestors.add(parent_id)
                    queue.append((parent_id, depth + 1))
        
        return ancestors
    
    def get_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between two entities using BFS"""
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
            
            for child_id in self.adjacency_list.get(current_id, []):
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, path + [child_id]))
        
        return None
    
    def find_cycles(self) -> List[List[str]]:
        """Detect cycles in lineage graph"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for child_id in self.adjacency_list.get(node_id, []):
                if child_id not in visited:
                    dfs(child_id, path + [child_id])
                elif child_id in rec_stack:
                    # Found cycle
                    cycle_start = path.index(child_id)
                    cycles.append(path[cycle_start:] + [child_id])
            
            rec_stack.remove(node_id)
        
        for entity_id in self.entities:
            if entity_id not in visited:
                dfs(entity_id, [entity_id])
        
        return cycles
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            'num_entities': len(self.entities),
            'num_relationships': len(self.relationships),
            'entity_types': {
                etype.value: sum(1 for e in self.entities.values() if e.entity_type == etype)
                for etype in EntityType
            },
            'relationship_types': {
                rtype.value: sum(1 for r in self.relationships if r.relationship_type == rtype)
                for rtype in LineageType
            }
        }


@dataclass
class ImpactAnalysis:
    """Results of impact analysis"""
    
    entity_id: str
    upstream: Set[str] = field(default_factory=set)
    downstream: Set[str] = field(default_factory=set)
    affected_entities: Set[str] = field(default_factory=set)
    critical_paths: List[List[str]] = field(default_factory=list)
    risk_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'entity_id': self.entity_id,
            'upstream_count': len(self.upstream),
            'downstream_count': len(self.downstream),
            'affected_count': len(self.affected_entities),
            'critical_paths_count': len(self.critical_paths),
            'risk_score': self.risk_score,
            'upstream': list(self.upstream),
            'downstream': list(self.downstream),
            'affected_entities': list(self.affected_entities)
        }


class LineageTracker:
    """Main lineage tracking engine"""
    
    def __init__(self, enable_column_lineage: bool = True):
        self.graph = LineageGraph()
        self.enable_column_lineage = enable_column_lineage
        self.tracking_enabled = True
        self.events: List[Dict[str, Any]] = []
    
    def track_transformation(
        self,
        source: str,
        target: str,
        operation: str,
        transformation_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a data transformation
        
        Args:
            source: Source entity identifier
            target: Target entity identifier
            operation: Operation name
            transformation_code: Optional transformation code
            metadata: Optional metadata
            
        Returns:
            Relationship ID
        """
        if not self.tracking_enabled:
            return ""
        
        # Create entities if they don't exist
        if source not in self.graph.entities:
            source_entity = LineageEntity(
                entity_id=source,
                entity_type=EntityType.DATASET,
                name=source
            )
            self.graph.add_entity(source_entity)
        
        if target not in self.graph.entities:
            target_entity = LineageEntity(
                entity_id=target,
                entity_type=EntityType.DATASET,
                name=target
            )
            self.graph.add_entity(target_entity)
        
        # Create relationship
        relationship = LineageRelationship(
            source_id=source,
            target_id=target,
            relationship_type=LineageType.TRANSFORMED_TO,
            operation=operation,
            transformation_code=transformation_code,
            metadata=metadata or {}
        )
        self.graph.add_relationship(relationship)
        
        # Log event
        self.events.append({
            'type': 'transformation',
            'source': source,
            'target': target,
            'operation': operation,
            'timestamp': time.time()
        })
        
        return f"{source}→{target}"
    
    def track_column_lineage(
        self,
        source_table: str,
        source_column: str,
        target_table: str,
        target_column: str,
        transformation: Optional[str] = None
    ) -> str:
        """
        Track column-level lineage
        
        Args:
            source_table: Source table name
            source_column: Source column name
            target_table: Target table name
            target_column: Target column name
            transformation: Optional transformation expression
            
        Returns:
            Relationship ID
        """
        if not self.enable_column_lineage:
            return ""
        
        # Create column entities
        source_col_id = f"{source_table}.{source_column}"
        target_col_id = f"{target_table}.{target_column}"
        
        source_entity = LineageEntity(
            entity_id=source_col_id,
            entity_type=EntityType.COLUMN,
            name=source_column,
            metadata={'table': source_table}
        )
        target_entity = LineageEntity(
            entity_id=target_col_id,
            entity_type=EntityType.COLUMN,
            name=target_column,
            metadata={'table': target_table}
        )
        
        self.graph.add_entity(source_entity)
        self.graph.add_entity(target_entity)
        
        # Create relationship
        relationship = LineageRelationship(
            source_id=source_col_id,
            target_id=target_col_id,
            relationship_type=LineageType.DERIVED_FROM,
            transformation_code=transformation
        )
        self.graph.add_relationship(relationship)
        
        return f"{source_col_id}→{target_col_id}"
    
    def analyze_impact(
        self,
        entity_id: str,
        include_upstream: bool = True,
        include_downstream: bool = True,
        max_depth: int = -1
    ) -> ImpactAnalysis:
        """
        Analyze impact of changes to an entity
        
        Args:
            entity_id: Entity to analyze
            include_upstream: Include upstream dependencies
            include_downstream: Include downstream dependencies
            max_depth: Maximum depth to traverse (-1 for unlimited)
            
        Returns:
            Impact analysis results
        """
        analysis = ImpactAnalysis(entity_id=entity_id)
        
        if include_upstream:
            analysis.upstream = self.graph.get_ancestors(entity_id, max_depth)
        
        if include_downstream:
            analysis.downstream = self.graph.get_descendants(entity_id, max_depth)
        
        analysis.affected_entities = analysis.upstream | analysis.downstream
        
        # Calculate risk score based on number of affected entities
        analysis.risk_score = min(len(analysis.affected_entities) / 100.0, 1.0)
        
        # Find critical paths (paths to most downstream entities)
        leaf_nodes = [
            eid for eid in analysis.downstream
            if not self.graph.adjacency_list.get(eid, [])
        ]
        
        for leaf_id in leaf_nodes[:10]:  # Limit to 10 critical paths
            path = self.graph.get_path(entity_id, leaf_id)
            if path:
                analysis.critical_paths.append(path)
        
        return analysis
    
    def get_lineage_chain(self, entity_id: str, direction: str = "both") -> List[str]:
        """
        Get full lineage chain for an entity
        
        Args:
            entity_id: Entity identifier
            direction: 'upstream', 'downstream', or 'both'
            
        Returns:
            List of entity IDs in lineage chain
        """
        chain = [entity_id]
        
        if direction in ("upstream", "both"):
            ancestors = self.graph.get_ancestors(entity_id)
            chain = list(ancestors) + chain
        
        if direction in ("downstream", "both"):
            descendants = self.graph.get_descendants(entity_id)
            chain = chain + list(descendants)
        
        return chain
    
    def export_to_dot(self, output_path: Path) -> None:
        """
        Export lineage graph to Graphviz DOT format
        
        Args:
            output_path: Path to output DOT file
        """
        lines = ["digraph lineage {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        
        # Add nodes
        for entity in self.graph.entities.values():
            label = entity.name
            color = {
                EntityType.DATASET: "lightblue",
                EntityType.TABLE: "lightgreen",
                EntityType.COLUMN: "lightyellow",
                EntityType.TRANSFORMATION: "lightpink"
            }.get(entity.entity_type, "white")
            
            lines.append(f'  "{entity.entity_id}" [label="{label}", fillcolor="{color}", style=filled];')
        
        # Add edges
        for rel in self.graph.relationships:
            label = rel.operation or rel.relationship_type.value
            lines.append(f'  "{rel.source_id}" -> "{rel.target_id}" [label="{label}"];')
        
        lines.append("}")
        
        output_path.write_text("\n".join(lines))
    
    def export_to_json(self, output_path: Path) -> None:
        """
        Export lineage graph to JSON format
        
        Args:
            output_path: Path to output JSON file
        """
        data = {
            'entities': [e.to_dict() for e in self.graph.entities.values()],
            'relationships': [r.to_dict() for r in self.graph.relationships],
            'stats': self.graph.get_stats(),
            'exported_at': time.time()
        }
        
        output_path.write_text(json.dumps(data, indent=2))
    
    def validate_lineage(self) -> Dict[str, Any]:
        """
        Validate lineage graph for issues
        
        Returns:
            Validation report
        """
        issues = []
        
        # Check for cycles
        cycles = self.graph.find_cycles()
        if cycles:
            issues.append({
                'type': 'cycle_detected',
                'severity': 'warning',
                'count': len(cycles),
                'examples': cycles[:3]
            })
        
        # Check for orphaned entities
        orphans = [
            eid for eid in self.graph.entities
            if not self.graph.adjacency_list.get(eid) and not self.graph.reverse_adjacency.get(eid)
        ]
        if orphans:
            issues.append({
                'type': 'orphaned_entities',
                'severity': 'info',
                'count': len(orphans),
                'entities': orphans[:10]
            })
        
        # Check for missing entities in relationships
        missing = []
        for rel in self.graph.relationships:
            if rel.source_id not in self.graph.entities:
                missing.append(rel.source_id)
            if rel.target_id not in self.graph.entities:
                missing.append(rel.target_id)
        
        if missing:
            issues.append({
                'type': 'missing_entities',
                'severity': 'error',
                'count': len(set(missing)),
                'entities': list(set(missing))[:10]
            })
        
        return {
            'valid': len([i for i in issues if i['severity'] == 'error']) == 0,
            'issue_count': len(issues),
            'issues': issues,
            'stats': self.graph.get_stats()
        }
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get lineage tracking statistics"""
        return {
            'tracking_enabled': self.tracking_enabled,
            'column_lineage_enabled': self.enable_column_lineage,
            'total_events': len(self.events),
            'graph_stats': self.graph.get_stats()
        }


# Public API
__all__ = [
    'LineageTracker',
    'LineageGraph',
    'LineageEntity',
    'LineageRelationship',
    'ImpactAnalysis',
    'LineageType',
    'EntityType'
]
