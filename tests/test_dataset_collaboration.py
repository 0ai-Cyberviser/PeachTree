"""Tests for dataset collaboration functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from peachtree.dataset_collaboration import (
    ChangeType,
    CollaboratorInfo,
    DatasetChange,
    DatasetCollaborationEngine,
    ReviewStatus,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_dataset(temp_dir):
    """Create a sample dataset for testing."""
    dataset = temp_dir / "dataset.jsonl"
    records = [
        {"record_id": "rec_001", "content": "Test content 1", "quality_score": 85},
        {"record_id": "rec_002", "content": "Test content 2", "quality_score": 90},
    ]
    with open(dataset, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return dataset


@pytest.fixture
def owner():
    """Create an owner collaborator."""
    return CollaboratorInfo(
        user_id="user_001",
        username="owner",
        email="owner@example.com",
        role="owner",
        joined_at=datetime.utcnow().isoformat() + "Z",
        permissions={"read", "write", "delete", "manage"},
    )


@pytest.fixture
def editor():
    """Create an editor collaborator."""
    return CollaboratorInfo(
        user_id="user_002",
        username="editor",
        email="editor@example.com",
        role="editor",
        joined_at=datetime.utcnow().isoformat() + "Z",
        permissions={"read", "write"},
    )


class TestCollaboratorInfo:
    """Test CollaboratorInfo dataclass."""
    
    def test_collaborator_creation(self):
        """Test creating a collaborator."""
        collab = CollaboratorInfo(
            user_id="test_001",
            username="testuser",
            email="test@example.com",
            role="editor",
            joined_at="2026-04-27T00:00:00Z",
            permissions={"read", "write"},
        )
        
        assert collab.user_id == "test_001"
        assert collab.username == "testuser"
        assert collab.role == "editor"
        assert "read" in collab.permissions
    
    def test_collaborator_to_dict(self):
        """Test converting collaborator to dictionary."""
        collab = CollaboratorInfo(
            user_id="test_001",
            username="testuser",
            email="test@example.com",
            role="viewer",
            joined_at="2026-04-27T00:00:00Z",
            permissions={"read"},
        )
        
        data = collab.to_dict()
        assert data["user_id"] == "test_001"
        assert data["role"] == "viewer"
        assert "read" in data["permissions"]
    
    def test_collaborator_from_dict(self):
        """Test creating collaborator from dictionary."""
        data = {
            "user_id": "test_001",
            "username": "testuser",
            "email": "test@example.com",
            "role": "reviewer",
            "joined_at": "2026-04-27T00:00:00Z",
            "permissions": ["read", "review"],
        }
        
        collab = CollaboratorInfo.from_dict(data)
        assert collab.user_id == "test_001"
        assert collab.role == "reviewer"
        assert "review" in collab.permissions


class TestDatasetChange:
    """Test DatasetChange dataclass."""
    
    def test_change_creation(self):
        """Test creating a dataset change."""
        change = DatasetChange(
            change_id="change_001",
            change_type=ChangeType.RECORD_ADDED,
            author="user_001",
            timestamp="2026-04-27T00:00:00Z",
            record_id="rec_001",
            new_value={"content": "New content"},
            description="Added new record",
        )
        
        assert change.change_id == "change_001"
        assert change.change_type == ChangeType.RECORD_ADDED
        assert change.review_status == ReviewStatus.PENDING
    
    def test_add_comment(self):
        """Test adding comments to a change."""
        change = DatasetChange(
            change_id="change_001",
            change_type=ChangeType.RECORD_MODIFIED,
            author="user_001",
            timestamp="2026-04-27T00:00:00Z",
        )
        
        change.add_comment("user_002", "Looks good!")
        
        assert len(change.comments) == 1
        assert change.comments[0]["author"] == "user_002"
        assert change.comments[0]["text"] == "Looks good!"
    
    def test_change_to_dict(self):
        """Test converting change to dictionary."""
        change = DatasetChange(
            change_id="change_001",
            change_type=ChangeType.RECORD_DELETED,
            author="user_001",
            timestamp="2026-04-27T00:00:00Z",
            record_id="rec_001",
        )
        
        data = change.to_dict()
        assert data["change_id"] == "change_001"
        assert data["change_type"] == "record_deleted"
        assert data["review_status"] == "pending"


class TestDatasetCollaborationEngine:
    """Test DatasetCollaborationEngine class."""
    
    def test_create_session(self, sample_dataset, owner):
        """Test creating a collaboration session."""
        engine = DatasetCollaborationEngine()
        
        session = engine.create_session(sample_dataset, owner)
        
        assert session.session_id is not None
        assert session.dataset_path == str(sample_dataset)
        assert len(session.participants) == 1
        assert session.participants[0].user_id == owner.user_id
    
    def test_add_collaborator(self, sample_dataset, owner, editor):
        """Test adding a collaborator to a session."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        engine.add_collaborator(session.session_id, editor)
        
        updated_session = engine.sessions[session.session_id]
        assert len(updated_session.participants) == 2
        assert updated_session.participants[1].user_id == editor.user_id
    
    def test_remove_collaborator(self, sample_dataset, owner, editor):
        """Test removing a collaborator from a session."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        engine.add_collaborator(session.session_id, editor)
        
        engine.remove_collaborator(session.session_id, editor.user_id)
        
        updated_session = engine.sessions[session.session_id]
        assert len(updated_session.participants) == 1
    
    def test_create_change(self):
        """Test creating a dataset change."""
        engine = DatasetCollaborationEngine()
        
        change = engine.create_change(
            change_type=ChangeType.RECORD_ADDED,
            author="user_001",
            record_id="rec_new",
            new_value={"content": "New record"},
            description="Adding new record",
        )
        
        assert change.change_id is not None
        assert change.change_type == ChangeType.RECORD_ADDED
        assert change.author == "user_001"
    
    def test_record_change(self, sample_dataset, owner):
        """Test recording a change in a session."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        change = engine.create_change(
            change_type=ChangeType.RECORD_MODIFIED,
            author=owner.user_id,
            record_id="rec_001",
        )
        
        engine.record_change(session.session_id, change)
        
        updated_session = engine.sessions[session.session_id]
        assert len(updated_session.changes) == 1
    
    def test_review_change(self, sample_dataset, owner, editor):
        """Test reviewing a change."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        change = engine.create_change(
            change_type=ChangeType.RECORD_ADDED,
            author=owner.user_id,
        )
        engine.record_change(session.session_id, change)
        
        engine.review_change(
            session.session_id,
            change.change_id,
            editor.user_id,
            ReviewStatus.APPROVED,
            "Looks good",
        )
        
        updated_session = engine.sessions[session.session_id]
        reviewed_change = updated_session.changes[0]
        assert reviewed_change.review_status == ReviewStatus.APPROVED
        assert editor.user_id in reviewed_change.reviewers
        assert len(reviewed_change.comments) == 1
    
    def test_get_pending_changes(self, sample_dataset, owner):
        """Test getting pending changes."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        # Add some changes
        for i in range(3):
            change = engine.create_change(
                change_type=ChangeType.RECORD_ADDED,
                author=owner.user_id,
            )
            engine.record_change(session.session_id, change)
        
        # Approve one
        changes = engine.sessions[session.session_id].changes
        engine.review_change(
            session.session_id,
            changes[0].change_id,
            owner.user_id,
            ReviewStatus.APPROVED,
        )
        
        pending = engine.get_pending_changes(session.session_id)
        assert len(pending) == 2
    
    def test_get_changes_by_author(self, sample_dataset, owner, editor):
        """Test getting changes by specific author."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        engine.add_collaborator(session.session_id, editor)
        
        # Add changes from different authors
        for author in [owner.user_id, editor.user_id, owner.user_id]:
            change = engine.create_change(
                change_type=ChangeType.RECORD_ADDED,
                author=author,
            )
            engine.record_change(session.session_id, change)
        
        owner_changes = engine.get_changes_by_author(session.session_id, owner.user_id)
        assert len(owner_changes) == 2
    
    def test_apply_approved_changes(self, sample_dataset, owner):
        """Test applying approved changes to dataset."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        # Add a change and approve it
        change = engine.create_change(
            change_type=ChangeType.RECORD_ADDED,
            author=owner.user_id,
            new_value={"record_id": "rec_003", "content": "New content", "quality_score": 95},
        )
        engine.record_change(session.session_id, change)
        engine.review_change(
            session.session_id,
            change.change_id,
            owner.user_id,
            ReviewStatus.APPROVED,
        )
        
        # Apply changes
        applied_count = engine.apply_approved_changes(session.session_id, sample_dataset)
        
        assert applied_count == 1
        
        # Verify dataset was updated
        with open(sample_dataset) as f:
            records = [json.loads(line) for line in f]
        
        assert len(records) == 3
        assert any(r["record_id"] == "rec_003" for r in records)
    
    def test_merge_sessions(self, sample_dataset, owner):
        """Test merging multiple sessions."""
        engine = DatasetCollaborationEngine()
        
        # Create two sessions
        session1 = engine.create_session(sample_dataset, owner)
        session2 = engine.create_session(sample_dataset, owner)
        
        # Add changes to both
        for session_id in [session1.session_id, session2.session_id]:
            change = engine.create_change(
                change_type=ChangeType.RECORD_ADDED,
                author=owner.user_id,
            )
            engine.record_change(session_id, change)
        
        # Merge into session1
        merged = engine.merge_sessions([session2.session_id], session1.session_id)
        
        assert len(merged.changes) == 2
        assert not engine.sessions[session2.session_id].is_active
    
    def test_get_collaboration_stats(self, sample_dataset, owner, editor):
        """Test getting collaboration statistics."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        engine.add_collaborator(session.session_id, editor)
        
        # Add various changes
        for change_type in [ChangeType.RECORD_ADDED, ChangeType.RECORD_MODIFIED, ChangeType.RECORD_DELETED]:
            change = engine.create_change(
                change_type=change_type,
                author=owner.user_id,
            )
            engine.record_change(session.session_id, change)
        
        stats = engine.get_collaboration_stats(session.session_id)
        
        assert stats["total_participants"] == 2
        assert stats["total_changes"] == 3
        assert stats["pending_changes"] == 3
        assert "changes_by_type" in stats
        assert "changes_by_author" in stats
    
    def test_save_and_load_session(self, sample_dataset, owner, temp_dir):
        """Test saving and loading a session."""
        engine = DatasetCollaborationEngine()
        session = engine.create_session(sample_dataset, owner)
        
        # Add a change
        change = engine.create_change(
            change_type=ChangeType.RECORD_ADDED,
            author=owner.user_id,
        )
        engine.record_change(session.session_id, change)
        
        # Save session
        output = temp_dir / "session.json"
        engine.save_session(session.session_id, output)
        
        assert output.exists()
        
        # Load session
        engine2 = DatasetCollaborationEngine()
        loaded_session = engine2.load_session(output)
        
        assert loaded_session.session_id == session.session_id
        assert len(loaded_session.participants) == 1
        assert len(loaded_session.changes) == 1
