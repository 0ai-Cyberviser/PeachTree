"""Advanced compression strategies for dataset storage optimization."""

import gzip
import lzma
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CompressionAlgorithm(Enum):
    """Compression algorithms."""
    
    GZIP = "gzip"
    LZMA = "lzma"
    ZLIB = "zlib"
    BZIP2 = "bzip2"
    NONE = "none"


class CompressionLevel(Enum):
    """Compression levels."""
    
    FASTEST = 1
    FAST = 3
    BALANCED = 6
    BEST = 9


@dataclass
class CompressionMetadata:
    """Metadata for compressed dataset."""
    
    compression_id: str
    algorithm: CompressionAlgorithm
    level: int
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compression_id": self.compression_id,
            "algorithm": self.algorithm.value,
            "level": self.level,
            "original_size_bytes": self.original_size_bytes,
            "compressed_size_bytes": self.compressed_size_bytes,
            "compression_ratio": self.compression_ratio,
            "created_at": self.created_at,
        }


@dataclass
class CompressionStats:
    """Statistics for compression operations."""
    
    files_processed: int = 0
    total_original_bytes: int = 0
    total_compressed_bytes: int = 0
    avg_compression_ratio: float = 0.0
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "files_processed": self.files_processed,
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "avg_compression_ratio": self.avg_compression_ratio,
            "duration_seconds": self.duration_seconds,
        }


class DatasetCompressor:
    """Compress datasets with various algorithms."""
    
    def __init__(self, algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP):
        """Initialize compressor."""
        self.algorithm = algorithm
    
    def compress_file(
        self,
        input_path: Path,
        output_path: Path,
        level: int = CompressionLevel.BALANCED.value,
    ) -> CompressionMetadata:
        """Compress a file."""
        from time import time
        
        time()
        original_size = input_path.stat().st_size
        
        with input_path.open("rb") as in_f:
            data = in_f.read()
        
        if self.algorithm == CompressionAlgorithm.GZIP:
            compressed = gzip.compress(data, compresslevel=level)
        
        elif self.algorithm == CompressionAlgorithm.LZMA:
            compressed = lzma.compress(data, preset=level)
        
        elif self.algorithm == CompressionAlgorithm.ZLIB:
            compressed = zlib.compress(data, level=level)
        
        elif self.algorithm == CompressionAlgorithm.BZIP2:
            import bz2
            compressed = bz2.compress(data, compresslevel=level)
        
        else:
            compressed = data
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("wb") as out_f:
            out_f.write(compressed)
        
        compressed_size = len(compressed)
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        return CompressionMetadata(
            compression_id=output_path.name,
            algorithm=self.algorithm,
            level=level,
            original_size_bytes=original_size,
            compressed_size_bytes=compressed_size,
            compression_ratio=compression_ratio,
        )
    
    def decompress_file(
        self,
        input_path: Path,
        output_path: Path,
    ) -> int:
        """Decompress a file."""
        with input_path.open("rb") as in_f:
            compressed = in_f.read()
        
        if self.algorithm == CompressionAlgorithm.GZIP:
            data = gzip.decompress(compressed)
        
        elif self.algorithm == CompressionAlgorithm.LZMA:
            data = lzma.decompress(compressed)
        
        elif self.algorithm == CompressionAlgorithm.ZLIB:
            data = zlib.decompress(compressed)
        
        elif self.algorithm == CompressionAlgorithm.BZIP2:
            import bz2
            data = bz2.decompress(compressed)
        
        else:
            data = compressed
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("wb") as out_f:
            out_f.write(data)
        
        return len(data)


class StreamingCompressor:
    """Compress datasets with streaming to handle large files."""
    
    def __init__(self, algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP):
        """Initialize streaming compressor."""
        self.algorithm = algorithm
    
    def compress_stream(
        self,
        input_path: Path,
        output_path: Path,
        level: int = CompressionLevel.BALANCED.value,
        chunk_size: int = 8192,
    ) -> CompressionMetadata:
        """Compress file using streaming."""
        from time import time
        
        time()
        original_size = 0
        compressed_size = 0
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.algorithm == CompressionAlgorithm.GZIP:
            with input_path.open("rb") as in_f:
                with gzip.open(output_path, "wb", compresslevel=level) as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        original_size += len(chunk)
        
        elif self.algorithm == CompressionAlgorithm.LZMA:
            with input_path.open("rb") as in_f:
                with lzma.open(output_path, "wb", preset=level) as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        original_size += len(chunk)
        
        elif self.algorithm == CompressionAlgorithm.BZIP2:
            import bz2
            with input_path.open("rb") as in_f:
                with bz2.open(output_path, "wb", compresslevel=level) as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        original_size += len(chunk)
        
        else:
            # No compression - just copy
            with input_path.open("rb") as in_f:
                with output_path.open("wb") as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        original_size += len(chunk)
        
        compressed_size = output_path.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        return CompressionMetadata(
            compression_id=output_path.name,
            algorithm=self.algorithm,
            level=level,
            original_size_bytes=original_size,
            compressed_size_bytes=compressed_size,
            compression_ratio=compression_ratio,
        )
    
    def decompress_stream(
        self,
        input_path: Path,
        output_path: Path,
        chunk_size: int = 8192,
    ) -> int:
        """Decompress file using streaming."""
        decompressed_size = 0
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.algorithm == CompressionAlgorithm.GZIP:
            with gzip.open(input_path, "rb") as in_f:
                with output_path.open("wb") as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        decompressed_size += len(chunk)
        
        elif self.algorithm == CompressionAlgorithm.LZMA:
            with lzma.open(input_path, "rb") as in_f:
                with output_path.open("wb") as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        decompressed_size += len(chunk)
        
        elif self.algorithm == CompressionAlgorithm.BZIP2:
            import bz2
            with bz2.open(input_path, "rb") as in_f:
                with output_path.open("wb") as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        decompressed_size += len(chunk)
        
        else:
            # No compression - just copy
            with input_path.open("rb") as in_f:
                with output_path.open("wb") as out_f:
                    while True:
                        chunk = in_f.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_f.write(chunk)
                        decompressed_size += len(chunk)
        
        return decompressed_size


class CompressionAnalyzer:
    """Analyze compression effectiveness."""
    
    def __init__(self):
        """Initialize compression analyzer."""
        self.stats = CompressionStats()
    
    def benchmark_algorithms(
        self,
        dataset_path: Path,
        algorithms: Optional[List[CompressionAlgorithm]] = None,
    ) -> List[CompressionMetadata]:
        """Benchmark different compression algorithms."""
        from tempfile import NamedTemporaryFile
        
        if algorithms is None:
            algorithms = [
                CompressionAlgorithm.GZIP,
                CompressionAlgorithm.LZMA,
                CompressionAlgorithm.ZLIB,
                CompressionAlgorithm.BZIP2,
            ]
        
        results = []
        
        for algorithm in algorithms:
            compressor = DatasetCompressor(algorithm)
            
            with NamedTemporaryFile(delete=False, suffix=f".{algorithm.value}") as tmp:
                tmp_path = Path(tmp.name)
            
            try:
                metadata = compressor.compress_file(dataset_path, tmp_path)
                results.append(metadata)
            
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
        
        return results
    
    def recommend_algorithm(
        self,
        dataset_path: Path,
    ) -> CompressionAlgorithm:
        """Recommend best compression algorithm."""
        results = self.benchmark_algorithms(dataset_path)
        
        # Find algorithm with best compression ratio
        best = min(results, key=lambda r: r.compression_ratio)
        
        return best.algorithm
    
    def estimate_compressed_size(
        self,
        original_size_bytes: int,
        algorithm: CompressionAlgorithm,
        typical_ratio: float = 0.3,
    ) -> int:
        """Estimate compressed size."""
        # Typical compression ratios
        ratios = {
            CompressionAlgorithm.GZIP: 0.3,
            CompressionAlgorithm.LZMA: 0.25,
            CompressionAlgorithm.ZLIB: 0.35,
            CompressionAlgorithm.BZIP2: 0.28,
            CompressionAlgorithm.NONE: 1.0,
        }
        
        ratio = ratios.get(algorithm, typical_ratio)
        
        return int(original_size_bytes * ratio)


class BatchCompressor:
    """Compress multiple datasets in batch."""
    
    def __init__(self, algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP):
        """Initialize batch compressor."""
        self.algorithm = algorithm
        self.compressor = StreamingCompressor(algorithm)
    
    def compress_datasets(
        self,
        dataset_paths: List[Path],
        output_dir: Path,
        level: int = CompressionLevel.BALANCED.value,
    ) -> List[CompressionMetadata]:
        """Compress multiple datasets."""
        from time import time
        
        time()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for dataset_path in dataset_paths:
            output_path = output_dir / f"{dataset_path.name}.{self.algorithm.value}"
            
            metadata = self.compressor.compress_stream(
                dataset_path,
                output_path,
                level=level,
            )
            
            results.append(metadata)
        
        return results
    
    def decompress_datasets(
        self,
        compressed_paths: List[Path],
        output_dir: Path,
    ) -> List[int]:
        """Decompress multiple datasets."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        sizes = []
        
        for compressed_path in compressed_paths:
            # Remove compression extension
            base_name = compressed_path.stem
            output_path = output_dir / base_name
            
            size = self.compressor.decompress_stream(compressed_path, output_path)
            sizes.append(size)
        
        return sizes
    
    def get_statistics(
        self,
        results: List[CompressionMetadata],
    ) -> CompressionStats:
        """Get compression statistics."""
        total_original = sum(r.original_size_bytes for r in results)
        total_compressed = sum(r.compressed_size_bytes for r in results)
        
        avg_ratio = total_compressed / total_original if total_original > 0 else 1.0
        
        return CompressionStats(
            files_processed=len(results),
            total_original_bytes=total_original,
            total_compressed_bytes=total_compressed,
            avg_compression_ratio=avg_ratio,
        )
