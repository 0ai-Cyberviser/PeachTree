"""
Tests for dataset_catalog module
"""
import pytest
import json
from peachtree.dataset_catalog import (
    DatasetCatalog,
    DatasetCatalogEntry,
    SearchResult,
)


@pytest.fixture
def test_datasets(tmp_path):
    """Create multiple test datasets"""
    datasets = []
    
    # Dataset 1
    ds1 = tmp_path / "dataset1.jsonl"
    records1 = [{"id": f"{i}", "content": f"Content {i}", "source_repo": "repo1"} for i in range(100)]
    ds1.write_text("\n".join(json.dumps(r) for r in records1) + "\n")
    datasets.append(ds1)
    
    # Dataset 2
    ds2 = tmp_path / "dataset2.jsonl"
    records2 = [{"id": f"{i}", "content": f"Text {i}", "source_repo": "repo2"} for i in range(50)]
    ds2.write_text("\n".join(json.dumps(r) for r in records2) + "\n")
    datasets.append(ds2)
    
    # Dataset 3
    ds3 = tmp_path / "dataset3.jsonl"
    records3 = [{"id": f"{i}", "content": f"Data {i}", "source_repo": "repo1"} for i in range(200)]
    ds3.write_text("\n".join(json.dumps(r) for r in records3) + "\n")
    datasets.append(ds3)
    
    return datasets


def test_catalog_entry_creation():
    """Test DatasetCatalogEntry initialization"""
    entry = DatasetCatalogEntry(
        dataset_path="test.jsonl",
        dataset_name="test",
        record_count=100,
        file_size_mb=1.5,
        created_timestamp="2026-04-27T10:00:00",
        modified_timestamp="2026-04-27T11:00:00",
        tags=["training", "v1"],
    )
    
    assert entry.record_count == 100
    assert "training" in entry.tags


def test_catalog_entry_matches_query():
    """Test query matching"""
    entry = DatasetCatalogEntry(
        dataset_path="test.jsonl",
        dataset_name="training-dataset",
        record_count=100,
        file_size_mb=1.0,
        created_timestamp="2026-04-27T10:00:00",
        modified_timestamp="2026-04-27T10:00:00",
        tags=["ml", "nlp"],
        source_repos=["repo1"],
    )
    
    # Match in name
    assert entry.matches_query("training")
    
    # Match in tags
    assert entry.matches_query("nlp")
    
    # Match in repos
    assert entry.matches_query("repo1")
    
    # No match
    assert not entry.matches_query("nonexistent")


def test_search_result_creation():
    """Test SearchResult dataclass"""
    entry = DatasetCatalogEntry(
        "test.jsonl", "test", 100, 1.0,
        "2026-04-27T10:00:00", "2026-04-27T10:00:00",
    )
    
    result = SearchResult(
        entry=entry,
        relevance_score=0.8,
        match_reasons=["High quality"],
    )
    
    assert result.relevance_score == 0.8
    assert len(result.match_reasons) == 1


def test_catalog_initialization(tmp_path):
    """Test catalog initialization"""
    index_path = tmp_path / "catalog.json"
    catalog = DatasetCatalog(index_path)
    
    assert catalog.index_path == index_path
    assert len(catalog.entries) == 0


def test_catalog_index_dataset(test_datasets):
    """Test indexing a dataset"""
    catalog = DatasetCatalog("/tmp/test-catalog.json")
    
    entry = catalog.index_dataset(
        test_datasets[0],
        tags=["training", "v1"],
        metadata={"version": "1.0"},
    )
    
    assert entry.dataset_name == "dataset1"
    assert entry.record_count == 100
    assert "training" in entry.tags
    assert entry.metadata["version"] == "1.0"


def test_catalog_index_dataset_extracts_repos(test_datasets):
    """Test that indexing extracts source repos"""
    catalog = DatasetCatalog("/tmp/test-catalog.json")
    
    entry = catalog.index_dataset(test_datasets[0])
    
    assert "repo1" in entry.source_repos


def test_catalog_index_nonexistent_dataset(tmp_path):
    """Test indexing nonexistent dataset raises error"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    with pytest.raises(FileNotFoundError):
        catalog.index_dataset(tmp_path / "nonexistent.jsonl")


def test_catalog_update_entry(test_datasets, tmp_path):
    """Test updating catalog entry"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0])
    
    catalog.update_entry(
        test_datasets[0],
        quality_score=85.0,
        tags=["v2", "production"],
    )
    
    entry = catalog.entries[str(test_datasets[0])]
    
    assert entry.quality_score == 85.0
    assert "production" in entry.tags


def test_catalog_update_nonexistent_entry(tmp_path):
    """Test updating nonexistent entry raises error"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    with pytest.raises(KeyError):
        catalog.update_entry("/nonexistent.jsonl", quality_score=90.0)


def test_catalog_remove_entry(test_datasets, tmp_path):
    """Test removing entry from catalog"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0])
    assert len(catalog.entries) == 1
    
    catalog.remove_entry(test_datasets[0])
    assert len(catalog.entries) == 0


def test_catalog_search_by_query(test_datasets, tmp_path):
    """Test searching by text query"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0], tags=["training"])
    catalog.index_dataset(test_datasets[1], tags=["validation"])
    
    results = catalog.search(query="dataset1")
    
    assert len(results) == 1
    assert results[0].entry.dataset_name == "dataset1"


def test_catalog_search_by_tags(test_datasets, tmp_path):
    """Test filtering by tags"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0], tags=["training", "v1"])
    catalog.index_dataset(test_datasets[1], tags=["validation", "v1"])
    catalog.index_dataset(test_datasets[2], tags=["test"])
    
    results = catalog.search(tags=["v1"])
    
    assert len(results) == 2


def test_catalog_search_by_quality(test_datasets, tmp_path):
    """Test filtering by quality score"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0])
    catalog.update_entry(test_datasets[0], quality_score=90.0)
    
    catalog.index_dataset(test_datasets[1])
    catalog.update_entry(test_datasets[1], quality_score=70.0)
    
    results = catalog.search(min_quality=80.0)
    
    assert len(results) == 1
    assert results[0].entry.quality_score == 90.0


def test_catalog_search_by_min_records(test_datasets, tmp_path):
    """Test filtering by minimum record count"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0])  # 100 records
    catalog.index_dataset(test_datasets[1])  # 50 records
    catalog.index_dataset(test_datasets[2])  # 200 records
    
    results = catalog.search(min_records=150)
    
    assert len(results) == 1
    assert results[0].entry.record_count == 200


def test_catalog_search_by_source_repo(test_datasets, tmp_path):
    """Test filtering by source repository"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds)
    
    results = catalog.search(source_repo="repo1")
    
    assert len(results) == 2  # dataset1 and dataset3


def test_catalog_search_combined_filters(test_datasets, tmp_path):
    """Test searching with multiple filters"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds, tags=["production"])
    
    catalog.update_entry(test_datasets[0], quality_score=95.0)
    catalog.update_entry(test_datasets[1], quality_score=75.0)
    catalog.update_entry(test_datasets[2], quality_score=85.0)
    
    results = catalog.search(
        tags=["production"],
        min_quality=80.0,
        min_records=100,
    )
    
    # Should return dataset1 (95, 100 records) and dataset3 (85, 200 records)
    assert len(results) == 2


def test_catalog_search_relevance_sorting(test_datasets, tmp_path):
    """Test that search results are sorted by relevance"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0], tags=["ml"])
    catalog.update_entry(test_datasets[0], quality_score=70.0)
    
    catalog.index_dataset(test_datasets[1], tags=["ml"])
    catalog.update_entry(test_datasets[1], quality_score=95.0)
    
    results = catalog.search(tags=["ml"])
    
    # Higher quality should rank higher
    assert results[0].entry.quality_score > results[1].entry.quality_score


def test_catalog_get_by_tag(test_datasets, tmp_path):
    """Test getting datasets by tag"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    catalog.index_dataset(test_datasets[0], tags=["training", "v1"])
    catalog.index_dataset(test_datasets[1], tags=["validation"])
    
    training_datasets = catalog.get_by_tag("training")
    
    assert len(training_datasets) == 1
    assert training_datasets[0].dataset_name == "dataset1"


def test_catalog_get_by_repo(test_datasets, tmp_path):
    """Test getting datasets by repository"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds)
    
    repo1_datasets = catalog.get_by_repo("repo1")
    
    assert len(repo1_datasets) == 2


def test_catalog_list_all(test_datasets, tmp_path):
    """Test listing all datasets"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds)
    
    all_datasets = catalog.list_all()
    
    assert len(all_datasets) == 3


def test_catalog_list_all_sorted_by_records(test_datasets, tmp_path):
    """Test listing sorted by record count"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds)
    
    datasets = catalog.list_all(sort_by="records")
    
    # Should be sorted by record count (descending)
    assert datasets[0].record_count == 200
    assert datasets[1].record_count == 100
    assert datasets[2].record_count == 50


def test_catalog_save_and_load(test_datasets, tmp_path):
    """Test saving and loading catalog"""
    index_path = tmp_path / "catalog.json"
    
    # Create and save
    catalog1 = DatasetCatalog(index_path)
    catalog1.index_dataset(test_datasets[0], tags=["v1"])
    catalog1.save()
    
    assert index_path.exists()
    
    # Load in new instance
    catalog2 = DatasetCatalog(index_path)
    
    assert len(catalog2.entries) == 1
    entry = list(catalog2.entries.values())[0]
    assert "v1" in entry.tags


def test_catalog_generate_report(test_datasets, tmp_path):
    """Test generating markdown report"""
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    
    for ds in test_datasets:
        catalog.index_dataset(ds, tags=["production"])
    
    catalog.update_entry(test_datasets[0], quality_score=90.0)
    
    report = catalog.generate_report()
    
    assert "# Dataset Catalog Report" in report
    assert "Total Datasets:** 3" in report
    assert "Total Records:** 350" in report  # 100 + 50 + 200
