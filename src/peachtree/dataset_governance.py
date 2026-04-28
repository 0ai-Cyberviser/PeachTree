"""
PeachTree Dataset Governance

Enterprise governance framework for dataset management with role-based access control,
data lifecycle policies, compliance tracking, audit trails, and governance reporting.

Features:
- Role-based access control (RBAC)
- Data classification and labeling
- Lifecycle policy management
- Retention and archival policies
- Compliance framework integration
- Audit trail generation
- Data lineage tracking
- Governance dashboards and reporting
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib


class AccessLevel(Enum):
    """Access control levels"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class DataClassification(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class LifecycleStage(Enum):
    """Data lifecycle stages"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"           # General Data Protection Regulation
    CCPA = "ccpa"           # California Consumer Privacy Act
    HIPAA = "hipaa"         # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"           # Service Organization Control 2
    ISO27001 = "iso27001"   # Information Security Management


@dataclass
class Role:
    """User role definition"""
    role_id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    access_level: AccessLevel = AccessLevel.READ
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions or self.access_level in [AccessLevel.ADMIN, AccessLevel.OWNER]
    
    def grant_permission(self, permission: str) -> None:
        """Grant permission to role"""
        self.permissions.add(permission)
    
    def revoke_permission(self, permission: str) -> None:
        """Revoke permission from role"""
        self.permissions.discard(permission)


@dataclass
class User:
    """User with roles and permissions"""
    user_id: str
    username: str
    email: str
    roles: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


@dataclass
class DataAsset:
    """Governed data asset"""
    asset_id: str
    name: str
    classification: DataClassification
    owner: str
    stewards: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lifecycle_stage: LifecycleStage = LifecycleStage.ACTIVE
    retention_days: Optional[int] = None
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    accessed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def should_archive(self) -> bool:
        """Check if asset should be archived based on retention policy"""
        if not self.retention_days:
            return False
        age_days = (datetime.now() - self.modified_at).days
        return age_days > self.retention_days
    
    def update_access_time(self) -> None:
        """Update last access timestamp"""
        self.accessed_at = datetime.now()


@dataclass
class GovernancePolicy:
    """Governance policy definition"""
    policy_id: str
    name: str
    description: str
    policy_type: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Evaluate policy against context"""
        violations = []
        
        for rule in self.rules:
            rule_type = rule.get("type")
            
            if rule_type == "classification_required":
                if "classification" not in context:
                    violations.append("Data classification is required")
            
            elif rule_type == "retention_limit":
                max_days = rule.get("max_retention_days")
                if context.get("retention_days", 0) > max_days:
                    violations.append(f"Retention period exceeds {max_days} days")
            
            elif rule_type == "owner_required":
                if not context.get("owner"):
                    violations.append("Data owner must be specified")
            
            elif rule_type == "encryption_required":
                classification = context.get("classification")
                if classification in ["CONFIDENTIAL", "RESTRICTED"]:
                    if not context.get("encrypted"):
                        violations.append(f"{classification} data must be encrypted")
        
        return len(violations) == 0, violations


@dataclass
class AuditEvent:
    """Audit trail event"""
    event_id: str
    event_type: str
    user_id: str
    asset_id: Optional[str]
    action: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "asset_id": self.asset_id,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "ip_address": self.ip_address
        }


class GovernanceEngine:
    """Central governance engine for dataset management"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.assets: Dict[str, DataAsset] = {}
        self.policies: Dict[str, GovernancePolicy] = {}
        self.audit_events: List[AuditEvent] = []
        
        # Initialize default roles
        self._initialize_default_roles()
    
    def _initialize_default_roles(self) -> None:
        """Initialize default RBAC roles"""
        default_roles = [
            Role(
                role_id="viewer",
                name="Viewer",
                description="Read-only access to data",
                permissions={"read", "list"},
                access_level=AccessLevel.READ
            ),
            Role(
                role_id="contributor",
                name="Contributor",
                description="Can create and modify data",
                permissions={"read", "write", "create", "update"},
                access_level=AccessLevel.WRITE
            ),
            Role(
                role_id="admin",
                name="Administrator",
                description="Full administrative access",
                permissions={"read", "write", "create", "update", "delete", "manage_users", "manage_policies"},
                access_level=AccessLevel.ADMIN
            )
        ]
        
        for role in default_roles:
            self.roles[role.role_id] = role
    
    def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: Optional[List[str]] = None
    ) -> User:
        """Create new user"""
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles or []
        )
        self.users[user_id] = user
        
        self._audit(
            event_type="user_management",
            user_id="system",
            asset_id=None,
            action="create_user",
            details={"created_user": user_id, "roles": roles}
        )
        
        return user
    
    def grant_role(self, user_id: str, role_id: str) -> None:
        """Grant role to user"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} not found")
        
        user = self.users[user_id]
        if role_id not in user.roles:
            user.roles.append(role_id)
        
        self._audit(
            event_type="access_control",
            user_id="system",
            asset_id=None,
            action="grant_role",
            details={"user": user_id, "role": role_id}
        )
    
    def check_access(
        self,
        user_id: str,
        asset_id: str,
        required_permission: str
    ) -> bool:
        """Check if user has access to perform action on asset"""
        if user_id not in self.users:
            return False
        if asset_id not in self.assets:
            return False
        
        user = self.users[user_id]
        asset = self.assets[asset_id]
        
        # Owner always has access
        if asset.owner == user_id:
            return True
        
        # Check user roles for permission
        for role_id in user.roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                if role.has_permission(required_permission):
                    return True
        
        return False
    
    def register_asset(
        self,
        asset_id: str,
        name: str,
        classification: DataClassification,
        owner: str,
        **kwargs
    ) -> DataAsset:
        """Register new data asset"""
        asset = DataAsset(
            asset_id=asset_id,
            name=name,
            classification=classification,
            owner=owner,
            **kwargs
        )
        self.assets[asset_id] = asset
        
        self._audit(
            event_type="asset_management",
            user_id=owner,
            asset_id=asset_id,
            action="register_asset",
            details={
                "name": name,
                "classification": classification.value
            }
        )
        
        return asset
    
    def classify_asset(
        self,
        asset_id: str,
        classification: DataClassification,
        user_id: str
    ) -> None:
        """Classify or reclassify data asset"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        if not self.check_access(user_id, asset_id, "classify"):
            raise PermissionError(f"User {user_id} lacks classification permission")
        
        asset = self.assets[asset_id]
        old_classification = asset.classification
        asset.classification = classification
        asset.modified_at = datetime.now()
        
        self._audit(
            event_type="classification",
            user_id=user_id,
            asset_id=asset_id,
            action="classify",
            details={
                "old_classification": old_classification.value,
                "new_classification": classification.value
            }
        )
    
    def create_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        policy_type: str,
        rules: List[Dict[str, Any]],
        created_by: str
    ) -> GovernancePolicy:
        """Create governance policy"""
        policy = GovernancePolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            policy_type=policy_type,
            rules=rules,
            created_by=created_by
        )
        self.policies[policy_id] = policy
        
        self._audit(
            event_type="policy_management",
            user_id=created_by,
            asset_id=None,
            action="create_policy",
            details={"policy": policy_id, "type": policy_type}
        )
        
        return policy
    
    def evaluate_policies(
        self,
        asset_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate all active policies against asset"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset = self.assets[asset_id]
        
        # Build evaluation context
        eval_context = context or {}
        eval_context.update({
            "asset_id": asset_id,
            "classification": asset.classification.value,
            "owner": asset.owner,
            "retention_days": asset.retention_days,
            "lifecycle_stage": asset.lifecycle_stage.value
        })
        
        results = {
            "asset_id": asset_id,
            "compliant": True,
            "violations": [],
            "policies_evaluated": []
        }
        
        for policy_id, policy in self.policies.items():
            if not policy.is_active:
                continue
            
            is_compliant, violations = policy.evaluate(eval_context)
            results["policies_evaluated"].append(policy_id)
            
            if not is_compliant:
                results["compliant"] = False
                results["violations"].extend([
                    {"policy": policy_id, "violation": v}
                    for v in violations
                ])
        
        return results
    
    def apply_lifecycle_policies(self) -> Dict[str, List[str]]:
        """Apply lifecycle policies to all assets"""
        results = {
            "archived": [],
            "deleted": [],
            "retained": []
        }
        
        for asset_id, asset in self.assets.items():
            # Archive old assets
            if asset.should_archive() and asset.lifecycle_stage == LifecycleStage.ACTIVE:
                asset.lifecycle_stage = LifecycleStage.ARCHIVED
                results["archived"].append(asset_id)
                
                self._audit(
                    event_type="lifecycle",
                    user_id="system",
                    asset_id=asset_id,
                    action="archive",
                    details={"reason": "retention_policy"}
                )
        
        return results
    
    def _audit(
        self,
        event_type: str,
        user_id: str,
        asset_id: Optional[str],
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Record audit event"""
        event = AuditEvent(
            event_id=hashlib.md5(
                f"{event_type}{user_id}{datetime.now().isoformat()}".encode()
            ).hexdigest(),
            event_type=event_type,
            user_id=user_id,
            asset_id=asset_id,
            action=action,
            details=details
        )
        self.audit_events.append(event)
    
    def get_audit_trail(
        self,
        asset_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Retrieve filtered audit trail"""
        filtered_events = self.audit_events
        
        if asset_id:
            filtered_events = [e for e in filtered_events if e.asset_id == asset_id]
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        
        return filtered_events
    
    def generate_governance_report(self) -> Dict[str, Any]:
        """Generate comprehensive governance report"""
        return {
            "summary": {
                "total_users": len(self.users),
                "active_users": sum(1 for u in self.users.values() if u.is_active),
                "total_assets": len(self.assets),
                "active_policies": sum(1 for p in self.policies.values() if p.is_active),
                "audit_events": len(self.audit_events)
            },
            "assets_by_classification": {
                classification.value: sum(
                    1 for a in self.assets.values() 
                    if a.classification == classification
                )
                for classification in DataClassification
            },
            "assets_by_lifecycle": {
                stage.value: sum(
                    1 for a in self.assets.values() 
                    if a.lifecycle_stage == stage
                )
                for stage in LifecycleStage
            },
            "compliance_coverage": {
                framework.value: sum(
                    1 for a in self.assets.values() 
                    if framework in a.compliance_frameworks
                )
                for framework in ComplianceFramework
            }
        }


# Export public API
__all__ = [
    'AccessLevel',
    'DataClassification',
    'LifecycleStage',
    'ComplianceFramework',
    'Role',
    'User',
    'DataAsset',
    'GovernancePolicy',
    'AuditEvent',
    'GovernanceEngine'
]
