#!/usr/bin/env python3
"""
Complete Dataset Merger
Merges all datasets into ultimate training corpus:
- Base Hancock (4,951 records)
- Complete Kali system extraction
- Iterative refinement synthetic data
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_datasets():
    """Merge all available datasets"""
    logger.info("🔄 Merging all datasets...")
    
    all_records = []
    sources = []
    
    # 1. Base Hancock dataset
    base_dataset = Path("data/hancock/unified-expanded.jsonl")
    if base_dataset.exists():
        count = 0
        with open(base_dataset, 'r') as f:
            for line in f:
                if line.strip():
                    all_records.append(json.loads(line))
                    count += 1
        sources.append(("Base Hancock", count))
        logger.info(f"✅ Added {count:,} records from base dataset")
    
    # 2. Complete Kali extraction
    kali_dir = Path("data/kali-complete")
    if kali_dir.exists():
        for kali_file in kali_dir.glob("kali_complete_*.jsonl"):
            count = 0
            with open(kali_file, 'r') as f:
                for line in f:
                    if line.strip():
                        all_records.append(json.loads(line))
                        count += 1
            sources.append((f"Kali System ({kali_file.name})", count))
            logger.info(f"✅ Added {count:,} records from Kali extraction")
    
    # 3. Iterative refinement synthetic data
    iter_dir = Path("models/hancock-iterative")
    if iter_dir.exists():
        for iter_file in iter_dir.glob("dataset_iteration_*.jsonl"):
            # Only use final iteration
            iteration_num = int(iter_file.stem.split('_')[-1])
            if iteration_num > 10:  # Only use mature iterations
                count = 0
                with open(iter_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            all_records.append(json.loads(line))
                            count += 1
                sources.append((f"Iteration {iteration_num}", count))
                logger.info(f"✅ Added {count:,} records from iteration {iteration_num}")
    
    # Deduplicate by source_digest
    logger.info("🔍 Deduplicating...")
    seen_digests = set()
    unique_records = []
    
    for record in all_records:
        digest = record.get('source_digest', record.get('id', ''))
        if digest not in seen_digests:
            seen_digests.add(digest)
            unique_records.append(record)
    
    logger.info(f"   Before dedup: {len(all_records):,}")
    logger.info(f"   After dedup: {len(unique_records):,}")
    logger.info(f"   Duplicates removed: {len(all_records) - len(unique_records):,}")
    
    # Save merged dataset
    output_file = Path("data/hancock/ultimate-training-corpus.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        for record in unique_records:
            f.write(json.dumps(record, sort_keys=True) + '\n')
    
    # Save summary
    summary = {
        "total_records": len(unique_records),
        "sources": [{"name": name, "records": count} for name, count in sources],
        "duplicates_removed": len(all_records) - len(unique_records),
        "output_file": str(output_file),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    summary_file = Path("data/hancock/merge_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("\n" + "="*60)
    logger.info("DATASET MERGE COMPLETE")
    logger.info("="*60)
    logger.info(f"Total unique records: {len(unique_records):,}")
    logger.info(f"\nSources:")
    for name, count in sources:
        logger.info(f"  {name}: {count:,}")
    logger.info(f"\nOutput: {output_file}")
    logger.info(f"Summary: {summary_file}")
    
    return summary


if __name__ == "__main__":
    merge_datasets()
