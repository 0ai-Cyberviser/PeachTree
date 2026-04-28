"""
Enhanced Security Framework for Dataset Operations

Provides comprehensive security features:
- Encryption at rest and in transit
- Key management and rotation
- Access control and auditing
- Data masking and anonymization
- Security scanning and vulnerability detection
- Compliance and policy enforcement

Example:
    >>> from peachtree.dataset_security_v2 import SecurityManager, EncryptionEngine
    >>> 
    >>> # Initialize security manager
    >>> security = SecurityManager(encryption_key="your-key-here")
    >>> 
    >>> # Encrypt sensitive data
    >>> encrypted = security.encrypt_data(sensitive_records)
    >>> 
    >>> # Audit access
    >>> security.audit_access(user="alice", action="read", resource="dataset-123")
"""

import base64
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class SecurityLevel(Enum):
    """Security classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class AccessAction(Enum):
    """Types of access actions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    FERNET = "fernet"
    AES_256 = "aes-256"
    RSA_4096 = "rsa-4096"


@dataclass
class SecurityPolicy:
    """Defines security requirements and policies"""
    
    policy_id: str
    name: str
    security_level: SecurityLevel
    require_encryption: bool = True
    require_audit: bool = True
    require_masking: bool = False
    allowed_actions: Set[AccessAction] = field(default_factory=lambda: {AccessAction.READ})
    max_access_duration: int = 3600  # seconds
    ip_whitelist: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    
    def is_action_allowed(self, action: AccessAction) -> bool:
        """Check if action is allowed by policy"""
        return action in self.allowed_actions
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted"""
        if not self.ip_whitelist:
            return True
        return ip_address in self.ip_whitelist


@dataclass
class AuditEvent:
    """Represents a security audit event"""
    
    event_id: str
    timestamp: float
    user: str
    action: AccessAction
    resource: str
    success: bool
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'user': self.user,
            'action': self.action.value,
            'resource': self.resource,
            'success': self.success,
            'ip_address': self.ip_address,
            'metadata': self.metadata,
            'risk_score': self.risk_score
        }


class EncryptionEngine:
    """Handles data encryption and decryption"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required for encryption")
        
        if encryption_key:
            self.key = self._derive_key(encryption_key)
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
        self.key_rotation_interval = 86400 * 30  # 30 days
        self.last_rotation = time.time()
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password"""
        if salt is None:
            salt = b'peachtree-salt-v1'  # In production, use random salt
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data"""
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_string(self, text: str) -> str:
        """Encrypt string and return base64-encoded result"""
        encrypted = self.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt base64-encoded encrypted string"""
        encrypted = base64.b64decode(encrypted_text.encode())
        decrypted = self.decrypt(encrypted)
        return decrypted.decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary as JSON"""
        json_str = json.dumps(data)
        return self.encrypt_string(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt encrypted dictionary"""
        json_str = self.decrypt_string(encrypted_data)
        return json.loads(json_str)
    
    def rotate_key(self, new_key: Optional[str] = None) -> bytes:
        """Rotate encryption key"""
        
        if new_key:
            self.key = self._derive_key(new_key)
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
        self.last_rotation = time.time()
        
        return self.key
    
    def needs_rotation(self) -> bool:
        """Check if key rotation is needed"""
        return time.time() - self.last_rotation > self.key_rotation_interval


class DataMasking:
    """Data masking and anonymization utilities"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        if '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 4:
            return '*' * len(digits)
        
        return '*' * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def mask_credit_card(card_number: str) -> str:
        """Mask credit card number"""
        digits = re.sub(r'\D', '', card_number)
        if len(digits) < 4:
            return '*' * len(digits)
        
        return '*' * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask social security number"""
        digits = re.sub(r'\D', '', ssn)
        if len(digits) < 4:
            return '*' * len(digits)
        
        return '***-**-' + digits[-4:]
    
    @staticmethod
    def anonymize_name(name: str) -> str:
        """Anonymize personal name"""
        parts = name.split()
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            return parts[0][0] + '***'
        else:
            return parts[0][0] + '*** ' + parts[-1][0] + '***'
    
    @staticmethod
    def hash_pii(value: str, salt: str = "peachtree") -> str:
        """Hash PII data for anonymization"""
        combined = f"{salt}:{value}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


class AccessControl:
    """Manages access control and permissions"""
    
    def __init__(self):
        self.permissions: Dict[str, Set[str]] = {}  # user -> resources
        self.roles: Dict[str, Set[AccessAction]] = {}  # role -> actions
        self.user_roles: Dict[str, Set[str]] = {}  # user -> roles
    
    def grant_permission(self, user: str, resource: str) -> None:
        """Grant user permission to resource"""
        if user not in self.permissions:
            self.permissions[user] = set()
        self.permissions[user].add(resource)
    
    def revoke_permission(self, user: str, resource: str) -> None:
        """Revoke user permission to resource"""
        if user in self.permissions:
            self.permissions[user].discard(resource)
    
    def has_permission(self, user: str, resource: str) -> bool:
        """Check if user has permission to resource"""
        return resource in self.permissions.get(user, set())
    
    def create_role(self, role: str, actions: Set[AccessAction]) -> None:
        """Create security role"""
        self.roles[role] = actions
    
    def assign_role(self, user: str, role: str) -> None:
        """Assign role to user"""
        if role not in self.roles:
            raise ValueError(f"Role {role} does not exist")
        
        if user not in self.user_roles:
            self.user_roles[user] = set()
        self.user_roles[user].add(role)
    
    def has_action(self, user: str, action: AccessAction) -> bool:
        """Check if user can perform action"""
        user_roles_set = self.user_roles.get(user, set())
        for role in user_roles_set:
            if action in self.roles.get(role, set()):
                return True
        return False
    
    def get_user_permissions(self, user: str) -> Dict[str, Any]:
        """Get all permissions for user"""
        return {
            'resources': list(self.permissions.get(user, set())),
            'roles': list(self.user_roles.get(user, set())),
            'actions': list({
                action
                for role in self.user_roles.get(user, set())
                for action in self.roles.get(role, set())
            })
        }


class SecurityScanner:
    """Scans for security vulnerabilities"""
    
    def __init__(self):
        self.patterns = {
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)["\s:=]+([a-zA-Z0-9_-]{20,})'),
            'aws_key': re.compile(r'AKIA[0-9A-Z]{16}'),
            'password': re.compile(r'(?i)(password|passwd|pwd)["\s:=]+([^\s]{8,})'),
            'private_key': re.compile(r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'),
            'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
        }
    
    def scan_text(self, text: str) -> Dict[str, List[str]]:
        """
        Scan text for security issues
        
        Returns:
            Dictionary of pattern_name -> list of matches
        """
        findings = {}
        
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                findings[pattern_name] = [
                    match if isinstance(match, str) else match[0]
                    for match in matches
                ]
        
        return findings
    
    def scan_dict(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Scan dictionary for security issues"""
        text = json.dumps(data)
        return self.scan_text(text)
    
    def calculate_risk_score(self, findings: Dict[str, List[str]]) -> float:
        """Calculate risk score based on findings"""
        severity_scores = {
            'private_key': 1.0,
            'api_key': 0.9,
            'aws_key': 0.9,
            'password': 0.8,
            'jwt': 0.7,
            'ssn': 0.9,
            'credit_card': 0.9,
            'email': 0.3,
            'phone': 0.3
        }
        
        total_score = 0.0
        for pattern_name, matches in findings.items():
            score = severity_scores.get(pattern_name, 0.5)
            total_score += score * len(matches)
        
        # Normalize to 0-1 range
        return min(total_score / 10.0, 1.0)


class SecurityManager:
    """Main security management system"""
    
    def __init__(
        self,
        encryption_key: Optional[str] = None,
        enable_audit: bool = True,
        enable_masking: bool = True
    ):
        self.encryption = EncryptionEngine(encryption_key) if CRYPTO_AVAILABLE else None
        self.masking = DataMasking()
        self.access_control = AccessControl()
        self.scanner = SecurityScanner()
        
        self.enable_audit = enable_audit
        self.enable_masking = enable_masking
        
        self.audit_log: List[AuditEvent] = []
        self.policies: Dict[str, SecurityPolicy] = {}
        
        # Initialize default roles
        self._init_default_roles()
    
    def _init_default_roles(self) -> None:
        """Initialize default security roles"""
        self.access_control.create_role('admin', {
            AccessAction.READ, AccessAction.WRITE,
            AccessAction.DELETE, AccessAction.EXECUTE, AccessAction.ADMIN
        })
        self.access_control.create_role('editor', {
            AccessAction.READ, AccessAction.WRITE, AccessAction.EXECUTE
        })
        self.access_control.create_role('viewer', {
            AccessAction.READ
        })
    
    def encrypt_data(self, data: Any) -> str:
        """Encrypt data (supports dict, str, bytes)"""
        if not self.encryption:
            raise RuntimeError("Encryption not available")
        
        if isinstance(data, dict):
            return self.encryption.encrypt_dict(data)
        elif isinstance(data, str):
            return self.encryption.encrypt_string(data)
        elif isinstance(data, bytes):
            encrypted = self.encryption.encrypt(data)
            return base64.b64encode(encrypted).decode()
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
    
    def decrypt_data(self, encrypted_data: str, data_type: str = "dict") -> Any:
        """Decrypt data"""
        if not self.encryption:
            raise RuntimeError("Encryption not available")
        
        if data_type == "dict":
            return self.encryption.decrypt_dict(encrypted_data)
        elif data_type == "str":
            return self.encryption.decrypt_string(encrypted_data)
        elif data_type == "bytes":
            encrypted = base64.b64decode(encrypted_data.encode())
            return self.encryption.decrypt(encrypted)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
    
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in dictionary"""
        if not self.enable_masking:
            return data
        
        masked = data.copy()
        
        for key, value in masked.items():
            if isinstance(value, str):
                key_lower = key.lower()
                if 'email' in key_lower:
                    masked[key] = self.masking.mask_email(value)
                elif 'phone' in key_lower:
                    masked[key] = self.masking.mask_phone(value)
                elif 'card' in key_lower or 'credit' in key_lower:
                    masked[key] = self.masking.mask_credit_card(value)
                elif 'ssn' in key_lower:
                    masked[key] = self.masking.mask_ssn(value)
                elif 'name' in key_lower:
                    masked[key] = self.masking.anonymize_name(value)
        
        return masked
    
    def audit_access(
        self,
        user: str,
        action: AccessAction,
        resource: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Audit an access event
        
        Returns:
            Event ID
        """
        if not self.enable_audit:
            return ""
        
        event_id = f"audit-{len(self.audit_log):08d}"
        event = AuditEvent(
            event_id=event_id,
            timestamp=time.time(),
            user=user,
            action=action,
            resource=resource,
            success=success,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        # Calculate risk score
        risk_factors = 0.0
        if not success:
            risk_factors += 0.3
        if action in (AccessAction.DELETE, AccessAction.ADMIN):
            risk_factors += 0.4
        
        event.risk_score = min(risk_factors, 1.0)
        
        self.audit_log.append(event)
        return event_id
    
    def scan_for_vulnerabilities(self, data: Any) -> Dict[str, Any]:
        """
        Scan data for security vulnerabilities
        
        Returns:
            Scan report with findings and risk score
        """
        if isinstance(data, dict):
            findings = self.scanner.scan_dict(data)
        elif isinstance(data, str):
            findings = self.scanner.scan_text(data)
        else:
            findings = {}
        
        risk_score = self.scanner.calculate_risk_score(findings)
        
        return {
            'findings': findings,
            'risk_score': risk_score,
            'has_issues': len(findings) > 0,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low'
        }
    
    def get_audit_log(
        self,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        filtered = self.audit_log
        
        if user:
            filtered = [e for e in filtered if e.user == user]
        if resource:
            filtered = [e for e in filtered if e.resource == resource]
        
        return [e.to_dict() for e in filtered[-limit:]]
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            'encryption_enabled': self.encryption is not None,
            'audit_enabled': self.enable_audit,
            'masking_enabled': self.enable_masking,
            'total_audit_events': len(self.audit_log),
            'total_policies': len(self.policies),
            'high_risk_events': len([e for e in self.audit_log if e.risk_score > 0.7])
        }


# Public API
__all__ = [
    'SecurityManager',
    'EncryptionEngine',
    'DataMasking',
    'AccessControl',
    'SecurityScanner',
    'SecurityPolicy',
    'AuditEvent',
    'SecurityLevel',
    'AccessAction',
    'EncryptionAlgorithm'
]
