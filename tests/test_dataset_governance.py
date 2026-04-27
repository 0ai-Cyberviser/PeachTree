"""
Tests for dataset_governance module - Enterprise governance framework
"""

import pytest
from datetime import datetime, timedelta
from peachtree.dataset_governance import (
    AccessLevel, DataClassification, LifecycleStage, ComplianceFramework,
    Role, User, DataAsset, GovernancePolicy, AuditEvent, GovernanceEngine
)


class TestRole:
    def test_role_creation(self):
        role = Role(
            role_id="viewer",
            name="Viewer",
            description="Read-only access",
            permissions={"read", "list"},
            access_level=AccessLevel.READ
        )
        assert role.role_id == "viewer"
        assert role.name == "Viewer"
        assert "read" in role.permissions
        assert role.access_level == AccessLevel.READ
    
    def test_role_has_permission(self):
        role = Role(
            role_id="contributor",
            name="Contributor",
            description="Can write",
            permissions={"read", "write"},
            access_level=AccessLevel.WRITE
        )
        assert role.has_permission("read")
        assert role.has_permission("write")
        assert not role.has_permission("delete")
    
    def test_admin_role_has_all_permissions(self):
        role = Role(
            role_id="admin",
            name="Admin",
            description="Administrator",
            access_level=AccessLevel.ADMIN
        )
        assert role.has_permission("any_permission")
    
    def test_grant_revoke_permission(self):
        role = Role(
            role_id="custom",
            name="Custom",
            description="Custom role",
            access_level=AccessLevel.READ
        )
        
        role.grant_permission("custom_perm")
        assert role.has_permission("custom_perm")
        
        role.revoke_permission("custom_perm")
        assert not role.has_permission("custom_perm")


class TestUser:
    def test_user_creation(self):
        user = User(
            user_id="user1",
            username="testuser",
            email="test@example.com",
            roles=["viewer"]
        )
        assert user.user_id == "user1"
        assert user.username == "testuser"
        assert user.is_active
        assert "viewer" in user.roles
    
    def test_user_to_dict(self):
        user = User(
            user_id="user1",
            username="testuser",
            email="test@example.com"
        )
        user_dict = user.to_dict()
        
        assert user_dict["user_id"] == "user1"
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["is_active"] is True


class TestDataAsset:
    def test_asset_creation(self):
        asset = DataAsset(
            asset_id="asset1",
            name="Test Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1",
            stewards=["user2"],
            tags=["ml", "training"]
        )
        assert asset.asset_id == "asset1"
        assert asset.name == "Test Dataset"
        assert asset.classification == DataClassification.INTERNAL
        assert asset.owner == "user1"
        assert "ml" in asset.tags
    
    def test_asset_retention_check(self):
        # Asset modified 100 days ago with 30 day retention
        old_date = datetime.now() - timedelta(days=100)
        asset = DataAsset(
            asset_id="asset1",
            name="Old Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1",
            retention_days=30,
            modified_at=old_date
        )
        assert asset.should_archive()
    
    def test_asset_not_ready_for_archive(self):
        # Asset modified 10 days ago with 30 day retention
        recent_date = datetime.now() - timedelta(days=10)
        asset = DataAsset(
            asset_id="asset1",
            name="Recent Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1",
            retention_days=30,
            modified_at=recent_date
        )
        assert not asset.should_archive()
    
    def test_asset_update_access_time(self):
        asset = DataAsset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.PUBLIC,
            owner="user1"
        )
        assert asset.accessed_at is None
        asset.update_access_time()
        assert asset.accessed_at is not None


class TestGovernancePolicy:
    def test_policy_creation(self):
        policy = GovernancePolicy(
            policy_id="pol1",
            name="Classification Policy",
            description="Require classification",
            policy_type="data_quality",
            rules=[{"type": "classification_required"}]
        )
        assert policy.policy_id == "pol1"
        assert policy.is_active
        assert len(policy.rules) == 1
    
    def test_policy_evaluation_classification_required(self):
        policy = GovernancePolicy(
            policy_id="pol1",
            name="Test",
            description="",
            policy_type="data_quality",
            rules=[{"type": "classification_required"}]
        )
        
        # Missing classification
        is_compliant, violations = policy.evaluate({})
        assert not is_compliant
        assert len(violations) > 0
        
        # With classification
        is_compliant, violations = policy.evaluate({"classification": "INTERNAL"})
        assert is_compliant
        assert len(violations) == 0
    
    def test_policy_evaluation_retention_limit(self):
        policy = GovernancePolicy(
            policy_id="pol1",
            name="Retention Policy",
            description="",
            policy_type="retention",
            rules=[{"type": "retention_limit", "max_retention_days": 365}]
        )
        
        # Exceeds limit
        is_compliant, violations = policy.evaluate({"retention_days": 730})
        assert not is_compliant
        assert "Retention period exceeds" in violations[0]
        
        # Within limit
        is_compliant, violations = policy.evaluate({"retention_days": 180})
        assert is_compliant
    
    def test_policy_evaluation_encryption_required(self):
        policy = GovernancePolicy(
            policy_id="pol1",
            name="Encryption Policy",
            description="",
            policy_type="security",
            rules=[{"type": "encryption_required"}]
        )
        
        # Confidential data without encryption
        is_compliant, violations = policy.evaluate({
            "classification": "CONFIDENTIAL",
            "encrypted": False
        })
        assert not is_compliant
        assert "must be encrypted" in violations[0]
        
        # Confidential data with encryption
        is_compliant, violations = policy.evaluate({
            "classification": "CONFIDENTIAL",
            "encrypted": True
        })
        assert is_compliant


class TestAuditEvent:
    def test_audit_event_creation(self):
        event = AuditEvent(
            event_id="evt1",
            event_type="access",
            user_id="user1",
            asset_id="asset1",
            action="read",
            details={"success": True}
        )
        assert event.event_id == "evt1"
        assert event.action == "read"
    
    def test_audit_event_to_dict(self):
        event = AuditEvent(
            event_id="evt1",
            event_type="access",
            user_id="user1",
            asset_id="asset1",
            action="read"
        )
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == "evt1"
        assert event_dict["user_id"] == "user1"
        assert event_dict["action"] == "read"


class TestGovernanceEngine:
    def test_engine_initialization(self):
        engine = GovernanceEngine()
        assert len(engine.roles) == 3  # Default roles: viewer, contributor, admin
        assert "viewer" in engine.roles
        assert "contributor" in engine.roles
        assert "admin" in engine.roles
    
    def test_create_user(self):
        engine = GovernanceEngine()
        user = engine.create_user(
            user_id="user1",
            username="testuser",
            email="test@example.com",
            roles=["viewer"]
        )
        
        assert "user1" in engine.users
        assert user.username == "testuser"
        assert "viewer" in user.roles
        assert len(engine.audit_events) > 0  # Audit event recorded
    
    def test_grant_role(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "testuser", "test@example.com")
        engine.grant_role("user1", "contributor")
        
        assert "contributor" in engine.users["user1"].roles
    
    def test_grant_role_invalid_user(self):
        engine = GovernanceEngine()
        with pytest.raises(ValueError):
            engine.grant_role("nonexistent", "viewer")
    
    def test_register_asset(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "owner", "owner@example.com")
        
        asset = engine.register_asset(
            asset_id="asset1",
            name="Test Dataset",
            classification=DataClassification.CONFIDENTIAL,
            owner="user1",
            tags=["ml"]
        )
        
        assert "asset1" in engine.assets
        assert asset.name == "Test Dataset"
        assert asset.classification == DataClassification.CONFIDENTIAL
    
    def test_check_access_owner(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "owner", "owner@example.com")
        engine.register_asset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1"
        )
        
        # Owner always has access
        assert engine.check_access("user1", "asset1", "any_permission")
    
    def test_check_access_with_role(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "viewer", "viewer@example.com", roles=["viewer"])
        engine.create_user("user2", "owner", "owner@example.com")
        engine.register_asset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.INTERNAL,
            owner="user2"
        )
        
        # Viewer has read permission
        assert engine.check_access("user1", "asset1", "read")
        # Viewer does not have delete permission
        assert not engine.check_access("user1", "asset1", "delete")
    
    def test_classify_asset(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "owner", "owner@example.com", roles=["admin"])
        engine.register_asset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1"
        )
        
        # Admin can classify (has all permissions)
        engine.classify_asset("asset1", DataClassification.CONFIDENTIAL, "user1")
        assert engine.assets["asset1"].classification == DataClassification.CONFIDENTIAL
    
    def test_create_policy(self):
        engine = GovernanceEngine()
        engine.create_user("admin1", "admin", "admin@example.com")
        
        policy = engine.create_policy(
            policy_id="pol1",
            name="Test Policy",
            description="Test",
            policy_type="security",
            rules=[{"type": "encryption_required"}],
            created_by="admin1"
        )
        
        assert "pol1" in engine.policies
        assert policy.name == "Test Policy"
    
    def test_evaluate_policies(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "owner", "owner@example.com")
        engine.register_asset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.CONFIDENTIAL,
            owner="user1"
        )
        
        # Create encryption policy
        engine.create_policy(
            policy_id="pol1",
            name="Encryption Policy",
            description="",
            policy_type="security",
            rules=[{"type": "encryption_required"}],
            created_by="user1"
        )
        
        # Evaluate without encryption
        results = engine.evaluate_policies("asset1", {"encrypted": False})
        assert not results["compliant"]
        assert len(results["violations"]) > 0
        
        # Evaluate with encryption
        results = engine.evaluate_policies("asset1", {"encrypted": True})
        assert results["compliant"]
    
    def test_apply_lifecycle_policies(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "owner", "owner@example.com")
        
        # Create old asset
        old_date = datetime.now() - timedelta(days=100)
        engine.register_asset(
            asset_id="old_asset",
            name="Old Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1",
            retention_days=30,
            modified_at=old_date
        )
        
        results = engine.apply_lifecycle_policies()
        
        assert "old_asset" in results["archived"]
        assert engine.assets["old_asset"].lifecycle_stage == LifecycleStage.ARCHIVED
    
    def test_get_audit_trail(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "user", "user@example.com")
        engine.create_user("user2", "user", "user2@example.com")
        
        events = engine.get_audit_trail()
        assert len(events) >= 2
        
        # Filter by user
        user1_events = engine.get_audit_trail(user_id="system")
        assert len(user1_events) >= 2
    
    def test_generate_governance_report(self):
        engine = GovernanceEngine()
        engine.create_user("user1", "user", "user@example.com")
        engine.register_asset(
            asset_id="asset1",
            name="Dataset",
            classification=DataClassification.INTERNAL,
            owner="user1"
        )
        
        report = engine.generate_governance_report()
        
        assert "summary" in report
        assert report["summary"]["total_users"] == 1
        assert report["summary"]["total_assets"] == 1
        assert "assets_by_classification" in report
        assert report["assets_by_classification"]["internal"] == 1
        assert "assets_by_lifecycle" in report
        assert report["assets_by_lifecycle"]["active"] == 1


class TestIntegrationScenarios:
    def test_full_governance_workflow(self):
        """Test a complete governance workflow"""
        engine = GovernanceEngine()
        
        # Create users with different roles
        engine.create_user("admin1", "admin", "admin@example.com", roles=["admin"])
        engine.create_user("data_owner", "owner", "owner@example.com", roles=["contributor"])
        engine.create_user("analyst", "analyst", "analyst@example.com", roles=["viewer"])
        
        # Register data assets
        asset1 = engine.register_asset(
            asset_id="customer_data",
            name="Customer Data",
            classification=DataClassification.CONFIDENTIAL,
            owner="data_owner",
            compliance_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.CCPA],
            retention_days=730
        )
        
        # Create governance policies
        engine.create_policy(
            policy_id="encryption_policy",
            name="Encryption Required",
            description="Confidential data must be encrypted",
            policy_type="security",
            rules=[{"type": "encryption_required"}],
            created_by="admin1"
        )
        
        engine.create_policy(
            policy_id="owner_policy",
            name="Owner Required",
            description="All datasets must have an owner",
            policy_type="ownership",
            rules=[{"type": "owner_required"}],
            created_by="admin1"
        )
        
        # Evaluate compliance
        results = engine.evaluate_policies("customer_data", {
            "encrypted": True,
            "owner": "data_owner"
        })
        
        assert results["compliant"]
        
        # Check access
        assert engine.check_access("data_owner", "customer_data", "write")  # Owner can write
        assert engine.check_access("analyst", "customer_data", "read")  # Viewer can read
        assert not engine.check_access("analyst", "customer_data", "delete")  # Viewer cannot delete
        
        # Generate report
        report = engine.generate_governance_report()
        assert report["summary"]["total_users"] == 3
        assert report["summary"]["total_assets"] == 1
        assert report["summary"]["active_policies"] == 2
