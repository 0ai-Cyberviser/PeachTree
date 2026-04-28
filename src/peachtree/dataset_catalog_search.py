"""Advanced dataset catalog search and discovery.

Provides sophisticated search capabilities for dataset catalogs
with filtering, ranking, and recommendations.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import json
import re


class SearchOperator(Enum):
    """Search operators."""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    IN_LIST = "in"


class RankingCriteria(Enum):
    """Ranking criteria."""
    RELEVANCE = "relevance"
    SIZE = "size"
    DATE = "date"
    QUALITY = "quality"
    POPULARITY = "popularity"


@dataclass
class SearchFilter:
    """Search filter specification."""
    field: str
    operator: SearchOperator
    value: Any
    
    def matches(self, record: Dict[str, Any]) -> bool:
        """Check if record matches filter."""
        field_value = record.get(self.field)
        
        if field_value is None:
            return False
        
        if self.operator == SearchOperator.EQUALS:
            return field_value == self.value
        elif self.operator == SearchOperator.CONTAINS:
            return str(self.value) in str(field_value)
        elif self.operator == SearchOperator.STARTS_WITH:
            return str(field_value).startswith(str(self.value))
        elif self.operator == SearchOperator.ENDS_WITH:
            return str(field_value).endswith(str(self.value))
        elif self.operator == SearchOperator.REGEX:
            return bool(re.search(str(self.value), str(field_value)))
        elif self.operator == SearchOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == SearchOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == SearchOperator.IN_LIST:
            return field_value in self.value
        
        return False


@dataclass
class SearchQuery:
    """Complete search query."""
    query_id: str
    filters: List[SearchFilter] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    ranking: RankingCriteria = RankingCriteria.RELEVANCE
    limit: int = 100
    offset: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "filters": [
                {"field": f.field, "operator": f.operator.value, "value": f.value}
                for f in self.filters
            ],
            "keywords": self.keywords,
            "ranking": self.ranking.value,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class SearchResult:
    """Single search result."""
    dataset_id: str
    score: float
    metadata: Dict[str, Any]
    matched_fields: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "score": self.score,
            "metadata": self.metadata,
            "matched_fields": self.matched_fields,
        }


@dataclass
class SearchResponse:
    """Search response with results."""
    query_id: str
    total_results: int
    results: List[SearchResult]
    search_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "total_results": self.total_results,
            "results": [r.to_dict() for r in self.results],
            "search_time_ms": self.search_time_ms,
        }


class CatalogSearchEngine:
    """Main catalog search engine."""
    
    def __init__(self, catalog_path: Path):
        """Initialize search engine."""
        self.catalog_path = catalog_path
        self.index: List[Dict[str, Any]] = []
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        """Load catalog data."""
        if self.catalog_path.exists():
            with open(self.catalog_path) as f:
                for line in f:
                    if line.strip():
                        self.index.append(json.loads(line))
    
    def search(self, query: SearchQuery) -> SearchResponse:
        """Execute search query."""
        start_time = datetime.now()
        
        # Apply filters
        filtered_results = []
        for record in self.index:
            if self._matches_filters(record, query.filters):
                if self._matches_keywords(record, query.keywords):
                    filtered_results.append(record)
        
        # Score and rank
        scored_results = []
        for record in filtered_results:
            score = self._calculate_score(record, query)
            matched_fields = self._get_matched_fields(record, query)
            
            scored_results.append(SearchResult(
                dataset_id=record.get("dataset_id", "unknown"),
                score=score,
                metadata=record,
                matched_fields=matched_fields,
            ))
        
        # Sort by score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        # Apply pagination
        total_results = len(scored_results)
        paginated = scored_results[query.offset:query.offset + query.limit]
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            query_id=query.query_id,
            total_results=total_results,
            results=paginated,
            search_time_ms=elapsed,
        )
    
    def _matches_filters(
        self,
        record: Dict[str, Any],
        filters: List[SearchFilter],
    ) -> bool:
        """Check if record matches all filters."""
        for filter in filters:
            if not filter.matches(record):
                return False
        return True
    
    def _matches_keywords(
        self,
        record: Dict[str, Any],
        keywords: List[str],
    ) -> bool:
        """Check if record matches keywords."""
        if not keywords:
            return True
        
        record_text = json.dumps(record).lower()
        
        for keyword in keywords:
            if keyword.lower() in record_text:
                return True
        
        return False
    
    def _calculate_score(
        self,
        record: Dict[str, Any],
        query: SearchQuery,
    ) -> float:
        """Calculate relevance score."""
        score = 0.0
        
        # Keyword matching score
        record_text = json.dumps(record).lower()
        for keyword in query.keywords:
            if keyword.lower() in record_text:
                score += 1.0
        
        # Ranking criteria
        if query.ranking == RankingCriteria.SIZE:
            score += record.get("size", 0) / 1000000  # Normalize
        elif query.ranking == RankingCriteria.QUALITY:
            score += record.get("quality_score", 0.0)
        elif query.ranking == RankingCriteria.POPULARITY:
            score += record.get("downloads", 0) / 100  # Normalize
        
        return score
    
    def _get_matched_fields(
        self,
        record: Dict[str, Any],
        query: SearchQuery,
    ) -> List[str]:
        """Get fields that matched the query."""
        matched = []
        
        for filter in query.filters:
            if filter.matches(record):
                matched.append(filter.field)
        
        return matched


class FacetedSearch:
    """Faceted search for catalog browsing."""
    
    def __init__(self, search_engine: CatalogSearchEngine):
        """Initialize faceted search."""
        self.search_engine = search_engine
    
    def get_facets(self, field: str) -> Dict[str, int]:
        """Get facet counts for a field."""
        facets: Dict[str, int] = {}
        
        for record in self.search_engine.index:
            value = record.get(field)
            if value is not None:
                value_str = str(value)
                facets[value_str] = facets.get(value_str, 0) + 1
        
        return facets
    
    def get_all_facets(self) -> Dict[str, Dict[str, int]]:
        """Get facets for all common fields."""
        common_fields = ["license", "format", "category", "language"]
        
        all_facets = {}
        for field in common_fields:
            all_facets[field] = self.get_facets(field)
        
        return all_facets


class SearchRecommender:
    """Recommend datasets based on search history."""
    
    def __init__(self):
        """Initialize recommender."""
        self.search_history: List[SearchQuery] = []
    
    def add_search(self, query: SearchQuery) -> None:
        """Add search to history."""
        self.search_history.append(query)
    
    def get_recommendations(
        self,
        catalog: CatalogSearchEngine,
        limit: int = 10,
    ) -> List[SearchResult]:
        """Get dataset recommendations."""
        recommendations = []
        
        if not self.search_history:
            return recommendations
        
        # Analyze search history
        all_keywords: Set[str] = set()
        for query in self.search_history:
            all_keywords.update(query.keywords)
        
        # Create recommendation query
        rec_query = SearchQuery(
            query_id="recommendation",
            keywords=list(all_keywords),
            limit=limit,
        )
        
        response = catalog.search(rec_query)
        return response.results


class AutocompleteEngine:
    """Autocomplete suggestions for search."""
    
    def __init__(self, catalog: CatalogSearchEngine):
        """Initialize autocomplete."""
        self.catalog = catalog
        self.terms: Set[str] = set()
        self._build_terms()
    
    def _build_terms(self) -> None:
        """Build term index."""
        for record in self.catalog.index:
            # Extract terms from record
            text = json.dumps(record).lower()
            words = re.findall(r'\w+', text)
            self.terms.update(words)
    
    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions."""
        prefix_lower = prefix.lower()
        matches = [
            term for term in self.terms
            if term.startswith(prefix_lower)
        ]
        
        matches.sort()
        return matches[:limit]


class SavedSearchManager:
    """Manage saved searches."""
    
    def __init__(self, storage_path: Path):
        """Initialize saved search manager."""
        self.storage_path = storage_path
        self.saved_searches: Dict[str, SearchQuery] = {}
        self._load()
    
    def _load(self) -> None:
        """Load saved searches."""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            for search_data in data.get("searches", []):
                query = SearchQuery(
                    query_id=search_data["query_id"],
                    keywords=search_data.get("keywords", []),
                    ranking=RankingCriteria(search_data.get("ranking", "relevance")),
                    limit=search_data.get("limit", 100),
                )
                self.saved_searches[query.query_id] = query
    
    def save_search(self, query: SearchQuery, name: str) -> None:
        """Save a search query."""
        self.saved_searches[name] = query
        self._persist()
    
    def get_search(self, name: str) -> Optional[SearchQuery]:
        """Get saved search."""
        return self.saved_searches.get(name)
    
    def list_searches(self) -> List[str]:
        """List saved searches."""
        return list(self.saved_searches.keys())
    
    def _persist(self) -> None:
        """Persist saved searches."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "searches": [
                query.to_dict()
                for query in self.saved_searches.values()
            ]
        }
        
        self.storage_path.write_text(json.dumps(data, indent=2))
