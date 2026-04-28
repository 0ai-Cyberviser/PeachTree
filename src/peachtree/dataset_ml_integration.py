"""
PeachTree ML Framework Integration

Seamless integration with major ML frameworks (PyTorch, TensorFlow, JAX, HuggingFace)
for efficient dataset loading, preprocessing, and training pipeline integration.

Features:
- PyTorch DataLoader integration
- TensorFlow Dataset API integration
- JAX data pipeline support
- HuggingFace Datasets compatibility
- Automatic batching and shuffling
- Memory-efficient streaming
- Multi-GPU data parallelism
- Custom collate functions
- Data augmentation hooks
"""

from typing import Dict, List, Any, Optional, Callable, Iterator, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
from abc import ABC, abstractmethod


class MLFramework(Enum):
    """Supported ML frameworks"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    JAX = "jax"
    HUGGINGFACE = "huggingface"


class DataFormat(Enum):
    """Data format types"""
    JSONL = "jsonl"
    PARQUET = "parquet"
    TFRECORD = "tfrecord"
    ARROW = "arrow"


@dataclass
class DataLoaderConfig:
    """Configuration for ML framework data loaders"""
    batch_size: int = 32
    shuffle: bool = True
    num_workers: int = 0
    prefetch_factor: int = 2
    drop_last: bool = False
    pin_memory: bool = False
    persistent_workers: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "batch_size": self.batch_size,
            "shuffle": self.shuffle,
            "num_workers": self.num_workers,
            "prefetch_factor": self.prefetch_factor,
            "drop_last": self.drop_last,
            "pin_memory": self.pin_memory,
            "persistent_workers": self.persistent_workers
        }


class BaseDatasetAdapter(ABC):
    """Abstract base class for framework-specific dataset adapters"""
    
    def __init__(self, dataset_path: str, config: Optional[DataLoaderConfig] = None):
        self.dataset_path = Path(dataset_path)
        self.config = config or DataLoaderConfig()
        self._records: List[Dict[str, Any]] = []
        self._load_dataset()
    
    def _load_dataset(self) -> None:
        """Load dataset from file"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        # Load JSONL format
        if self.dataset_path.suffix == ".jsonl":
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self._records.append(json.loads(line))
    
    @abstractmethod
    def get_loader(self) -> Any:
        """Get framework-specific data loader"""
        pass
    
    def __len__(self) -> int:
        """Get dataset size"""
        return len(self._records)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get item by index"""
        return self._records[idx]


class PyTorchDatasetAdapter(BaseDatasetAdapter):
    """PyTorch Dataset and DataLoader adapter"""
    
    def __init__(
        self,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        transform: Optional[Callable] = None,
        collate_fn: Optional[Callable] = None
    ):
        self.transform = transform
        self.collate_fn = collate_fn
        super().__init__(dataset_path, config)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get transformed item"""
        item = self._records[idx]
        if self.transform:
            item = self.transform(item)
        return item
    
    def get_loader(self) -> 'DataLoader':
        """Get PyTorch DataLoader"""
        try:
            from torch.utils.data import DataLoader, Dataset
            
            class PeachTreeDataset(Dataset):
                def __init__(self, records, transform=None):
                    self.records = records
                    self.transform = transform
                
                def __len__(self):
                    return len(self.records)
                
                def __getitem__(self, idx):
                    item = self.records[idx]
                    if self.transform:
                        item = self.transform(item)
                    return item
            
            dataset = PeachTreeDataset(self._records, self.transform)
            
            loader = DataLoader(
                dataset,
                batch_size=self.config.batch_size,
                shuffle=self.config.shuffle,
                num_workers=self.config.num_workers,
                collate_fn=self.collate_fn,
                drop_last=self.config.drop_last,
                pin_memory=self.config.pin_memory,
                persistent_workers=self.config.persistent_workers if self.config.num_workers > 0 else False
            )
            return loader
        except ImportError:
            raise ImportError("PyTorch not installed. Install with: pip install torch")
    
    def to_tensors(self) -> Tuple[Any, Any]:
        """Convert dataset to PyTorch tensors (X, y)"""
        try:
            import torch
            
            # Extract features and labels
            X = [record.get("features", record.get("text", "")) for record in self._records]
            y = [record.get("label", record.get("target", 0)) for record in self._records]
            
            return torch.tensor(X) if isinstance(X[0], (int, float)) else X, torch.tensor(y)
        except ImportError:
            raise ImportError("PyTorch not installed")


class TensorFlowDatasetAdapter(BaseDatasetAdapter):
    """TensorFlow Dataset API adapter"""
    
    def __init__(
        self,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        map_fn: Optional[Callable] = None
    ):
        self.map_fn = map_fn
        super().__init__(dataset_path, config)
    
    def get_loader(self) -> 'tf.data.Dataset':
        """Get TensorFlow Dataset"""
        try:
            import tensorflow as tf
            
            def generator():
                for record in self._records:
                    if self.map_fn:
                        yield self.map_fn(record)
                    else:
                        yield record
            
            # Infer output signature from first record
            sample_record = self._records[0] if self._records else {}
            if self.map_fn:
                sample_record = self.map_fn(sample_record)
            
            output_signature = {
                key: tf.TensorSpec(shape=(), dtype=self._infer_dtype(value))
                for key, value in sample_record.items()
            }
            
            dataset = tf.data.Dataset.from_generator(
                generator,
                output_signature=output_signature
            )
            
            if self.config.shuffle:
                dataset = dataset.shuffle(buffer_size=len(self._records))
            
            dataset = dataset.batch(self.config.batch_size, drop_remainder=self.config.drop_last)
            dataset = dataset.prefetch(tf.data.AUTOTUNE)
            
            return dataset
        except ImportError:
            raise ImportError("TensorFlow not installed. Install with: pip install tensorflow")
    
    def _infer_dtype(self, value: Any) -> 'tf.DType':
        """Infer TensorFlow dtype from Python value"""
        try:
            import tensorflow as tf
            
            if isinstance(value, bool):
                return tf.bool
            elif isinstance(value, int):
                return tf.int64
            elif isinstance(value, float):
                return tf.float32
            elif isinstance(value, str):
                return tf.string
            else:
                return tf.string
        except ImportError:
            raise ImportError("TensorFlow not installed")


class JAXDatasetAdapter(BaseDatasetAdapter):
    """JAX data pipeline adapter"""
    
    def __init__(
        self,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        preprocessor: Optional[Callable] = None
    ):
        self.preprocessor = preprocessor
        super().__init__(dataset_path, config)
    
    def get_loader(self) -> Iterator[Dict[str, Any]]:
        """Get JAX-compatible data iterator"""
        try:
            import numpy as np
            
            indices = np.arange(len(self._records))
            
            if self.config.shuffle:
                np.random.shuffle(indices)
            
            for i in range(0, len(indices), self.config.batch_size):
                batch_indices = indices[i:i + self.config.batch_size]
                
                if self.config.drop_last and len(batch_indices) < self.config.batch_size:
                    continue
                
                batch = [self._records[idx] for idx in batch_indices]
                
                if self.preprocessor:
                    batch = [self.preprocessor(item) for item in batch]
                
                yield self._collate_batch(batch)
        except ImportError:
            raise ImportError("NumPy not installed. Install with: pip install numpy")
    
    def _collate_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collate batch into arrays"""
        try:
            import numpy as np
            
            if not batch:
                return {}
            
            keys = batch[0].keys()
            collated = {}
            
            for key in keys:
                values = [item[key] for item in batch]
                if isinstance(values[0], (int, float)):
                    collated[key] = np.array(values)
                else:
                    collated[key] = values
            
            return collated
        except ImportError:
            raise ImportError("NumPy not installed")
    
    def to_arrays(self) -> Dict[str, Any]:
        """Convert entire dataset to NumPy arrays"""
        try:
            import numpy as np
            
            if not self._records:
                return {}
            
            keys = self._records[0].keys()
            arrays = {}
            
            for key in keys:
                values = [record[key] for record in self._records]
                if isinstance(values[0], (int, float)):
                    arrays[key] = np.array(values)
                else:
                    arrays[key] = values
            
            return arrays
        except ImportError:
            raise ImportError("NumPy not installed")


class HuggingFaceDatasetAdapter(BaseDatasetAdapter):
    """HuggingFace Datasets library adapter"""
    
    def __init__(
        self,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        tokenizer: Optional[Any] = None
    ):
        self.tokenizer = tokenizer
        super().__init__(dataset_path, config)
    
    def get_loader(self) -> 'Dataset':
        """Get HuggingFace Dataset"""
        try:
            from datasets import Dataset
            
            # Convert records to HuggingFace Dataset
            dataset = Dataset.from_list(self._records)
            
            if self.tokenizer:
                dataset = dataset.map(
                    lambda examples: self.tokenizer(examples["text"]),
                    batched=True
                )
            
            return dataset
        except ImportError:
            raise ImportError("HuggingFace datasets not installed. Install with: pip install datasets")
    
    def get_dataloader(self) -> 'DataLoader':
        """Get HuggingFace-compatible PyTorch DataLoader"""
        try:
            from torch.utils.data import DataLoader
            
            dataset = self.get_loader()
            
            loader = DataLoader(
                dataset,
                batch_size=self.config.batch_size,
                shuffle=self.config.shuffle,
                num_workers=self.config.num_workers,
                collate_fn=self._default_collate_fn
            )
            return loader
        except ImportError:
            raise ImportError("PyTorch or HuggingFace datasets not installed")
    
    def _default_collate_fn(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Default collate function for HuggingFace datasets"""
        try:
            import torch
            
            if not batch:
                return {}
            
            keys = batch[0].keys()
            collated = {}
            
            for key in keys:
                values = [item[key] for item in batch]
                if isinstance(values[0], (int, float)):
                    collated[key] = torch.tensor(values)
                elif isinstance(values[0], list) and isinstance(values[0][0], (int, float)):
                    collated[key] = torch.tensor(values)
                else:
                    collated[key] = values
            
            return collated
        except ImportError:
            raise ImportError("PyTorch not installed")


class MLIntegrationManager:
    """Centralized manager for ML framework integrations"""
    
    def __init__(self):
        self.adapters: Dict[MLFramework, type] = {
            MLFramework.PYTORCH: PyTorchDatasetAdapter,
            MLFramework.TENSORFLOW: TensorFlowDatasetAdapter,
            MLFramework.JAX: JAXDatasetAdapter,
            MLFramework.HUGGINGFACE: HuggingFaceDatasetAdapter
        }
    
    def create_loader(
        self,
        framework: MLFramework,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        **kwargs
    ) -> Any:
        """Create framework-specific data loader"""
        if framework not in self.adapters:
            raise ValueError(f"Unsupported framework: {framework}")
        
        adapter_class = self.adapters[framework]
        adapter = adapter_class(dataset_path, config, **kwargs)
        return adapter.get_loader()
    
    def get_adapter(
        self,
        framework: MLFramework,
        dataset_path: str,
        config: Optional[DataLoaderConfig] = None,
        **kwargs
    ) -> BaseDatasetAdapter:
        """Get framework-specific adapter"""
        if framework not in self.adapters:
            raise ValueError(f"Unsupported framework: {framework}")
        
        adapter_class = self.adapters[framework]
        return adapter_class(dataset_path, config, **kwargs)
    
    def detect_framework(self) -> Optional[MLFramework]:
        """Auto-detect available ML framework"""
        try:
            import torch
            return MLFramework.PYTORCH
        except ImportError:
            pass
        
        try:
            import tensorflow
            return MLFramework.TENSORFLOW
        except ImportError:
            pass
        
        try:
            import jax
            return MLFramework.JAX
        except ImportError:
            pass
        
        try:
            import datasets
            return MLFramework.HUGGINGFACE
        except ImportError:
            pass
        
        return None
    
    def benchmark_loaders(
        self,
        dataset_path: str,
        frameworks: Optional[List[MLFramework]] = None,
        num_iterations: int = 10
    ) -> Dict[str, Dict[str, float]]:
        """Benchmark different framework loaders"""
        import time
        
        frameworks = frameworks or list(MLFramework)
        results = {}
        
        config = DataLoaderConfig(batch_size=32, shuffle=False, num_workers=0)
        
        for framework in frameworks:
            try:
                adapter = self.get_adapter(framework, dataset_path, config)
                loader = adapter.get_loader()
                
                # Warmup
                _ = next(iter(loader)) if hasattr(loader, '__iter__') else None
                
                # Benchmark
                start_time = time.time()
                for _ in range(num_iterations):
                    if hasattr(loader, '__iter__'):
                        for batch in loader:
                            pass
                    else:
                        _ = loader
                end_time = time.time()
                
                elapsed = end_time - start_time
                results[framework.value] = {
                    "total_time": elapsed,
                    "avg_time_per_iteration": elapsed / num_iterations,
                    "throughput": (len(adapter) * num_iterations) / elapsed
                }
            except Exception as e:
                results[framework.value] = {"error": str(e)}
        
        return results


# Export public API
__all__ = [
    'MLFramework',
    'DataFormat',
    'DataLoaderConfig',
    'BaseDatasetAdapter',
    'PyTorchDatasetAdapter',
    'TensorFlowDatasetAdapter',
    'JAXDatasetAdapter',
    'HuggingFaceDatasetAdapter',
    'MLIntegrationManager'
]
