"""Dataset collaboration engine for multi-user workflows."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ChangeType(Enum):
    """Types of dataset changes."""
    
    RECORD_ADDED = "record_added"
    RECORD_MODIFIED = "record_modified"
    RECORD_DELETED = "record_deleted"
    METADATA_UPDATED = "metadata_updated"
    QUALITY_IMPROVED = "quality_improved"


class ReviewStatus(Enum):
    """Status of a change review."""
    
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class CollaboratorInfo:
    """Information about a dataset collaborator."""
    
    user_id: str
    username: str
    email: str
    role: str  # owner, editor, reviewer, viewer
    joined_at: str
    permissions: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "joined_at": self.joined_at,
            "permissions": list(self.permissions),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollaboratorInfo":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            role=data["role"],
            joined_at=data["joined_at"],
            permissions=set(data.get("permissions", [])),
        )


@dataclass
class DatasetChange:
    """Represents a change to a dataset."""
    
    change_id: str
    change_type: ChangeType
    author: str
    timestamp: str
    record_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    description: str = ""
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewers: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "author": self.author,
            "timestamp": self.timestamp,
            "record_id": self.record_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "description": self.description,
            "review_status": self.review_status.value,
            "reviewers": self.reviewers,
            "comments": self.comments,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetChange":
        """Create from dictionary."""
        return cls(
            change_id=data["change_id"],
            change_type=ChangeType(data["change_type"]),
            author=data["author"],
            timestamp=data["timestamp"],
            record_id=data.get("record_id"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            description=data.get("description", ""),
            review_status=ReviewStatus(data.get("review_status", "pending")),
            reviewers=data.get("reviewers", []),
            comments=data.get("comments", []),
        )
    
    def add_comment(self, author: str, text: str) -> None:
        """Add a comment to this change."""
        comment = {
            "author": author,
            "text": text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.comments.append(comment)


@dataclass
class CollaborationSession:
    """A collaborative editing session."""
    
    session_id: str
    dataset_path: str
    participants: List[CollaboratorInfo]
    changes: List[DatasetChange]
    created_at: str
    updated_at: str
    is_active: bool = True
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "session_id": self.session_id,
            "dataset_path": self.dataset_path,
            "participants": [p.to_dict() for p in self.participants],
            "changes": [c.to_dict() for c in self.changes],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
        }, indent=2)


class DatasetCollaborationEngine:
    """Engine for managing collaborative dataset workflows."""
    
    def __init__(self):
        """Initialize the collaboration engine."""
        self.sessions: Dict[str, CollaborationSession] = {}
        self.collaborators: Dict[str, CollaboratorInfo] = {}
    
    def create_session(
        self,
        dataset_path: Path,
        owner: CollaboratorInfo,
    ) -> CollaborationSession:
        """Create a new collaboration session."""
        session_id = self._generate_session_id(str(dataset_path))
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        session = CollaborationSession(
            session_id=session_id,
            dataset_path=str(dataset_path),
            participants=[owner],
            changes=[],
            created_at=timestamp,
            updated_at=timestamp,
        )
        
        self.sessions[session_id] = session
        self.collaborators[owner.user_id] = owner
        
        return session
    
    def add_collaborator(
        self,
        session_id: str,
        collaborator: CollaboratorInfo,
    ) -> None:
        """Add a collaborator to a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session.participants.append(collaborator)
        session.updated_at = datetime.utcnow().isoformat() + "Z"
        
        self.collaborators[collaborator.user_id] = collaborator
    
    def remove_collaborator(
        self,
        session_id: str,
        user_id: str,
    ) -> None:
        """Remove a collaborator from a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session.participants = [p for p in session.participants if p.user_id != user_id]
        session.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def record_change(
        self,
        session_id: str,
        change: DatasetChange,
    ) -> None:
        """Record a change in a collaboration session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session.changes.append(change)
        session.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def create_change(
        self,
        change_type: ChangeType,
        author: str,
        record_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> DatasetChange:
        """Create a new dataset change."""
        change_id = self._generate_change_id(author, change_type)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return DatasetChange(
            change_id=change_id,
            change_type=change_type,
            author=author,
            timestamp=timestamp,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            description=description,
        )
    
    def review_change(
        self,
        session_id: str,
        change_id: str,
        reviewer: str,
        status: ReviewStatus,
        comment: str = "",
    ) -> None:
        """Review a change in a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # Find the change
        change = None
        for c in session.changes:
            if c.change_id == change_id:
                change = c
                break
        
        if not change:
            raise ValueError(f"Change {change_id} not found")
        
        # Update review status
        change.review_status = status
        if reviewer not in change.reviewers:
            change.reviewers.append(reviewer)
        
        if comment:
            change.add_comment(reviewer, comment)
        
        session.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def get_pending_changes(
        self,
        session_id: str,
    ) -> List[DatasetChange]:
        """Get all pending changes in a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        return [c for c in session.changes if c.review_status == ReviewStatus.PENDING]
    
    def get_changes_by_author(
        self,
        session_id: str,
        author: str,
    ) -> List[DatasetChange]:
        """Get all changes by a specific author."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        return [c for c in session.changes if c.author == author]
    
    def apply_approved_changes(
        self,
        session_id: str,
        dataset_path: Path,
    ) -> int:
        """Apply all approved changes to a dataset."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        approved = [c for c in session.changes if c.review_status == ReviewStatus.APPROVED]
        
        # Load dataset
        records = []
        if dataset_path.exists():
            with open(dataset_path, encoding="utf-8") as f:
                for line in f:
                    records.append(json.loads(line))
        
        # Apply changes
        records_dict = {r.get("record_id"): r for r in records}
        
        for change in approved:
            if change.change_type == ChangeType.RECORD_ADDED:
                if change.new_value:
                    records_dict[change.new_value.get("record_id")] = change.new_value
            
            elif change.change_type == ChangeType.RECORD_MODIFIED:
                if change.record_id and change.new_value:
                    records_dict[change.record_id] = change.new_value
            
            elif change.change_type == ChangeType.RECORD_DELETED:
                if change.record_id and change.record_id in records_dict:
                    del records_dict[change.record_id]
        
        # Write back
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dataset_path, "w", encoding="utf-8") as f:
            for record in records_dict.values():
                f.write(json.dumps(record) + "\n")
        
        return len(approved)
    
    def merge_sessions(
        self,
        session_ids: List[str],
        target_session_id: str,
    ) -> CollaborationSession:
        """Merge multiple sessions into one."""
        if target_session_id not in self.sessions:
            raise ValueError(f"Target session {target_session_id} not found")
        
        target = self.sessions[target_session_id]
        
        for session_id in session_ids:
            if session_id == target_session_id:
                continue
            
            if session_id not in self.sessions:
                continue
            
            source = self.sessions[session_id]
            
            # Merge participants
            for participant in source.participants:
                if participant.user_id not in [p.user_id for p in target.participants]:
                    target.participants.append(participant)
            
            # Merge changes
            target.changes.extend(source.changes)
            
            # Mark source as inactive
            source.is_active = False
        
        target.updated_at = datetime.utcnow().isoformat() + "Z"
        return target
    
    def get_collaboration_stats(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """Get statistics for a collaboration session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        stats = {
            "total_participants": len(session.participants),
            "total_changes": len(session.changes),
            "pending_changes": len([c for c in session.changes if c.review_status == ReviewStatus.PENDING]),
            "approved_changes": len([c for c in session.changes if c.review_status == ReviewStatus.APPROVED]),
            "rejected_changes": len([c for c in session.changes if c.review_status == ReviewStatus.REJECTED]),
            "changes_by_type": {},
            "changes_by_author": {},
        }
        
        # Count by type
        for change in session.changes:
            type_name = change.change_type.value
            stats["changes_by_type"][type_name] = stats["changes_by_type"].get(type_name, 0) + 1
        
        # Count by author
        for change in session.changes:
            stats["changes_by_author"][change.author] = stats["changes_by_author"].get(change.author, 0) + 1
        
        return stats
    
    def save_session(
        self,
        session_id: str,
        output_path: Path,
    ) -> None:
        """Save a collaboration session to file."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(session.to_json() + "\n", encoding="utf-8")
    
    def load_session(
        self,
        input_path: Path,
    ) -> CollaborationSession:
        """Load a collaboration session from file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        
        session = CollaborationSession(
            session_id=data["session_id"],
            dataset_path=data["dataset_path"],
            participants=[CollaboratorInfo.from_dict(p) for p in data["participants"]],
            changes=[DatasetChange.from_dict(c) for c in data["changes"]],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            is_active=data.get("is_active", True),
        )
        
        self.sessions[session.session_id] = session
        return session
    
    def _generate_session_id(self, dataset_path: str) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        data = f"{dataset_path}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_change_id(self, author: str, change_type: ChangeType) -> str:
        """Generate a unique change ID."""
        timestamp = datetime.utcnow().isoformat()
        data = f"{author}:{change_type.value}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
