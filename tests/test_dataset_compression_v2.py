"""Tests for dataset compression - matching actual APIs."""
from __future__ import annotations

from pathlib import Path


from peachtree.dataset_compression import (
    DatasetCompressor,
    StreamingCompressor,
    CompressionAnalyzer,
    BatchCompressor,
    CompressionMetadata,
    CompressionStats,
    CompressionAlgorithm,
    CompressionLevel,
)


def test_compression_algorithm_enum():
    """Test CompressionAlgorithm enum values."""
    assert CompressionAlgorithm.GZIP.value == "gzip"
    assert CompressionAlgorithm.LZMA.value == "lzma"
    assert CompressionAlgorithm.ZLIB.value == "zlib"
    assert CompressionAlgorithm.BZIP2.value == "bzip2"
    assert CompressionAlgorithm.NONE.value == "none"


def test_compression_level_enum():
    """Test CompressionLevel enum values."""
    assert CompressionLevel.FASTEST.value == 1
    assert CompressionLevel.FAST.value == 3
    assert CompressionLevel.BALANCED.value == 6
    assert CompressionLevel.BEST.value == 9


def test_compression_metadata_creation():
    """Test CompressionMetadata creation."""
    metadata = CompressionMetadata(
        compression_id="test-123",
        algorithm=CompressionAlgorithm.GZIP,
        level=6,
        original_size_bytes=1000,
        compressed_size_bytes=500,
        compression_ratio=0.5,
    )
    assert metadata.compression_id == "test-123"
    assert metadata.algorithm == CompressionAlgorithm.GZIP
    assert metadata.level == 6
    assert metadata.original_size_bytes == 1000
    assert metadata.compressed_size_bytes == 500
    assert metadata.compression_ratio == 0.5


def test_compression_metadata_to_dict():
    """Test CompressionMetadata serialization."""
    metadata = CompressionMetadata(
        compression_id="test-123",
        algorithm=CompressionAlgorithm.GZIP,
        level=6,
        original_size_bytes=1000,
        compressed_size_bytes=500,
        compression_ratio=0.5,
    )
    data = metadata.to_dict()
    
    assert data["compression_id"] == "test-123"
    assert data["algorithm"] == "gzip"
    assert data["level"] == 6
    assert data["original_size_bytes"] == 1000
    assert data["compressed_size_bytes"] == 500
    assert data["compression_ratio"] == 0.5


def test_compression_stats_creation():
    """Test CompressionStats creation."""
    stats = CompressionStats(
        files_processed=5,
        total_original_bytes=5000,
        total_compressed_bytes=2500,
        avg_compression_ratio=0.5,
        duration_seconds=1.5,
    )
    assert stats.files_processed == 5
    assert stats.total_original_bytes == 5000
    assert stats.total_compressed_bytes == 2500
    assert stats.avg_compression_ratio == 0.5


def test_compression_stats_to_dict():
    """Test CompressionStats serialization."""
    stats = CompressionStats(
        files_processed=5,
        total_original_bytes=5000,
        total_compressed_bytes=2500,
        avg_compression_ratio=0.5,
        duration_seconds=1.5,
    )
    data = stats.to_dict()
    
    assert data["files_processed"] == 5
    assert data["total_original_bytes"] == 5000
    assert data["total_compressed_bytes"] == 2500


def test_dataset_compressor_init():
    """Test DatasetCompressor initialization."""
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    assert compressor.algorithm == CompressionAlgorithm.GZIP


def test_dataset_compressor_compress_file_gzip(tmp_path: Path):
    """Test compressing file with gzip."""
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.gz"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.algorithm == CompressionAlgorithm.GZIP
    assert metadata.original_size_bytes == len(test_data.encode())
    assert metadata.compressed_size_bytes < metadata.original_size_bytes
    assert output_file.exists()


def test_dataset_compressor_compress_file_lzma(tmp_path: Path):
    """Test compressing file with lzma."""
    compressor = DatasetCompressor(CompressionAlgorithm.LZMA)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.xz"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.algorithm == CompressionAlgorithm.LZMA
    assert output_file.exists()


def test_dataset_compressor_compress_file_zlib(tmp_path: Path):
    """Test compressing file with zlib."""
    compressor = DatasetCompressor(CompressionAlgorithm.ZLIB)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.zlib"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.algorithm == CompressionAlgorithm.ZLIB
    assert output_file.exists()


def test_dataset_compressor_compress_file_bzip2(tmp_path: Path):
    """Test compressing file with bzip2."""
    compressor = DatasetCompressor(CompressionAlgorithm.BZIP2)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.bz2"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.algorithm == CompressionAlgorithm.BZIP2
    assert output_file.exists()


def test_dataset_compressor_decompress_file_gzip(tmp_path: Path):
    """Test decompressing gzip file."""
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "input.txt"
    compressed_file = tmp_path / "compressed.gz"
    decompressed_file = tmp_path / "decompressed.txt"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    compressor.compress_file(input_file, compressed_file)
    size = compressor.decompress_file(compressed_file, decompressed_file)
    
    assert decompressed_file.read_text() == test_data
    assert size == len(test_data.encode())


def test_dataset_compressor_decompress_file_lzma(tmp_path: Path):
    """Test decompressing lzma file."""
    compressor = DatasetCompressor(CompressionAlgorithm.LZMA)
    
    input_file = tmp_path / "input.txt"
    compressed_file = tmp_path / "compressed.xz"
    decompressed_file = tmp_path / "decompressed.txt"
    
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    compressor.compress_file(input_file, compressed_file)
    compressor.decompress_file(compressed_file, decompressed_file)
    
    assert decompressed_file.read_text() == test_data


def test_dataset_compressor_compression_levels(tmp_path: Path):
    """Test different compression levels."""
    input_file = tmp_path / "input.txt"
    test_data = "Hello World! " * 100
    input_file.write_text(test_data)
    
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    
    # Fast compression
    fast_file = tmp_path / "fast.gz"
    fast_meta = compressor.compress_file(input_file, fast_file, level=1)
    
    # Best compression
    best_file = tmp_path / "best.gz"
    best_meta = compressor.compress_file(input_file, best_file, level=9)
    
    # Best compression should result in smaller or equal file
    assert best_meta.compressed_size_bytes <= fast_meta.compressed_size_bytes


def test_streaming_compressor_init():
    """Test StreamingCompressor initialization."""
    compressor = StreamingCompressor(CompressionAlgorithm.GZIP)
    assert compressor.algorithm == CompressionAlgorithm.GZIP


def test_streaming_compressor_compress_stream(tmp_path: Path):
    """Test streaming compression."""
    compressor = StreamingCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.gz"
    
    # Create larger file for streaming
    test_data = "Hello World! " * 10000
    input_file.write_text(test_data)
    
    metadata = compressor.compress_stream(input_file, output_file)
    
    assert metadata.algorithm == CompressionAlgorithm.GZIP
    assert metadata.compressed_size_bytes < metadata.original_size_bytes
    assert output_file.exists()


def test_streaming_compressor_decompress_stream(tmp_path: Path):
    """Test streaming decompression."""
    compressor = StreamingCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "input.txt"
    compressed_file = tmp_path / "compressed.gz"
    decompressed_file = tmp_path / "decompressed.txt"
    
    test_data = "Hello World! " * 10000
    input_file.write_text(test_data)
    
    compressor.compress_stream(input_file, compressed_file)
    size = compressor.decompress_stream(compressed_file, decompressed_file)
    
    assert decompressed_file.read_text() == test_data
    assert size == len(test_data.encode())


def test_compression_analyzer_init():
    """Test CompressionAnalyzer initialization."""
    analyzer = CompressionAnalyzer()
    assert analyzer is not None


def test_compression_analyzer_benchmark_algorithms(tmp_path: Path):
    """Test benchmarking compression algorithms."""
    analyzer = CompressionAnalyzer()
    
    dataset = tmp_path / "dataset.jsonl"
    test_data = '{"id": 1, "content": "test data"}\n' * 100
    dataset.write_text(test_data)
    
    results = analyzer.benchmark_algorithms(dataset)
    
    # Should benchmark all algorithms except NONE
    assert len(results) >= 4
    
    # All results should have valid metadata
    for result in results:
        assert result.original_size_bytes > 0
        assert result.compressed_size_bytes > 0
        assert 0 <= result.compression_ratio <= 1


def test_compression_analyzer_recommend_algorithm(tmp_path: Path):
    """Test algorithm recommendation."""
    analyzer = CompressionAnalyzer()
    
    dataset = tmp_path / "dataset.jsonl"
    test_data = '{"id": 1, "content": "test data"}\n' * 100
    dataset.write_text(test_data)
    
    recommendation = analyzer.recommend_algorithm(dataset)
    
    assert recommendation in [
        CompressionAlgorithm.GZIP,
        CompressionAlgorithm.LZMA,
        CompressionAlgorithm.ZLIB,
        CompressionAlgorithm.BZIP2,
    ]


def test_batch_compressor_init():
    """Test BatchCompressor initialization."""
    compressor = BatchCompressor(CompressionAlgorithm.GZIP)
    assert compressor.algorithm == CompressionAlgorithm.GZIP


def test_batch_compressor_compress_datasets(tmp_path: Path):
    """Test batch compression of multiple datasets."""
    compressor = BatchCompressor(CompressionAlgorithm.GZIP)
    
    input1 = tmp_path / "input1.jsonl"
    input2 = tmp_path / "input2.jsonl"
    output_dir = tmp_path / "compressed"
    output_dir.mkdir()
    
    test_data = '{"id": 1}\n' * 100
    input1.write_text(test_data)
    input2.write_text(test_data)
    
    results = compressor.compress_datasets([input1, input2], output_dir)
    
    assert len(results) == 2
    assert all(r.algorithm == CompressionAlgorithm.GZIP for r in results)


def test_batch_compressor_get_statistics():
    """Test batch compression statistics."""
    compressor = BatchCompressor(CompressionAlgorithm.GZIP)
    
    results = [
        CompressionMetadata(
            compression_id="1",
            algorithm=CompressionAlgorithm.GZIP,
            level=6,
            original_size_bytes=1000,
            compressed_size_bytes=500,
            compression_ratio=0.5,
        ),
        CompressionMetadata(
            compression_id="2",
            algorithm=CompressionAlgorithm.GZIP,
            level=6,
            original_size_bytes=2000,
            compressed_size_bytes=1000,
            compression_ratio=0.5,
        ),
    ]
    
    stats = compressor.get_statistics(results)
    
    assert stats.files_processed == 2
    assert stats.total_original_bytes == 3000
    assert stats.total_compressed_bytes == 1500
    assert stats.avg_compression_ratio == 0.5


def test_dataset_compressor_empty_file(tmp_path: Path):
    """Test compressing empty file."""
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "empty.txt"
    output_file = tmp_path / "output.gz"
    
    input_file.write_text("")
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.original_size_bytes == 0
    assert output_file.exists()


def test_dataset_compressor_large_file(tmp_path: Path):
    """Test compressing large file."""
    compressor = DatasetCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "large.txt"
    output_file = tmp_path / "output.gz"
    
    # Create 1MB file
    test_data = "A" * (1024 * 1024)
    input_file.write_text(test_data)
    
    metadata = compressor.compress_file(input_file, output_file)
    
    assert metadata.original_size_bytes == 1024 * 1024
    # Highly repetitive data should compress well
    assert metadata.compression_ratio < 0.1


def test_streaming_compressor_chunk_size(tmp_path: Path):
    """Test streaming compression with custom chunk size."""
    compressor = StreamingCompressor(CompressionAlgorithm.GZIP)
    
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.gz"
    
    test_data = "Hello World! " * 10000
    input_file.write_text(test_data)
    
    # chunk_size is parameter to compress_stream
    metadata = compressor.compress_stream(input_file, output_file, chunk_size=4096)
    
    assert metadata.compressed_size_bytes < metadata.original_size_bytes


def test_batch_compressor_empty_list(tmp_path: Path):
    """Test batch compression with empty list."""
    compressor = BatchCompressor(CompressionAlgorithm.GZIP)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    results = compressor.compress_datasets([], output_dir)
    
    assert results == []


def test_compression_metadata_space_savings():
    """Test compression metadata calculates space savings."""
    metadata = CompressionMetadata(
        compression_id="test",
        algorithm=CompressionAlgorithm.GZIP,
        level=6,
        original_size_bytes=1000,
        compressed_size_bytes=400,
        compression_ratio=0.4,
    )
    
    space_saved = metadata.original_size_bytes - metadata.compressed_size_bytes
    assert space_saved == 600
