"""Dataset provenance tracking for complete data lineage.

Provides comprehensive provenance tracking with chain of custody,
data origins, transformations, and lineage visualization.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import json


class ProvenanceEventType(Enum):
    """Provenance event types."""
    CREATED = "created"
    MODIFIED = "modified"
    TRANSFORMED = "transformed"
    MERGED = "merged"
    SPLIT = "split"
    FILTERED = "filtered"
    DERIVED = "derived"
    DELETED = "deleted"


class EntityType(Enum):
    """Provenance entity types."""
    DATASET = "dataset"
    RECORD = "record"
    FIELD = "field"
    TRANSFORMATION = "transformation"
    AGENT = "agent"
    ACTIVITY = "activity"


class ProvenanceRelation(Enum):
    """Provenance relationships."""
    WAS_DERIVED_FROM = "wasDerivedFrom"
    WAS_GENERATED_BY = "wasGeneratedBy"
    USED = "used"
    WAS_ATTRIBUTED_TO = "wasAttributedTo"
    WAS_ASSOCIATED_WITH = "wasAssociatedWith"
    ACTED_ON_BEHALF_OF = "actedOnBehalfOf"


@dataclass
class ProvenanceEntity:
    """Provenance entity."""
    entity_id: str
    entity_type: EntityType
    name: str
    created_at: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "attributes": self.attributes,
            "checksum": self.checksum,
        }


@dataclass
class ProvenanceActivity:
    """Provenance activity."""
    activity_id: str
    activity_type: ProvenanceEventType
    started_at: datetime
    ended_at: Optional[datetime] = None
    agent_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "agent_id": self.agent_id,
            "parameters": self.parameters,
        }


@dataclass
class ProvenanceAgent:
    """Provenance agent."""
    agent_id: str
    name: str
    agent_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "attributes": self.attributes,
        }


@dataclass
class ProvenanceRelationship:
    """Provenance relationship between entities."""
    relation_type: ProvenanceRelation
    from_entity_id: str
    to_entity_id: str
    activity_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "relation_type": self.relation_type.value,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "activity_id": self.activity_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
        }


@dataclass
class ProvenanceChain:
    """Complete provenance chain."""
    chain_id: str
    root_entity_id: str
    entities: List[ProvenanceEntity]
    activities: List[ProvenanceActivity]
    relationships: List[ProvenanceRelationship]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_id": self.chain_id,
            "root_entity_id": self.root_entity_id,
            "entities": [e.to_dict() for e in self.entities],
            "activities": [a.to_dict() for a in self.activities],
            "relationships": [r.to_dict() for r in self.relationships],
            "created_at": self.created_at.isoformat(),
        }


class ProvenanceTracker:
    """Track dataset provenance."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize provenance tracker."""
        self.storage_path = storage_path
        self.entities: Dict[str, ProvenanceEntity] = {}
        self.activities: Dict[str, ProvenanceActivity] = {}
        self.agents: Dict[str, ProvenanceAgent] = {}
        self.relationships: List[ProvenanceRelationship] = []
        
        if storage_path and storage_path.exists():
            self._load()
    
    def _load(self) -> None:
        """Load provenance data."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        data = json.loads(self.storage_path.read_text())
        
        for entity_data in data.get("entities", []):
            entity = ProvenanceEntity(
                entity_id=entity_data["entity_id"],
                entity_type=EntityType(entity_data["entity_type"]),
                name=entity_data["name"],
                created_at=datetime.fromisoformat(entity_data["created_at"]),
                attributes=entity_data.get("attributes", {}),
                checksum=entity_data.get("checksum"),
            )
            self.entities[entity.entity_id] = entity
    
    def _save(self) -> None:
        """Save provenance data."""
        if not self.storage_path:
            return
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "activities": [a.to_dict() for a in self.activities.values()],
            "agents": [a.to_dict() for a in self.agents.values()],
            "relationships": [r.to_dict() for r in self.relationships],
            "updated_at": datetime.now().isoformat(),
        }
        
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def register_entity(
        self,
        entity_id: str,
        entity_type: EntityType,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        checksum: Optional[str] = None,
    ) -> ProvenanceEntity:
        """Register a provenance entity."""
        entity = ProvenanceEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            created_at=datetime.now(),
            attributes=attributes or {},
            checksum=checksum,
        )
        
        self.entities[entity_id] = entity
        self._save()
        return entity
    
    def register_activity(
        self,
        activity_id: str,
        activity_type: ProvenanceEventType,
        agent_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceActivity:
        """Register a provenance activity."""
        activity = ProvenanceActivity(
            activity_id=activity_id,
            activity_type=activity_type,
            started_at=datetime.now(),
            agent_id=agent_id,
            parameters=parameters or {},
        )
        
        self.activities[activity_id] = activity
        self._save()
        return activity
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceAgent:
        """Register a provenance agent."""
        agent = ProvenanceAgent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            attributes=attributes or {},
        )
        
        self.agents[agent_id] = agent
        self._save()
        return agent
    
    def add_relationship(
        self,
        relation_type: ProvenanceRelation,
        from_entity_id: str,
        to_entity_id: str,
        activity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRelationship:
        """Add a provenance relationship."""
        relationship = ProvenanceRelationship(
            relation_type=relation_type,
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            activity_id=activity_id,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        self.relationships.append(relationship)
        self._save()
        return relationship
    
    def complete_activity(self, activity_id: str) -> None:
        """Mark activity as completed."""
        if activity_id in self.activities:
            self.activities[activity_id].ended_at = datetime.now()
            self._save()
    
    def get_entity(self, entity_id: str) -> Optional[ProvenanceEntity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_ancestors(self, entity_id: str) -> List[ProvenanceEntity]:
        """Get all ancestor entities."""
        ancestors = []
        visited = set()
        
        def traverse(eid: str):
            if eid in visited:
                return
            visited.add(eid)
            
            for rel in self.relationships:
                if rel.to_entity_id == eid and rel.from_entity_id in self.entities:
                    ancestor = self.entities[rel.from_entity_id]
                    ancestors.append(ancestor)
                    traverse(rel.from_entity_id)
        
        traverse(entity_id)
        return ancestors
    
    def get_descendants(self, entity_id: str) -> List[ProvenanceEntity]:
        """Get all descendant entities."""
        descendants = []
        visited = set()
        
        def traverse(eid: str):
            if eid in visited:
                return
            visited.add(eid)
            
            for rel in self.relationships:
                if rel.from_entity_id == eid and rel.to_entity_id in self.entities:
                    descendant = self.entities[rel.to_entity_id]
                    descendants.append(descendant)
                    traverse(rel.to_entity_id)
        
        traverse(entity_id)
        return descendants
    
    def get_chain(self, entity_id: str) -> ProvenanceChain:
        """Get complete provenance chain for entity."""
        # Collect all related entities
        related_entities = [self.entities[entity_id]]
        related_entities.extend(self.get_ancestors(entity_id))
        related_entities.extend(self.get_descendants(entity_id))
        
        # Get related activities
        entity_ids = {e.entity_id for e in related_entities}
        related_activities = []
        related_relationships = []
        
        for rel in self.relationships:
            if rel.from_entity_id in entity_ids or rel.to_entity_id in entity_ids:
                related_relationships.append(rel)
                if rel.activity_id and rel.activity_id in self.activities:
                    activity = self.activities[rel.activity_id]
                    if activity not in related_activities:
                        related_activities.append(activity)
        
        chain_id = hashlib.sha256(f"{entity_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        return ProvenanceChain(
            chain_id=chain_id,
            root_entity_id=entity_id,
            entities=related_entities,
            activities=related_activities,
            relationships=related_relationships,
            created_at=datetime.now(),
        )
    
    def export_provenance(self, output_path: Path) -> None:
        """Export provenance to file."""
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "activities": [a.to_dict() for a in self.activities.values()],
            "agents": [a.to_dict() for a in self.agents.values()],
            "relationships": [r.to_dict() for r in self.relationships],
            "exported_at": datetime.now().isoformat(),
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))


class DatasetProvenanceRecorder:
    """Record provenance for dataset operations."""
    
    def __init__(self, tracker: ProvenanceTracker):
        """Initialize provenance recorder."""
        self.tracker = tracker
    
    def record_creation(
        self,
        dataset_path: Path,
        agent_id: str,
        source_paths: Optional[List[Path]] = None,
    ) -> str:
        """Record dataset creation."""
        # Register dataset entity
        dataset_id = hashlib.sha256(str(dataset_path).encode()).hexdigest()[:16]
        checksum = self._calculate_checksum(dataset_path)
        
        self.tracker.register_entity(
            dataset_id,
            EntityType.DATASET,
            str(dataset_path),
            attributes={"path": str(dataset_path)},
            checksum=checksum,
        )
        
        # Register creation activity
        activity_id = f"create_{dataset_id}"
        self.tracker.register_activity(
            activity_id,
            ProvenanceEventType.CREATED,
            agent_id=agent_id,
        )
        
        # Link activity to entity
        self.tracker.add_relationship(
            ProvenanceRelation.WAS_GENERATED_BY,
            dataset_id,
            activity_id,
            activity_id=activity_id,
        )
        
        # Link source datasets
        if source_paths:
            for source_path in source_paths:
                source_id = hashlib.sha256(str(source_path).encode()).hexdigest()[:16]
                self.tracker.add_relationship(
                    ProvenanceRelation.WAS_DERIVED_FROM,
                    dataset_id,
                    source_id,
                    activity_id=activity_id,
                )
        
        self.tracker.complete_activity(activity_id)
        return dataset_id
    
    def record_transformation(
        self,
        input_path: Path,
        output_path: Path,
        transformation_name: str,
        agent_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record dataset transformation."""
        input_id = hashlib.sha256(str(input_path).encode()).hexdigest()[:16]
        output_id = hashlib.sha256(str(output_path).encode()).hexdigest()[:16]
        
        # Register output entity
        checksum = self._calculate_checksum(output_path)
        self.tracker.register_entity(
            output_id,
            EntityType.DATASET,
            str(output_path),
            attributes={"path": str(output_path)},
            checksum=checksum,
        )
        
        # Register transformation activity
        activity_id = f"transform_{output_id}"
        self.tracker.register_activity(
            activity_id,
            ProvenanceEventType.TRANSFORMED,
            agent_id=agent_id,
            parameters=parameters or {"transformation": transformation_name},
        )
        
        # Link transformation
        self.tracker.add_relationship(
            ProvenanceRelation.USED,
            activity_id,
            input_id,
            activity_id=activity_id,
        )
        
        self.tracker.add_relationship(
            ProvenanceRelation.WAS_GENERATED_BY,
            output_id,
            activity_id,
            activity_id=activity_id,
        )
        
        self.tracker.complete_activity(activity_id)
        return output_id
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate file checksum."""
        if path.exists():
            return hashlib.sha256(path.read_bytes()).hexdigest()
        return ""


class ProvenanceValidator:
    """Validate provenance chains."""
    
    def __init__(self, tracker: ProvenanceTracker):
        """Initialize validator."""
        self.tracker = tracker
    
    def validate_chain(self, entity_id: str) -> Dict[str, Any]:
        """Validate provenance chain integrity."""
        chain = self.tracker.get_chain(entity_id)
        
        issues = []
        
        # Check for missing entities
        for rel in chain.relationships:
            if rel.from_entity_id not in self.tracker.entities:
                issues.append(f"Missing source entity: {rel.from_entity_id}")
            if rel.to_entity_id not in self.tracker.entities:
                issues.append(f"Missing target entity: {rel.to_entity_id}")
        
        # Check for orphaned activities
        for activity in chain.activities:
            has_relationship = any(
                r.activity_id == activity.activity_id
                for r in chain.relationships
            )
            if not has_relationship:
                issues.append(f"Orphaned activity: {activity.activity_id}")
        
        return {
            "valid": len(issues) == 0,
            "entity_id": entity_id,
            "entity_count": len(chain.entities),
            "activity_count": len(chain.activities),
            "relationship_count": len(chain.relationships),
            "issues": issues,
        }
    
    def check_integrity(self) -> Dict[str, Any]:
        """Check overall provenance integrity."""
        total_entities = len(self.tracker.entities)
        total_activities = len(self.tracker.activities)
        total_relationships = len(self.tracker.relationships)
        
        # Check for broken references
        broken_refs = []
        for rel in self.tracker.relationships:
            if rel.from_entity_id not in self.tracker.entities:
                broken_refs.append(f"Broken from: {rel.from_entity_id}")
            if rel.to_entity_id not in self.tracker.entities:
                broken_refs.append(f"Broken to: {rel.to_entity_id}")
        
        return {
            "total_entities": total_entities,
            "total_activities": total_activities,
            "total_relationships": total_relationships,
            "broken_references": len(broken_refs),
            "integrity_score": 1.0 - (len(broken_refs) / max(total_relationships, 1)),
            "issues": broken_refs[:10],  # First 10 issues
        }
