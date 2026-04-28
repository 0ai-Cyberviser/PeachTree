"""Plugin system for extending PeachTree functionality."""

import importlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


class PluginType(Enum):
    """Types of plugins."""
    
    IMPORTER = "importer"  # Import data from external sources
    EXPORTER = "exporter"  # Export data to external formats
    TRANSFORMER = "transformer"  # Transform dataset records
    VALIDATOR = "validator"  # Validate dataset records
    ENRICHER = "enricher"  # Enrich records with additional data
    QUALITY_SCORER = "quality_scorer"  # Custom quality scoring
    DEDUPLICATOR = "deduplicator"  # Custom deduplication logic
    FILTER = "filter"  # Filter records based on criteria


class PluginStatus(Enum):
    """Status of a plugin."""
    
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "plugin_type": self.plugin_type.value,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
        }


class Plugin(ABC):
    """Base class for all plugins."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the plugin's main functionality."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class ImporterPlugin(Plugin):
    """Base class for importer plugins."""
    
    @abstractmethod
    def import_data(self, source: str, **options: Any) -> List[Dict[str, Any]]:
        """Import data from source."""
        pass


class ExporterPlugin(Plugin):
    """Base class for exporter plugins."""
    
    @abstractmethod
    def export_data(
        self,
        data: List[Dict[str, Any]],
        destination: str,
        **options: Any,
    ) -> Dict[str, Any]:
        """Export data to destination."""
        pass


class TransformerPlugin(Plugin):
    """Base class for transformer plugins."""
    
    @abstractmethod
    def transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single record."""
        pass


class ValidatorPlugin(Plugin):
    """Base class for validator plugins."""
    
    @abstractmethod
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate a single record."""
        pass


@dataclass
class PluginRegistration:
    """Registration information for a plugin."""
    
    metadata: PluginMetadata
    plugin_class: Type[Plugin]
    status: PluginStatus = PluginStatus.DISABLED
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "status": self.status.value,
            "registered_at": self.registered_at,
            "error_message": self.error_message,
        }


class PluginManager:
    """Manager for loading and executing plugins."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, PluginRegistration] = {}
        self.instances: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
    
    def register_plugin(
        self,
        metadata: PluginMetadata,
        plugin_class: Type[Plugin],
    ) -> bool:
        """Register a plugin."""
        try:
            registration = PluginRegistration(
                metadata=metadata,
                plugin_class=plugin_class,
                status=PluginStatus.DISABLED,
            )
            
            self.plugins[metadata.plugin_id] = registration
            return True
        
        except Exception as e:
            registration = PluginRegistration(
                metadata=metadata,
                plugin_class=plugin_class,
                status=PluginStatus.ERROR,
                error_message=str(e),
            )
            self.plugins[metadata.plugin_id] = registration
            return False
    
    def enable_plugin(
        self,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Enable a plugin."""
        registration = self.plugins.get(plugin_id)
        
        if not registration:
            return False
        
        try:
            # Create instance if not exists
            if plugin_id not in self.instances:
                instance = registration.plugin_class()
                instance.initialize(config or {})
                self.instances[plugin_id] = instance
            
            registration.status = PluginStatus.ENABLED
            return True
        
        except Exception as e:
            registration.status = PluginStatus.ERROR
            registration.error_message = str(e)
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        registration = self.plugins.get(plugin_id)
        
        if not registration:
            return False
        
        # Cleanup instance
        if plugin_id in self.instances:
            try:
                self.instances[plugin_id].cleanup()
            except Exception:
                pass
            del self.instances[plugin_id]
        
        registration.status = PluginStatus.DISABLED
        return True
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin."""
        if plugin_id in self.plugins:
            # Disable first
            self.disable_plugin(plugin_id)
            
            # Remove registration
            del self.plugins[plugin_id]
            return True
        
        return False
    
    def execute_plugin(
        self,
        plugin_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a plugin."""
        registration = self.plugins.get(plugin_id)
        
        if not registration:
            raise ValueError(f"Plugin {plugin_id} not found")
        
        if registration.status != PluginStatus.ENABLED:
            raise ValueError(f"Plugin {plugin_id} is not enabled")
        
        instance = self.instances.get(plugin_id)
        
        if not instance:
            raise ValueError(f"Plugin {plugin_id} has no instance")
        
        return instance.execute(*args, **kwargs)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[str]:
        """Get all plugin IDs of a specific type."""
        return [
            plugin_id
            for plugin_id, reg in self.plugins.items()
            if reg.metadata.plugin_type == plugin_type
        ]
    
    def get_enabled_plugins(self) -> List[str]:
        """Get all enabled plugin IDs."""
        return [
            plugin_id
            for plugin_id, reg in self.plugins.items()
            if reg.status == PluginStatus.ENABLED
        ]
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a hook callback."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(callback)
    
    def execute_hooks(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Execute all callbacks for a hook."""
        callbacks = self.hooks.get(hook_name, [])
        results = []
        
        for callback in callbacks:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        
        return results
    
    def load_plugin_from_file(self, plugin_path: Path) -> bool:
        """Load a plugin from a Python file."""
        try:
            # Read plugin module
            spec = importlib.util.spec_from_file_location("custom_plugin", plugin_path)
            if not spec or not spec.loader:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class and metadata
            if not hasattr(module, "PLUGIN_METADATA") or not hasattr(module, "PluginClass"):
                return False
            
            metadata_dict = module.PLUGIN_METADATA
            plugin_class = module.PluginClass
            
            # Create metadata
            metadata = PluginMetadata(
                plugin_id=metadata_dict["plugin_id"],
                name=metadata_dict["name"],
                version=metadata_dict["version"],
                description=metadata_dict["description"],
                author=metadata_dict["author"],
                plugin_type=PluginType(metadata_dict["plugin_type"]),
                entry_point=metadata_dict["entry_point"],
                dependencies=metadata_dict.get("dependencies", []),
                config_schema=metadata_dict.get("config_schema", {}),
            )
            
            # Register plugin
            return self.register_plugin(metadata, plugin_class)
        
        except Exception:
            return False
    
    def save_plugin_registry(self, output_path: Path) -> None:
        """Save plugin registry to file."""
        data = {
            "plugins": [
                {
                    "plugin_id": plugin_id,
                    "registration": reg.to_dict(),
                }
                for plugin_id, reg in self.plugins.items()
            ],
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin information."""
        registration = self.plugins.get(plugin_id)
        
        if not registration:
            return None
        
        return registration.to_dict()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        total = len(self.plugins)
        enabled = len(self.get_enabled_plugins())
        
        by_type = {}
        by_status = {}
        
        for registration in self.plugins.values():
            plugin_type = registration.metadata.plugin_type.value
            status = registration.status.value
            
            by_type[plugin_type] = by_type.get(plugin_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_plugins": total,
            "enabled_plugins": enabled,
            "by_type": by_type,
            "by_status": by_status,
            "total_hooks": len(self.hooks),
        }


# Example plugin implementation
class ExampleTransformerPlugin(TransformerPlugin):
    """Example transformer plugin that uppercases text."""
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin."""
        self.field = config.get("field", "content")
    
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute plugin."""
        if args:
            return self.transform_record(args[0])
        return None
    
    def transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform record by uppercasing specified field."""
        if self.field in record and isinstance(record[self.field], str):
            record[self.field] = record[self.field].upper()
        return record
    
    def cleanup(self) -> None:
        """Cleanup plugin."""
        pass


# Example plugin metadata
EXAMPLE_PLUGIN_METADATA = PluginMetadata(
    plugin_id="example_uppercase_transformer",
    name="Uppercase Transformer",
    version="1.0.0",
    description="Transforms text fields to uppercase",
    author="PeachTree",
    plugin_type=PluginType.TRANSFORMER,
    entry_point="ExampleTransformerPlugin",
    config_schema={
        "field": {
            "type": "string",
            "default": "content",
            "description": "Field to transform",
        },
    },
)
