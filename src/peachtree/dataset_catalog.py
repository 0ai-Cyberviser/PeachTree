"""
PeachTree Dataset Catalog & Discovery

Index, search, and discover datasets across the workspace. Track metadata,
dependencies, and enable fast discovery by tags, repos, and quality scores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import hashlib


@dataclass
class DatasetCatalogEntry:
    """Single dataset catalog entry"""
    dataset_path: str
    dataset_name: str
    record_count: int
    file_size_mb: float
    created_timestamp: str
    modified_timestamp: str
    tags: list[str] = field(default_factory=list)
    source_repos: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    quality_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "dataset_name": self.dataset_name,
            "record_count": self.record_count,
            "file_size_mb": self.file_size_mb,
            "created_timestamp": self.created_timestamp,
            "modified_timestamp": self.modified_timestamp,
            "tags": self.tags,
            "source_repos": self.source_repos,
            "dependencies": self.dependencies,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
        }
    
    def matches_query(self, query: str) -> bool:
        """Check if entry matches search query"""
        query_lower = query.lower()
        
        # Search in name
        if query_lower in self.dataset_name.lower():
            return True
        
        # Search in tags
        if any(query_lower in tag.lower() for tag in self.tags):
            return True
        
        # Search in repos
        if any(query_lower in repo.lower() for repo in self.source_repos):
            return True
        
        # Search in metadata
        for value in self.metadata.values():
            if isinstance(value, str) and query_lower in value.lower():
                return True
        
        return False


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    entry: DatasetCatalogEntry
    relevance_score: float
    match_reasons: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "relevance_score": self.relevance_score,
            "match_reasons": self.match_reasons,
        }


class DatasetCatalog:
    """Catalog and search dataset index"""
    
    def __init__(self, index_path: Path | str):
        """
        Initialize dataset catalog
        
        Args:
            index_path: Path to catalog index file
        """
        self.index_path = Path(index_path)
        self.entries: dict[str, DatasetCatalogEntry] = {}
        
        if self.index_path.exists():
            self.load()
    
    def index_dataset(
        self,
        dataset_path: Path | str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetCatalogEntry:
        """
        Index a dataset and add to catalog
        
        Args:
            dataset_path: Dataset file path
            tags: Optional tags for categorization
            metadata: Optional metadata
        
        Returns:
            DatasetCatalogEntry
        """
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # Count records
        record_count = 0
        source_repos = set()
        dependencies = set()
        
        with open(dataset_path) as f:
            for line in f:
                if not line.strip():
                    continue
                
                record_count += 1
                record = json.loads(line)
                
                # Extract source repos
                if "source_repo" in record:
                    source_repos.add(record["source_repo"])
                
                # Extract dependencies from metadata
                if "metadata" in record and "dependencies" in record["metadata"]:
                    for dep in record["metadata"]["dependencies"]:
                        dependencies.add(dep)
        
        # Get file stats
        stat = dataset_path.stat()
        file_size_mb = stat.st_size / (1024 * 1024)
        
        # Create entry
        entry = DatasetCatalogEntry(
            dataset_path=str(dataset_path),
            dataset_name=dataset_path.stem,
            record_count=record_count,
            file_size_mb=file_size_mb,
            created_timestamp=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            modified_timestamp=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            tags=tags or [],
            source_repos=list(source_repos),
            dependencies=list(dependencies),
            metadata=metadata or {},
        )
        
        # Add to catalog
        self.entries[str(dataset_path)] = entry
        
        return entry
    
    def update_entry(
        self,
        dataset_path: Path | str,
        quality_score: float | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Update catalog entry
        
        Args:
            dataset_path: Dataset path
            quality_score: Optional quality score
            tags: Optional tags (replaces existing)
            metadata: Optional metadata (merges with existing)
        """
        dataset_key = str(Path(dataset_path))
        
        if dataset_key not in self.entries:
            raise KeyError(f"Dataset not in catalog: {dataset_path}")
        
        entry = self.entries[dataset_key]
        
        if quality_score is not None:
            entry.quality_score = quality_score
        
        if tags is not None:
            entry.tags = tags
        
        if metadata is not None:
            entry.metadata.update(metadata)
    
    def remove_entry(self, dataset_path: Path | str) -> None:
        """Remove dataset from catalog"""
        dataset_key = str(Path(dataset_path))
        self.entries.pop(dataset_key, None)
    
    def search(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        min_quality: float | None = None,
        min_records: int | None = None,
        source_repo: str | None = None,
    ) -> list[SearchResult]:
        """
        Search catalog with filters
        
        Args:
            query: Text search query
            tags: Filter by tags (match any)
            min_quality: Minimum quality score
            min_records: Minimum record count
            source_repo: Filter by source repository
        
        Returns:
            List of SearchResult sorted by relevance
        """
        results = []
        
        for entry in self.entries.values():
            # Apply filters
            if min_quality is not None and (entry.quality_score is None or entry.quality_score < min_quality):
                continue
            
            if min_records is not None and entry.record_count < min_records:
                continue
            
            if source_repo is not None and source_repo not in entry.source_repos:
                continue
            
            if tags is not None and not any(tag in entry.tags for tag in tags):
                continue
            
            # Calculate relevance
            relevance = 0.0
            match_reasons = []
            
            if query:
                if entry.matches_query(query):
                    relevance += 1.0
                    match_reasons.append(f"Matches query '{query}'")
                else:
                    continue  # Skip if doesn't match query
            else:
                relevance += 0.5
            
            # Boost by quality score
            if entry.quality_score is not None:
                relevance += entry.quality_score / 100.0
                if entry.quality_score >= 80:
                    match_reasons.append(f"High quality ({entry.quality_score:.0f})")
            
            # Boost by tag matches
            if tags:
                tag_matches = sum(1 for tag in tags if tag in entry.tags)
                relevance += tag_matches * 0.3
                if tag_matches > 0:
                    match_reasons.append(f"Matches {tag_matches} tag(s)")
            
            results.append(SearchResult(
                entry=entry,
                relevance_score=relevance,
                match_reasons=match_reasons,
            ))
        
        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return results
    
    def get_by_tag(self, tag: str) -> list[DatasetCatalogEntry]:
        """Get all datasets with a specific tag"""
        return [
            entry for entry in self.entries.values()
            if tag in entry.tags
        ]
    
    def get_by_repo(self, repo: str) -> list[DatasetCatalogEntry]:
        """Get all datasets from a specific repository"""
        return [
            entry for entry in self.entries.values()
            if repo in entry.source_repos
        ]
    
    def get_dependencies(self, dataset_path: Path | str) -> list[str]:
        """Get dependencies for a dataset"""
        dataset_key = str(Path(dataset_path))
        
        if dataset_key not in self.entries:
            return []
        
        return self.entries[dataset_key].dependencies
    
    def get_dependents(self, dataset_path: Path | str) -> list[str]:
        """Get datasets that depend on this dataset"""
        dataset_key = str(Path(dataset_path))
        
        dependents = []
        
        for entry in self.entries.values():
            if dataset_key in entry.dependencies:
                dependents.append(entry.dataset_path)
        
        return dependents
    
    def list_all(self, sort_by: str = "modified") -> list[DatasetCatalogEntry]:
        """
        List all datasets in catalog
        
        Args:
            sort_by: Sort key (modified, created, name, size, records, quality)
        
        Returns:
            List of catalog entries
        """
        entries = list(self.entries.values())
        
        if sort_by == "modified":
            entries.sort(key=lambda e: e.modified_timestamp, reverse=True)
        elif sort_by == "created":
            entries.sort(key=lambda e: e.created_timestamp, reverse=True)
        elif sort_by == "name":
            entries.sort(key=lambda e: e.dataset_name)
        elif sort_by == "size":
            entries.sort(key=lambda e: e.file_size_mb, reverse=True)
        elif sort_by == "records":
            entries.sort(key=lambda e: e.record_count, reverse=True)
        elif sort_by == "quality":
            entries.sort(key=lambda e: e.quality_score or 0, reverse=True)
        
        return entries
    
    def save(self) -> None:
        """Save catalog to index file"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entries": {
                path: entry.to_dict()
                for path, entry in self.entries.items()
            },
            "last_updated": datetime.now().isoformat(),
        }
        
        self.index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    
    def load(self) -> None:
        """Load catalog from index file"""
        if not self.index_path.exists():
            return
        
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        
        self.entries = {}
        
        for path, entry_data in data.get("entries", {}).items():
            entry = DatasetCatalogEntry(**entry_data)
            self.entries[path] = entry
    
    def generate_report(self) -> str:
        """Generate markdown catalog report"""
        total_entries = len(self.entries)
        total_records = sum(e.record_count for e in self.entries.values())
        total_size_mb = sum(e.file_size_mb for e in self.entries.values())
        
        lines = [
            "# Dataset Catalog Report",
            "",
            f"**Total Datasets:** {total_entries}",
            f"**Total Records:** {total_records:,}",
            f"**Total Size:** {total_size_mb:.1f} MB",
            "",
            "## Datasets",
            "",
            "| Name | Records | Size (MB) | Quality | Tags |",
            "|------|---------|-----------|---------|------|",
        ]
        
        for entry in self.list_all(sort_by="modified"):
            quality_str = f"{entry.quality_score:.0f}" if entry.quality_score else "N/A"
            tags_str = ", ".join(entry.tags[:3]) if entry.tags else "-"
            
            lines.append(
                f"| {entry.dataset_name} | {entry.record_count:,} | "
                f"{entry.file_size_mb:.1f} | {quality_str} | {tags_str} |"
            )
        
        return "\n".join(lines)
