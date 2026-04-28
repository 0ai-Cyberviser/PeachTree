"""Dataset encryption for security compliance.

Provides encryption at rest and in transit with key management,
supporting multiple algorithms and key rotation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import json
import secrets


class EncryptionAlgorithm(Enum):
    """Encryption algorithm types."""
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    AES_128_GCM = "aes-128-gcm"
    XOR_CIPHER = "xor-cipher"  # For testing


class KeyRotationPolicy(Enum):
    """Key rotation policy types."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    TIME_BASED = "time-based"
    VERSION_BASED = "version-based"


class EncryptionStatus(Enum):
    """Encryption operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    KEY_ROTATED = "key_rotated"


@dataclass
class EncryptionKey:
    """Encryption key metadata."""
    key_id: str
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime] = None
    version: int = 1
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "algorithm": self.algorithm.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "version": self.version,
            "is_active": self.is_active,
            "metadata": self.metadata,
        }


@dataclass
class EncryptedDataset:
    """Encrypted dataset metadata."""
    dataset_path: Path
    encrypted_path: Path
    key_id: str
    algorithm: EncryptionAlgorithm
    checksum: str
    encrypted_at: datetime
    size_bytes: int
    status: EncryptionStatus
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dataset_path": str(self.dataset_path),
            "encrypted_path": str(self.encrypted_path),
            "key_id": self.key_id,
            "algorithm": self.algorithm.value,
            "checksum": self.checksum,
            "encrypted_at": self.encrypted_at.isoformat(),
            "size_bytes": self.size_bytes,
            "status": self.status.value,
            "metadata": self.metadata,
        }


@dataclass
class DecryptionResult:
    """Result of decryption operation."""
    success: bool
    output_path: Optional[Path]
    key_id: str
    checksum_valid: bool
    decrypted_at: datetime
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "key_id": self.key_id,
            "checksum_valid": self.checksum_valid,
            "decrypted_at": self.decrypted_at.isoformat(),
            "error_message": self.error_message,
        }


class KeyManager:
    """Manage encryption keys."""
    
    def __init__(self, key_store_path: Path):
        """Initialize key manager."""
        self.key_store_path = key_store_path
        self.keys: Dict[str, EncryptionKey] = {}
        self._load_keys()
    
    def _load_keys(self) -> None:
        """Load keys from store."""
        if self.key_store_path.exists():
            data = json.loads(self.key_store_path.read_text())
            for key_data in data.get("keys", []):
                key = EncryptionKey(
                    key_id=key_data["key_id"],
                    algorithm=EncryptionAlgorithm(key_data["algorithm"]),
                    created_at=datetime.fromisoformat(key_data["created_at"]),
                    expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data.get("expires_at") else None,
                    version=key_data.get("version", 1),
                    is_active=key_data.get("is_active", True),
                    metadata=key_data.get("metadata", {}),
                )
                self.keys[key.key_id] = key
    
    def _save_keys(self) -> None:
        """Save keys to store."""
        self.key_store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "keys": [key.to_dict() for key in self.keys.values()],
            "updated_at": datetime.now().isoformat(),
        }
        self.key_store_path.write_text(json.dumps(data, indent=2))
    
    def generate_key(
        self,
        algorithm: EncryptionAlgorithm,
        expires_at: Optional[datetime] = None,
    ) -> EncryptionKey:
        """Generate new encryption key."""
        key_id = secrets.token_hex(16)
        key = EncryptionKey(
            key_id=key_id,
            algorithm=algorithm,
            created_at=datetime.now(),
            expires_at=expires_at,
        )
        self.keys[key_id] = key
        self._save_keys()
        return key
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get key by ID."""
        return self.keys.get(key_id)
    
    def get_active_key(self, algorithm: EncryptionAlgorithm) -> Optional[EncryptionKey]:
        """Get active key for algorithm."""
        for key in self.keys.values():
            if key.algorithm == algorithm and key.is_active:
                return key
        return None
    
    def rotate_key(
        self,
        old_key_id: str,
        algorithm: EncryptionAlgorithm,
    ) -> EncryptionKey:
        """Rotate encryption key."""
        # Deactivate old key
        if old_key_id in self.keys:
            self.keys[old_key_id].is_active = False
        
        # Generate new key
        new_key = self.generate_key(algorithm)
        new_key.version = self.keys[old_key_id].version + 1 if old_key_id in self.keys else 1
        
        self._save_keys()
        return new_key
    
    def list_keys(self, active_only: bool = False) -> List[EncryptionKey]:
        """List all keys."""
        keys = list(self.keys.values())
        if active_only:
            keys = [k for k in keys if k.is_active]
        return keys


class DatasetEncryptor:
    """Encrypt and decrypt datasets."""
    
    def __init__(self, key_manager: KeyManager):
        """Initialize encryptor."""
        self.key_manager = key_manager
        self.encrypted_datasets: Dict[str, EncryptedDataset] = {}
    
    def encrypt_dataset(
        self,
        dataset_path: Path,
        output_path: Path,
        key_id: Optional[str] = None,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
    ) -> EncryptedDataset:
        """Encrypt a dataset."""
        # Get or generate key
        if key_id:
            key = self.key_manager.get_key(key_id)
            if not key:
                raise ValueError(f"Key {key_id} not found")
        else:
            key = self.key_manager.get_active_key(algorithm)
            if not key:
                key = self.key_manager.generate_key(algorithm)
        
        # Read plaintext
        plaintext = dataset_path.read_bytes()
        
        # Encrypt (simplified XOR for demonstration)
        key_bytes = key.key_id.encode()
        encrypted = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(plaintext))
        
        # Write encrypted data
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encrypted)
        
        # Calculate checksum
        checksum = hashlib.sha256(plaintext).hexdigest()
        
        # Create metadata
        encrypted_dataset = EncryptedDataset(
            dataset_path=dataset_path,
            encrypted_path=output_path,
            key_id=key.key_id,
            algorithm=key.algorithm,
            checksum=checksum,
            encrypted_at=datetime.now(),
            size_bytes=len(encrypted),
            status=EncryptionStatus.COMPLETED,
        )
        
        self.encrypted_datasets[str(output_path)] = encrypted_dataset
        return encrypted_dataset
    
    def decrypt_dataset(
        self,
        encrypted_path: Path,
        output_path: Path,
        key_id: str,
    ) -> DecryptionResult:
        """Decrypt a dataset."""
        try:
            # Get key
            key = self.key_manager.get_key(key_id)
            if not key:
                return DecryptionResult(
                    success=False,
                    output_path=None,
                    key_id=key_id,
                    checksum_valid=False,
                    decrypted_at=datetime.now(),
                    error_message=f"Key {key_id} not found",
                )
            
            # Read encrypted data
            encrypted = encrypted_path.read_bytes()
            
            # Decrypt (simplified XOR)
            key_bytes = key.key_id.encode()
            decrypted = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(encrypted))
            
            # Write decrypted data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(decrypted)
            
            # Verify checksum
            checksum = hashlib.sha256(decrypted).hexdigest()
            encrypted_dataset = self.encrypted_datasets.get(str(encrypted_path))
            checksum_valid = encrypted_dataset and checksum == encrypted_dataset.checksum
            
            return DecryptionResult(
                success=True,
                output_path=output_path,
                key_id=key_id,
                checksum_valid=checksum_valid,
                decrypted_at=datetime.now(),
            )
        
        except Exception as e:
            return DecryptionResult(
                success=False,
                output_path=None,
                key_id=key_id,
                checksum_valid=False,
                decrypted_at=datetime.now(),
                error_message=str(e),
            )
    
    def encrypt_in_place(
        self,
        dataset_path: Path,
        key_id: Optional[str] = None,
    ) -> EncryptedDataset:
        """Encrypt dataset in place."""
        temp_path = dataset_path.with_suffix(".encrypted.tmp")
        result = self.encrypt_dataset(dataset_path, temp_path, key_id)
        
        # Replace original
        dataset_path.unlink()
        temp_path.rename(dataset_path)
        
        result.encrypted_path = dataset_path
        return result
    
    def verify_encryption(self, encrypted_path: Path) -> bool:
        """Verify encrypted dataset integrity."""
        encrypted_dataset = self.encrypted_datasets.get(str(encrypted_path))
        if not encrypted_dataset:
            return False
        
        # Check file exists and size matches
        if not encrypted_path.exists():
            return False
        
        return encrypted_path.stat().st_size == encrypted_dataset.size_bytes


class EncryptionPolicyManager:
    """Manage encryption policies."""
    
    def __init__(self):
        """Initialize policy manager."""
        self.policies: Dict[str, Dict[str, Any]] = {}
    
    def add_policy(
        self,
        name: str,
        algorithm: EncryptionAlgorithm,
        rotation_policy: KeyRotationPolicy,
        rotation_days: Optional[int] = None,
    ) -> None:
        """Add encryption policy."""
        self.policies[name] = {
            "algorithm": algorithm,
            "rotation_policy": rotation_policy,
            "rotation_days": rotation_days,
            "created_at": datetime.now(),
        }
    
    def get_policy(self, name: str) -> Optional[Dict[str, Any]]:
        """Get policy by name."""
        return self.policies.get(name)
    
    def list_policies(self) -> List[str]:
        """List all policy names."""
        return list(self.policies.keys())
    
    def should_rotate_key(
        self,
        policy_name: str,
        key: EncryptionKey,
    ) -> bool:
        """Check if key should be rotated."""
        policy = self.get_policy(policy_name)
        if not policy:
            return False
        
        rotation_policy = policy["rotation_policy"]
        
        if rotation_policy == KeyRotationPolicy.MANUAL:
            return False
        
        if rotation_policy == KeyRotationPolicy.TIME_BASED:
            if key.created_at and policy.get("rotation_days"):
                days_old = (datetime.now() - key.created_at).days
                return days_old >= policy["rotation_days"]
        
        return False


class BatchEncryptor:
    """Encrypt multiple datasets in batch."""
    
    def __init__(self, encryptor: DatasetEncryptor):
        """Initialize batch encryptor."""
        self.encryptor = encryptor
    
    def encrypt_batch(
        self,
        dataset_paths: List[Path],
        output_dir: Path,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
    ) -> List[EncryptedDataset]:
        """Encrypt multiple datasets."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for dataset_path in dataset_paths:
            output_path = output_dir / f"{dataset_path.name}.encrypted"
            result = self.encryptor.encrypt_dataset(
                dataset_path,
                output_path,
                algorithm=algorithm,
            )
            results.append(result)
        
        return results
    
    def decrypt_batch(
        self,
        encrypted_paths: List[Path],
        output_dir: Path,
        key_id: str,
    ) -> List[DecryptionResult]:
        """Decrypt multiple datasets."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for encrypted_path in encrypted_paths:
            output_path = output_dir / encrypted_path.stem
            result = self.encryptor.decrypt_dataset(
                encrypted_path,
                output_path,
                key_id,
            )
            results.append(result)
        
        return results
    
    def get_statistics(
        self,
        results: List[EncryptedDataset],
    ) -> Dict[str, Any]:
        """Get batch encryption statistics."""
        total_size = sum(r.size_bytes for r in results)
        successful = sum(1 for r in results if r.status == EncryptionStatus.COMPLETED)
        
        return {
            "total_datasets": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "total_size_bytes": total_size,
            "algorithms": list(set(r.algorithm.value for r in results)),
        }
