# Performance Optimization Guide

Guide to optimizing PeachTree for large-scale dataset building.

## Benchmarking Baseline

Before optimizing, establish baseline metrics:

```bash
# Measure build time
time peachtree build --input data/ --output dataset.jsonl

# Measure memory usage
/usr/bin/time -v peachtree build --input data/ --output dataset.jsonl

# Measure deduplication time
time peachtree dedup --input dataset.jsonl --output dedup.jsonl

# Count records
wc -l dataset.jsonl
```

Expected baseline (for 100K records):
- Build time: 2-5 minutes
- Memory: 500MB - 2GB
- Dedup time: 1-3 minutes

## Quick Wins (Easy Optimizations)

### 1. Use Simpler Deduplication

```yaml
# peachtree.yaml
deduplication:
  method: content_hash  # Fastest
  # method: fuzzy      # Slower
  # method: semantic   # Slowest
```

**Performance impact:** 5-10x faster

```bash
# Benchmark each method
time peachtree build --dedup-method content_hash --input data/ --output d1.jsonl
time peachtree build --dedup-method fuzzy --input data/ --output d2.jsonl
time peachtree build --dedup-method semantic --input data/ --output d3.jsonl
```

### 2. Filter Source Data First

```bash
# Before building, filter repository
find /repo -name "*.py" -o -name "*.md" | wc -l  # Check size

# Keep only useful files
find /repo -type f \
  -name "*.py" \
  -o -name "*.md" \
  -o -name "*.txt" \
  > filtered-files.txt

# Build from filtered list
peachtree build --input filtered-files.txt --output dataset.jsonl
```

**Performance impact:** 2-5x faster (depends on filtering)

### 3. Skip Expensive Safety Gates

```yaml
# peachtree.yaml
safety_gates:
  secret_filter: true      # Fast, keep enabled
  license_gate: false      # Expensive, disable if not needed
  content_filter: true     # Medium, can disable
  semantic_analysis: false # Expensive, disable for speed
```

**Performance impact:** 3-10x faster (depends on gates)

### 4. Process in Parallel

```bash
# Split source data
split -n l/4 filtered-files.txt chunk_

# Process chunks in parallel
for chunk in chunk_*; do
  peachtree build --input $chunk --output $chunk.jsonl &
done
wait

# Merge results
cat chunk_*.jsonl > combined.jsonl
peachtree dedup --input combined.jsonl --output final.jsonl
```

**Performance impact:** Up to 4x faster (with 4 processes)

## Memory Optimization

### Monitor Memory Usage

```bash
# Real-time monitoring
watch -n 1 'ps aux | grep peachtree | grep -v grep'

# Get peak memory usage
/usr/bin/time -v peachtree build --input data/ --output dataset.jsonl 2>&1 | grep "Maximum resident"

# Profile memory per function
python -m memory_profiler src/peachtree/builder.py
```

### Reduce Memory Footprint

```python
# In .peachtree.yaml
settings:
  chunk_size: 1000        # Smaller chunks = less memory
  cache_size: 100         # Smaller cache
  buffer_size: 1024       # Smaller buffers

# Or via CLI
peachtree build \
  --input data/ \
  --output dataset.jsonl \
  --chunk-size 500 \
  --buffer-size 512
```

**Memory savings:** 50-70% reduction

## CPU Optimization

### Profile CPU Usage

```bash
# Identify hot spots
python -m cProfile -s cumtime -m peachtree build --input data/ --output dataset.jsonl | head -20

# Generate flame graph
python -m py_spy record -o profile.svg -- peachtree build --input data/ --output dataset.jsonl
```

### Optimize CPU-Intensive Operations

```yaml
# peachtree.yaml
deduplication:
  method: content_hash     # Fastest (SHA-256)
  similarity_threshold: 0.95  # Higher = faster
  
quality_scoring:
  fast_mode: true          # Skip expensive metrics
  
safety_gates:
  semantic_analysis: false # Disable expensive NLP
```

## Storage Optimization

### Reduce Disk I/O

```bash
# Use temporary RAM disk for intermediate files
mkdir -p /dev/shm/peachtree
cd /dev/shm/peachtree

# Build dataset in RAM (faster I/O)
peachtree build --input /path/to/data/ --output dataset.jsonl

# Copy back to persistent storage
cp dataset.jsonl /persistent/storage/

# Clean up
cd /
rm -rf /dev/shm/peachtree
```

**Performance impact:** 2-3x faster I/O

### Compress Output

```bash
# Build uncompressed, then compress
peachtree build --input data/ --output dataset.jsonl
gzip -9 dataset.jsonl  # Best compression (slower)
# or
gzip -1 dataset.jsonl  # Fastest compression

# Decompress for processing
gunzip dataset.jsonl.gz

# Verify integrity
zcat dataset.jsonl.gz | wc -l
```

## Network Optimization

### For Remote Repositories

```bash
# Clone locally first (faster)
git clone https://github.com/project/repo.git local-repo
peachtree build --input local-repo --output dataset.jsonl

# Instead of:
peachtree build --input /tmp/github-cache/ --output dataset.jsonl
```

### Cache Remote Data

```bash
# Clone once, reuse
CACHE_DIR=~/.peachtree/cache
git clone https://github.com/project/repo.git $CACHE_DIR/repo
peachtree build --input $CACHE_DIR/repo --output dataset1.jsonl
peachtree build --input $CACHE_DIR/repo --output dataset2.jsonl
```

## Scaling to Very Large Datasets (100M+ records)

### Distributed Processing

```bash
# Split into manageable chunks
split -n l/10 large-file-list.txt chunk_

# Process chunks on different machines
# Machine 1:
peachtree build --input chunk_aa --output chunk_aa.jsonl

# Machine 2:
peachtree build --input chunk_ab --output chunk_ab.jsonl

# etc...

# Merge results (on one machine)
cat chunk_*.jsonl > combined.jsonl

# Deduplicate globally
peachtree dedup --input combined.jsonl --output final.jsonl
```

### Stream Processing

```python
# Process line-by-line without loading entire dataset
import json
from peachtree import DatasetBuilder

builder = DatasetBuilder()

with open('large-dataset.jsonl') as f_in:
    with open('processed.jsonl', 'w') as f_out:
        for line in f_in:
            record = json.loads(line)
            # Process one record at a time
            processed = builder.process(record)
            f_out.write(json.dumps(processed) + '\n')
```

## Benchmarking Results

### Example Performance Metrics

```
Test Configuration:
- Python: 3.10.5
- CPU: 8 cores @ 3.2 GHz
- RAM: 16 GB
- SSD: 500 GB

Dataset: 1M records

Default Settings:
  Build time: 12 minutes
  Memory peak: 3.2 GB
  Final size: 450 MB

Optimized Settings (chunk_size=1000, content_hash dedup):
  Build time: 3 minutes
  Memory peak: 800 MB
  Final size: 450 MB

Speed improvement: 4x faster
Memory improvement: 4x less
```

## Checklist for Performance Tuning

- [ ] Establish baseline metrics
- [ ] Filter source data before building
- [ ] Use content_hash deduplication
- [ ] Disable unnecessary safety gates
- [ ] Adjust chunk_size and buffer_size
- [ ] Use RAM disk for temporary files
- [ ] Monitor memory and CPU usage
- [ ] Profile hot spots
- [ ] Test with representative data
- [ ] Document your optimizations

## When to Optimize

**Don't optimize:**
- Before baseline measurements
- Without profiling (guessing is dangerous)
- At the cost of correctness
- Single operations (focus on pipelines)

**Do optimize:**
- Repeated operations
- Known bottlenecks
- After profiling shows hot spots
- When serving users

## Tools & Resources

- **Python profiler:** `python -m cProfile`
- **Memory profiler:** `python -m memory_profiler`
- **py-spy:** `pip install py-spy`
- **Flame graphs:** `py_spy record -o profile.svg`
- **htop:** Real-time system monitor
- **time:** Measure execution time

---

**Last Updated:** 2026-04-27

See [DEVELOPMENT.md](DEVELOPMENT.md) for profiling examples.
