"""Tests for dataset plugin system functionality."""

from pathlib import Path
import json
import pytest

from peachtree.dataset_plugins import (
    PluginManager,
    Plugin,
    PluginMetadata,
    PluginRegistration,
    PluginType,
    PluginStatus,
    TransformerPlugin,
    ExampleTransformerPlugin,
    EXAMPLE_PLUGIN_METADATA,
)


def test_plugin_manager_initialization():
    """Test that plugin manager initializes."""
    manager = PluginManager()
    
    assert isinstance(manager.plugins, dict)
    assert isinstance(manager.instances, dict)
    assert isinstance(manager.hooks, dict)


def test_register_plugin():
    """Test registering a plugin."""
    manager = PluginManager()
    
    metadata = PluginMetadata(
        plugin_id="test_plugin",
        name="Test Plugin",
        version="1.0.0",
        description="A test plugin",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="TestPlugin",
    )
    
    success = manager.register_plugin(metadata, ExampleTransformerPlugin)
    
    assert success
    assert "test_plugin" in manager.plugins
    assert manager.plugins["test_plugin"].status == PluginStatus.DISABLED


def test_register_example_plugin():
    """Test registering the example plugin."""
    manager = PluginManager()
    
    success = manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    assert success
    assert EXAMPLE_PLUGIN_METADATA.plugin_id in manager.plugins


def test_enable_plugin():
    """Test enabling a plugin."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    success = manager.enable_plugin(
        EXAMPLE_PLUGIN_METADATA.plugin_id,
        config={"field": "content"},
    )
    
    assert success
    registration = manager.plugins[EXAMPLE_PLUGIN_METADATA.plugin_id]
    assert registration.status == PluginStatus.ENABLED
    assert EXAMPLE_PLUGIN_METADATA.plugin_id in manager.instances


def test_disable_plugin():
    """Test disabling a plugin."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    manager.enable_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id, config={})
    
    success = manager.disable_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id)
    
    assert success
    registration = manager.plugins[EXAMPLE_PLUGIN_METADATA.plugin_id]
    assert registration.status == PluginStatus.DISABLED
    assert EXAMPLE_PLUGIN_METADATA.plugin_id not in manager.instances


def test_enable_nonexistent_plugin():
    """Test enabling a plugin that doesn't exist."""
    manager = PluginManager()
    
    success = manager.enable_plugin("nonexistent")
    
    assert not success


def test_disable_nonexistent_plugin():
    """Test disabling a plugin that doesn't exist."""
    manager = PluginManager()
    
    success = manager.disable_plugin("nonexistent")
    
    assert not success


def test_unregister_plugin():
    """Test unregistering a plugin."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    assert EXAMPLE_PLUGIN_METADATA.plugin_id in manager.plugins
    
    success = manager.unregister_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id)
    
    assert success
    assert EXAMPLE_PLUGIN_METADATA.plugin_id not in manager.plugins


def test_unregister_nonexistent_plugin():
    """Test unregistering a plugin that doesn't exist."""
    manager = PluginManager()
    
    success = manager.unregister_plugin("nonexistent")
    
    assert not success


def test_execute_plugin():
    """Test executing a plugin."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    manager.enable_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id, config={"field": "content"})
    
    record = {"content": "hello world", "id": "1"}
    result = manager.execute_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id, record)
    
    assert result["content"] == "HELLO WORLD"
    assert result["id"] == "1"


def test_execute_nonexistent_plugin():
    """Test executing a plugin that doesn't exist."""
    manager = PluginManager()
    
    with pytest.raises(ValueError, match="not found"):
        manager.execute_plugin("nonexistent", {})


def test_execute_disabled_plugin():
    """Test executing a disabled plugin."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    with pytest.raises(ValueError, match="not enabled"):
        manager.execute_plugin(EXAMPLE_PLUGIN_METADATA.plugin_id, {})


def test_get_plugins_by_type():
    """Test getting plugins by type."""
    manager = PluginManager()
    
    # Register plugins of different types
    meta1 = PluginMetadata(
        plugin_id="transformer1",
        name="Transformer",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="Test",
    )
    
    meta2 = PluginMetadata(
        plugin_id="validator1",
        name="Validator",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.VALIDATOR,
        entry_point="Test",
    )
    
    manager.register_plugin(meta1, ExampleTransformerPlugin)
    manager.register_plugin(meta2, ExampleTransformerPlugin)  # Using same class for test
    
    transformers = manager.get_plugins_by_type(PluginType.TRANSFORMER)
    validators = manager.get_plugins_by_type(PluginType.VALIDATOR)
    
    assert "transformer1" in transformers
    assert "transformer1" not in validators
    assert "validator1" in validators


def test_get_enabled_plugins():
    """Test getting enabled plugins."""
    manager = PluginManager()
    
    meta1 = PluginMetadata(
        plugin_id="plugin1",
        name="Plugin 1",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="Test",
    )
    
    meta2 = PluginMetadata(
        plugin_id="plugin2",
        name="Plugin 2",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="Test",
    )
    
    manager.register_plugin(meta1, ExampleTransformerPlugin)
    manager.register_plugin(meta2, ExampleTransformerPlugin)
    
    # Enable only plugin1
    manager.enable_plugin("plugin1", config={})
    
    enabled = manager.get_enabled_plugins()
    
    assert "plugin1" in enabled
    assert "plugin2" not in enabled


def test_register_hook():
    """Test registering a hook callback."""
    manager = PluginManager()
    
    callback_called = []
    
    def test_callback(*args, **kwargs):
        callback_called.append(True)
        return "result"
    
    manager.register_hook("test_hook", test_callback)
    
    assert "test_hook" in manager.hooks
    assert len(manager.hooks["test_hook"]) == 1


def test_execute_hooks():
    """Test executing hook callbacks."""
    manager = PluginManager()
    
    results = []
    
    def callback1():
        results.append(1)
        return "callback1"
    
    def callback2():
        results.append(2)
        return "callback2"
    
    manager.register_hook("test_hook", callback1)
    manager.register_hook("test_hook", callback2)
    
    hook_results = manager.execute_hooks("test_hook")
    
    assert len(hook_results) == 2
    assert "callback1" in hook_results
    assert "callback2" in hook_results
    assert 1 in results
    assert 2 in results


def test_execute_hooks_with_error():
    """Test that hook errors are captured."""
    manager = PluginManager()
    
    def failing_callback():
        raise ValueError("Test error")
    
    manager.register_hook("test_hook", failing_callback)
    
    results = manager.execute_hooks("test_hook")
    
    assert len(results) == 1
    assert "error" in results[0]


def test_save_plugin_registry(tmp_path):
    """Test saving plugin registry to file."""
    manager = PluginManager()
    output_path = tmp_path / "registry.json"
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    manager.save_plugin_registry(output_path)
    
    assert output_path.exists()
    
    # Verify content
    data = json.loads(output_path.read_text())
    assert "plugins" in data
    assert len(data["plugins"]) == 1


def test_get_plugin_info():
    """Test getting plugin information."""
    manager = PluginManager()
    
    manager.register_plugin(EXAMPLE_PLUGIN_METADATA, ExampleTransformerPlugin)
    
    info = manager.get_plugin_info(EXAMPLE_PLUGIN_METADATA.plugin_id)
    
    assert info is not None
    assert info["metadata"]["plugin_id"] == EXAMPLE_PLUGIN_METADATA.plugin_id
    assert info["metadata"]["name"] == EXAMPLE_PLUGIN_METADATA.name
    assert info["status"] == "disabled"


def test_get_plugin_info_nonexistent():
    """Test getting info for nonexistent plugin."""
    manager = PluginManager()
    
    info = manager.get_plugin_info("nonexistent")
    
    assert info is None


def test_get_statistics():
    """Test getting plugin system statistics."""
    manager = PluginManager()
    
    meta1 = PluginMetadata(
        plugin_id="plugin1",
        name="Plugin 1",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="Test",
    )
    
    meta2 = PluginMetadata(
        plugin_id="plugin2",
        name="Plugin 2",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.VALIDATOR,
        entry_point="Test",
    )
    
    manager.register_plugin(meta1, ExampleTransformerPlugin)
    manager.register_plugin(meta2, ExampleTransformerPlugin)
    manager.enable_plugin("plugin1", config={})
    
    stats = manager.get_statistics()
    
    assert stats["total_plugins"] == 2
    assert stats["enabled_plugins"] == 1
    assert "by_type" in stats
    assert "by_status" in stats


def test_plugin_metadata_to_dict():
    """Test converting plugin metadata to dictionary."""
    metadata = PluginMetadata(
        plugin_id="test_id",
        name="Test Plugin",
        version="1.0.0",
        description="Test description",
        author="test_author",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="TestClass",
        dependencies=["dep1", "dep2"],
        config_schema={"field": {"type": "string"}},
    )
    
    data = metadata.to_dict()
    
    assert data["plugin_id"] == "test_id"
    assert data["name"] == "Test Plugin"
    assert data["plugin_type"] == "transformer"
    assert "dep1" in data["dependencies"]


def test_plugin_registration_to_dict():
    """Test converting plugin registration to dictionary."""
    metadata = PluginMetadata(
        plugin_id="test",
        name="Test",
        version="1.0.0",
        description="Test",
        author="test",
        plugin_type=PluginType.TRANSFORMER,
        entry_point="Test",
    )
    
    registration = PluginRegistration(
        metadata=metadata,
        plugin_class=ExampleTransformerPlugin,
        status=PluginStatus.ENABLED,
    )
    
    data = registration.to_dict()
    
    assert "metadata" in data
    assert "status" in data
    assert data["status"] == "enabled"


def test_example_transformer_plugin():
    """Test the example transformer plugin."""
    plugin = ExampleTransformerPlugin()
    plugin.initialize({"field": "text"})
    
    record = {"text": "hello", "id": "1"}
    result = plugin.transform_record(record)
    
    assert result["text"] == "HELLO"
    assert result["id"] == "1"


def test_example_transformer_with_missing_field():
    """Test transformer with missing field."""
    plugin = ExampleTransformerPlugin()
    plugin.initialize({"field": "missing_field"})
    
    record = {"text": "hello"}
    result = plugin.transform_record(record)
    
    # Should not modify record if field doesn't exist
    assert result["text"] == "hello"


def test_example_transformer_with_non_string():
    """Test transformer with non-string value."""
    plugin = ExampleTransformerPlugin()
    plugin.initialize({"field": "number"})
    
    record = {"number": 123}
    result = plugin.transform_record(record)
    
    # Should not modify non-string fields
    assert result["number"] == 123


def test_plugin_cleanup():
    """Test plugin cleanup."""
    plugin = ExampleTransformerPlugin()
    plugin.initialize({})
    
    # Cleanup should not raise errors
    plugin.cleanup()


def test_plugin_type_enum_values():
    """Test PluginType enum has expected values."""
    assert PluginType.IMPORTER.value == "importer"
    assert PluginType.EXPORTER.value == "exporter"
    assert PluginType.TRANSFORMER.value == "transformer"
    assert PluginType.VALIDATOR.value == "validator"
    assert PluginType.ENRICHER.value == "enricher"
    assert PluginType.QUALITY_SCORER.value == "quality_scorer"
    assert PluginType.DEDUPLICATOR.value == "deduplicator"
    assert PluginType.FILTER.value == "filter"


def test_plugin_status_enum_values():
    """Test PluginStatus enum has expected values."""
    assert PluginStatus.ENABLED.value == "enabled"
    assert PluginStatus.DISABLED.value == "disabled"
    assert PluginStatus.ERROR.value == "error"
