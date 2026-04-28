"""Tests for dataset_encryption module."""
import json
import pytest
from datetime import datetime, timedelta
from peachtree.dataset_encryption import (
    DatasetEncryptor,
    KeyManager,
    EncryptionAlgorithm,
    KeyRotationPolicy,
    EncryptionStatus,
    EncryptionPolicyManager,
    BatchEncryptor,
)


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a sample JSONL dataset."""
    dataset = tmp_path / "test.jsonl"
    records = [
        {"id": 1, "text": "sensitive data", "label": "secret"},
        {"id": 2, "text": "confidential info", "label": "private"},
        {"id": 3, "text": "protected content", "label": "secure"},
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in records))
    return dataset


@pytest.fixture
def key_manager(tmp_path):
    """Create a key manager."""
    return KeyManager(tmp_path / "keys.json")


def test_key_manager_init(tmp_path):
    """Test key manager initialization."""
    km = KeyManager(tmp_path / "keys.json")
    assert km.key_store_path == tmp_path / "keys.json"


def test_generate_key(key_manager):
    """Test key generation."""
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    
    assert key.key_id
    assert key.algorithm == EncryptionAlgorithm.AES_256_GCM
    assert key.is_active
    assert key.version == 1


def test_generate_key_with_expiry(key_manager):
    """Test key generation with expiration."""
    expires = datetime.now() + timedelta(days=30)
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM, expires_at=expires)
    
    assert key.expires_at == expires


def test_get_key(key_manager):
    """Test retrieving a key."""
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    
    retrieved = key_manager.get_key(key.key_id)
    assert retrieved.key_id == key.key_id


def test_get_active_key(key_manager):
    """Test getting active key for algorithm."""
    key = key_manager.generate_key(EncryptionAlgorithm.CHACHA20_POLY1305)
    
    active = key_manager.get_active_key(EncryptionAlgorithm.CHACHA20_POLY1305)
    assert active.key_id == key.key_id


def test_rotate_key(key_manager):
    """Test key rotation."""
    old_key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    new_key = key_manager.rotate_key(old_key.key_id, EncryptionAlgorithm.AES_256_GCM)
    
    assert new_key.version == old_key.version + 1
    assert new_key.is_active
    assert not key_manager.get_key(old_key.key_id).is_active


def test_list_keys(key_manager):
    """Test listing all keys."""
    key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    key_manager.generate_key(EncryptionAlgorithm.CHACHA20_POLY1305)
    
    keys = key_manager.list_keys()
    assert len(keys) == 2


def test_list_active_keys_only(key_manager):
    """Test listing only active keys."""
    key1 = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    key_manager.generate_key(EncryptionAlgorithm.CHACHA20_POLY1305)
    key_manager.rotate_key(key1.key_id, EncryptionAlgorithm.AES_256_GCM)
    
    active_keys = key_manager.list_keys(active_only=True)
    assert len(active_keys) == 2


def test_encrypt_dataset(tmp_path, sample_dataset, key_manager):
    """Test encrypting a dataset."""
    encryptor = DatasetEncryptor(key_manager)
    output = tmp_path / "encrypted.bin"
    
    result = encryptor.encrypt_dataset(sample_dataset, output)
    
    assert result.status == EncryptionStatus.COMPLETED
    assert output.exists()
    assert result.checksum


def test_decrypt_dataset(tmp_path, sample_dataset, key_manager):
    """Test decrypting a dataset."""
    encryptor = DatasetEncryptor(key_manager)
    encrypted_path = tmp_path / "encrypted.bin"
    decrypted_path = tmp_path / "decrypted.jsonl"
    
    # Encrypt first
    encrypted = encryptor.encrypt_dataset(sample_dataset, encrypted_path)
    
    # Decrypt
    result = encryptor.decrypt_dataset(encrypted_path, decrypted_path, encrypted.key_id)
    
    assert result.success
    assert decrypted_path.exists()
    assert decrypted_path.read_bytes() == sample_dataset.read_bytes()


def test_encrypt_with_specific_key(tmp_path, sample_dataset, key_manager):
    """Test encrypting with specific key."""
    key = key_manager.generate_key(EncryptionAlgorithm.AES_128_GCM)
    encryptor = DatasetEncryptor(key_manager)
    output = tmp_path / "encrypted.bin"
    
    result = encryptor.encrypt_dataset(sample_dataset, output, key_id=key.key_id)
    
    assert result.key_id == key.key_id


def test_encrypt_in_place(tmp_path, key_manager):
    """Test in-place encryption."""
    dataset = tmp_path / "data.jsonl"
    dataset.write_text('{"test": "data"}')
    
    encryptor = DatasetEncryptor(key_manager)
    result = encryptor.encrypt_in_place(dataset)
    
    assert result.status == EncryptionStatus.COMPLETED
    assert result.encrypted_path == dataset


def test_verify_encryption(tmp_path, sample_dataset, key_manager):
    """Test verifying encrypted dataset."""
    encryptor = DatasetEncryptor(key_manager)
    output = tmp_path / "encrypted.bin"
    
    encryptor.encrypt_dataset(sample_dataset, output)
    
    assert encryptor.verify_encryption(output)


def test_decryption_with_wrong_key(tmp_path, sample_dataset, key_manager):
    """Test decryption with wrong key fails gracefully."""
    encryptor = DatasetEncryptor(key_manager)
    encrypted_path = tmp_path / "encrypted.bin"
    decrypted_path = tmp_path / "decrypted.jsonl"
    
    encryptor.encrypt_dataset(sample_dataset, encrypted_path)
    
    # Try to decrypt with nonexistent key
    result = encryptor.decrypt_dataset(encrypted_path, decrypted_path, "wrong-key")
    
    assert not result.success
    assert result.error_message


def test_encryption_policy_manager():
    """Test encryption policy manager."""
    manager = EncryptionPolicyManager()
    
    manager.add_policy(
        "standard",
        EncryptionAlgorithm.AES_256_GCM,
        KeyRotationPolicy.TIME_BASED,
        rotation_days=30,
    )
    
    policy = manager.get_policy("standard")
    assert policy["algorithm"] == EncryptionAlgorithm.AES_256_GCM


def test_list_policies():
    """Test listing policies."""
    manager = EncryptionPolicyManager()
    manager.add_policy("p1", EncryptionAlgorithm.AES_256_GCM, KeyRotationPolicy.MANUAL)
    manager.add_policy("p2", EncryptionAlgorithm.CHACHA20_POLY1305, KeyRotationPolicy.AUTOMATIC)
    
    policies = manager.list_policies()
    assert len(policies) == 2


def test_should_rotate_manual_policy(key_manager):
    """Test manual rotation policy."""
    manager = EncryptionPolicyManager()
    manager.add_policy("manual", EncryptionAlgorithm.AES_256_GCM, KeyRotationPolicy.MANUAL)
    
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    
    assert not manager.should_rotate_key("manual", key)


def test_should_rotate_time_based_policy(key_manager):
    """Test time-based rotation policy."""
    manager = EncryptionPolicyManager()
    manager.add_policy("time", EncryptionAlgorithm.AES_256_GCM, KeyRotationPolicy.TIME_BASED, rotation_days=1)
    
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    key.created_at = datetime.now() - timedelta(days=2)
    
    assert manager.should_rotate_key("time", key)


def test_batch_encryptor(tmp_path, key_manager):
    """Test batch encryption."""
    # Create multiple datasets
    datasets = []
    for i in range(3):
        dataset = tmp_path / f"data{i}.jsonl"
        dataset.write_text(f'{{"id": {i}}}')
        datasets.append(dataset)
    
    encryptor = DatasetEncryptor(key_manager)
    batch = BatchEncryptor(encryptor)
    output_dir = tmp_path / "encrypted"
    
    results = batch.encrypt_batch(datasets, output_dir)
    
    assert len(results) == 3
    assert all(r.status == EncryptionStatus.COMPLETED for r in results)


def test_batch_decrypt(tmp_path, key_manager):
    """Test batch decryption."""
    # Create and encrypt datasets
    datasets = []
    for i in range(2):
        dataset = tmp_path / f"data{i}.jsonl"
        dataset.write_text(f'{{"id": {i}}}')
        datasets.append(dataset)
    
    encryptor = DatasetEncryptor(key_manager)
    batch = BatchEncryptor(encryptor)
    
    encrypted_dir = tmp_path / "encrypted"
    encrypted_results = batch.encrypt_batch(datasets, encrypted_dir)
    
    # Decrypt
    encrypted_paths = [r.encrypted_path for r in encrypted_results]
    decrypted_dir = tmp_path / "decrypted"
    
    decrypt_results = batch.decrypt_batch(encrypted_paths, decrypted_dir, encrypted_results[0].key_id)
    
    assert len(decrypt_results) == 2


def test_batch_statistics(tmp_path, key_manager):
    """Test batch encryption statistics."""
    datasets = []
    for i in range(3):
        dataset = tmp_path / f"data{i}.jsonl"
        dataset.write_text(f'{{"id": {i}}}' * 10)
        datasets.append(dataset)
    
    encryptor = DatasetEncryptor(key_manager)
    batch = BatchEncryptor(encryptor)
    
    results = batch.encrypt_batch(datasets, tmp_path / "out")
    stats = batch.get_statistics(results)
    
    assert stats["total_datasets"] == 3
    assert stats["successful"] == 3
    assert stats["total_size_bytes"] > 0


def test_encryption_algorithm_enum():
    """Test encryption algorithm enum."""
    assert EncryptionAlgorithm.AES_256_GCM
    assert EncryptionAlgorithm.CHACHA20_POLY1305
    assert EncryptionAlgorithm.AES_128_GCM
    assert EncryptionAlgorithm.XOR_CIPHER


def test_key_rotation_policy_enum():
    """Test key rotation policy enum."""
    assert KeyRotationPolicy.MANUAL
    assert KeyRotationPolicy.AUTOMATIC
    assert KeyRotationPolicy.TIME_BASED
    assert KeyRotationPolicy.VERSION_BASED


def test_encryption_status_enum():
    """Test encryption status enum."""
    assert EncryptionStatus.PENDING
    assert EncryptionStatus.IN_PROGRESS
    assert EncryptionStatus.COMPLETED
    assert EncryptionStatus.FAILED
    assert EncryptionStatus.KEY_ROTATED


def test_encryption_key_serialization(key_manager):
    """Test encryption key serialization."""
    key = key_manager.generate_key(EncryptionAlgorithm.AES_256_GCM)
    data = key.to_dict()
    
    assert "key_id" in data
    assert "algorithm" in data
    assert "created_at" in data


def test_encrypted_dataset_serialization(tmp_path, sample_dataset, key_manager):
    """Test encrypted dataset serialization."""
    encryptor = DatasetEncryptor(key_manager)
    result = encryptor.encrypt_dataset(sample_dataset, tmp_path / "enc.bin")
    data = result.to_dict()
    
    assert "encrypted_path" in data
    assert "checksum" in data
    assert "status" in data
