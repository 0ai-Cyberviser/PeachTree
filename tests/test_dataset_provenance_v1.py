"""Tests for dataset_provenance module."""
import json
import pytest
from pathlib import Path
from peachtree.dataset_provenance import (
    ProvenanceTracker,
    ProvenanceEntity,
    ProvenanceActivity,
    ProvenanceAgent,
    ProvenanceRelationship,
    ProvenanceChain,
    ProvenanceEventType,
    EntityType,
    ProvenanceRelation,
    DatasetProvenanceRecorder,
    ProvenanceValidator,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory."""
    storage = tmp_path / "provenance"
    storage.mkdir()
    return storage


@pytest.fixture
def tracker(temp_storage):
    """Create provenance tracker."""
    return ProvenanceTracker(temp_storage / "provenance.json")


@pytest.fixture
def recorder(tracker):
    """Create provenance recorder."""
    return DatasetProvenanceRecorder(tracker)


def test_provenance_tracker_init(temp_storage):
    """Test tracker initialization."""
    tracker = ProvenanceTracker(temp_storage / "prov.json")
    assert tracker.storage_path == temp_storage / "prov.json"
    assert len(tracker.entities) == 0
    assert len(tracker.activities) == 0
    assert len(tracker.agents) == 0


def test_register_entity(tracker):
    """Test entity registration."""
    entity = tracker.register_entity(
        "dataset_1",
        EntityType.DATASET,
        "Test Dataset",
        attributes={"size": 1000},
    )
    
    assert entity.entity_id == "dataset_1"
    assert entity.entity_type == EntityType.DATASET
    assert entity.name == "Test Dataset"
    assert entity.attributes["size"] == 1000
    assert entity.entity_id in tracker.entities


def test_register_activity(tracker):
    """Test activity registration."""
    activity = tracker.register_activity(
        "activity_1",
        ProvenanceEventType.TRANSFORMED,
        agent_id="agent_1",
    )
    
    assert activity.activity_id == "activity_1"
    assert activity.activity_type == ProvenanceEventType.TRANSFORMED
    assert activity.activity_id in tracker.activities


def test_register_agent(tracker):
    """Test agent registration."""
    agent = tracker.register_agent(
        "agent_1",
        "DatasetBuilder",
        agent_type="software",
    )
    
    assert agent.agent_id == "agent_1"
    assert agent.name == "DatasetBuilder"
    assert agent.agent_type == "software"
    assert agent.agent_id in tracker.agents


def test_record_relationship(tracker):
    """Test relationship recording."""
    entity1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    entity2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    
    rel = tracker.add_relationship(
        ProvenanceRelation.WAS_DERIVED_FROM,
        entity1.entity_id,
        entity2.entity_id,
    )
    
    assert rel.from_entity_id == entity1.entity_id
    assert rel.to_entity_id == entity2.entity_id
    assert rel.relation_type == ProvenanceRelation.WAS_DERIVED_FROM


def test_get_ancestors(tracker):
    """Test getting ancestors."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    e3 = tracker.register_entity("e3", EntityType.DATASET, "Dataset 3")
    
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e1.entity_id, e2.entity_id)
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e2.entity_id, e3.entity_id)
    
    ancestors = tracker.get_ancestors(e3.entity_id)
    assert len(ancestors) >= 1
    assert e1.entity_id in [a.entity_id for a in ancestors] or e2.entity_id in [a.entity_id for a in ancestors]


def test_get_descendants(tracker):
    """Test getting descendants."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    e3 = tracker.register_entity("e3", EntityType.DATASET, "Dataset 3")
    
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e1.entity_id, e2.entity_id)
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e2.entity_id, e3.entity_id)
    
    descendants = tracker.get_descendants(e1.entity_id)
    assert len(descendants) >= 1
    assert e2.entity_id in [d.entity_id for d in descendants] or e3.entity_id in [d.entity_id for d in descendants]


def test_get_chain(tracker):
    """Test getting complete provenance chain."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e1.entity_id, e2.entity_id)
    
    chain = tracker.get_chain(e2.entity_id)
    assert chain.root_entity_id == e2.entity_id
    assert len(chain.entities) >= 1
    assert e1.entity_id in [e.entity_id for e in chain.entities]


def test_export_import_provenance(tracker, temp_storage):
    """Test exporting and importing provenance."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e1.entity_id, e2.entity_id)
    
    export_path = temp_storage / "export.json"
    tracker.export_provenance(export_path)
    
    assert export_path.exists()
    
    # Verify export content
    import json
    data = json.loads(export_path.read_text())
    assert len(data["entities"]) == 2
    assert len(data["relationships"]) == 1


def test_provenance_recorder_record_creation(recorder, tmp_path):
    """Test recording dataset creation."""
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"text": "test"}')
    
    dataset_id = recorder.record_creation(
        dataset,
        "builder_agent",
        source_paths=[tmp_path / "source.txt"],
    )
    
    assert dataset_id is not None
    entity = recorder.tracker.get_entity(dataset_id)
    assert entity is not None
    assert entity.entity_type == EntityType.DATASET


def test_provenance_recorder_record_transformation(recorder, tmp_path):
    """Test recording dataset transformation."""
    input_dataset = tmp_path / "input.jsonl"
    output_dataset = tmp_path / "output.jsonl"
    input_dataset.write_text('{"text": "test"}')
    output_dataset.write_text('{"text": "transformed"}')
    
    dataset_id = recorder.record_transformation(
        input_dataset,
        output_dataset,
        "deduplicate",
        "dedup_agent",
    )
    
    assert dataset_id is not None
    entity = recorder.tracker.get_entity(dataset_id)
    assert entity is not None


def test_provenance_validator_validate_chain(tracker):
    """Test provenance chain validation."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e1.entity_id, e2.entity_id)
    
    validator = ProvenanceValidator(tracker)
    result = validator.validate_chain(e2.entity_id)
    
    assert result["valid"]
    assert result["entity_count"] >= 2
    assert result["relationship_count"] >= 1


def test_provenance_validator_check_completeness(tracker):
    """Test integrity checking."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    
    validator = ProvenanceValidator(tracker)
    result = validator.check_integrity()
    
    assert isinstance(result, dict)
    assert "total_entities" in result
    assert result["total_entities"] >= 1


def test_provenance_entity_to_dict():
    """Test entity serialization."""
    from datetime import datetime
    entity = ProvenanceEntity(
        entity_id="e1",
        entity_type=EntityType.DATASET,
        name="Test",
        attributes={},
        created_at=datetime.now(),
    )
    
    data = entity.to_dict()
    assert data["entity_id"] == "e1"
    assert data["entity_type"] == EntityType.DATASET.value
    assert data["name"] == "Test"


def test_provenance_activity_to_dict():
    """Test activity serialization."""
    from datetime import datetime
    activity = ProvenanceActivity(
        activity_id="a1",
        activity_type=ProvenanceEventType.TRANSFORMED,
        started_at=datetime.now(),
        ended_at=None,
        parameters={},
    )
    
    data = activity.to_dict()
    assert data["activity_id"] == "a1"
    assert data["activity_type"] == "transformed"


def test_provenance_agent_to_dict():
    """Test agent serialization."""
    agent = ProvenanceAgent(
        agent_id="ag1",
        name="Builder",
        agent_type="software",
        attributes={},
    )
    
    data = agent.to_dict()
    assert data["agent_id"] == "ag1"
    assert data["name"] == "Builder"


def test_provenance_relationship_to_dict():
    """Test relationship serialization."""
    from datetime import datetime
    rel = ProvenanceRelationship(
        relation_type=ProvenanceRelation.WAS_DERIVED_FROM,
        from_entity_id="e1",
        to_entity_id="e2",
        timestamp=datetime.now(),
        metadata={},
    )
    
    data = rel.to_dict()
    assert data["from_entity_id"] == "e1"
    assert data["to_entity_id"] == "e2"
    assert data["relation_type"] == ProvenanceRelation.WAS_DERIVED_FROM.value


def test_provenance_chain_to_dict(tracker):
    """Test provenance chain serialization."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    chain = tracker.get_chain(e1.entity_id)
    
    data = chain.to_dict()
    assert data["root_entity_id"] == e1.entity_id
    assert "entities" in data
    assert "activities" in data
    assert "relationships" in data


def test_multiple_relationships(tracker):
    """Test multiple relationships from one entity."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    e2 = tracker.register_entity("e2", EntityType.DATASET, "Dataset 2")
    e3 = tracker.register_entity("e3", EntityType.DATASET, "Dataset 3")
    
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e2.entity_id, e1.entity_id)
    tracker.add_relationship(ProvenanceRelation.WAS_DERIVED_FROM, e3.entity_id, e1.entity_id)
    
    ancestors = tracker.get_ancestors(e1.entity_id)
    assert len(ancestors) >= 1


def test_empty_chain(tracker):
    """Test getting chain for entity with no relationships."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    
    chain = tracker.get_chain(e1.entity_id)
    assert chain.root_entity_id == e1.entity_id
    assert len(chain.relationships) == 0


def test_persistence(tracker, temp_storage):
    """Test tracker persistence."""
    e1 = tracker.register_entity("e1", EntityType.DATASET, "Dataset 1")
    tracker._save()
    
    # Create new tracker with same storage
    new_tracker = ProvenanceTracker(tracker.storage_path)
    assert len(new_tracker.entities) == 1
    assert "e1" in new_tracker.entities
