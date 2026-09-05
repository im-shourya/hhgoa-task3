from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from ..config import get_settings
from ..errors import SearchError, SearchProviderError, NoResultsError
from .models import SearchCandidate, SearchResult, SearchProviderType


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    @property
    @abstractmethod
    def provider_type(self) -> SearchProviderType:
        """Return the provider type."""
        pass
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> SearchResult:
        """
        Search for candidates.
        
        Args:
            query: Search query (typically a name or description)
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult with candidates
            
        Raises:
            SearchProviderError: If search fails
            NoResultsError: If no results found
        """
        pass
    
    @abstractmethod
    def search_by_image(self, image_bytes: bytes, max_results: int = 10) -> SearchResult:
        """
        Reverse image search.
        
        Args:
            image_bytes: Query image bytes
            max_results: Maximum number of results
            
        Returns:
            SearchResult with candidates
        """
        pass


class SearchProviderFactory:
    """Factory for creating search providers."""
    
    _providers: dict[SearchProviderType, type[SearchProvider]] = {}
    
    @classmethod
    def register(cls, provider_type: SearchProviderType, provider_class: type[SearchProvider]) -> None:
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def create(cls, provider_type: SearchProviderType, **kwargs) -> SearchProvider:
        if provider_type not in cls._providers:
            raise SearchError(f"Unknown search provider: {provider_type}")
        return cls._providers[provider_type](**kwargs)
    
    @classmethod
    def create_from_settings(cls, **kwargs) -> SearchProvider:
        settings = get_settings()
        return cls.create(settings.search_provider, **kwargs)


class MockSearchProvider(SearchProvider):
    """Mock search provider for testing and development."""
    
    def __init__(self, candidates: Optional[list[SearchCandidate]] = None):
        self._candidates = candidates or self._default_candidates()
    
    @property
    def provider_type(self) -> SearchProviderType:
        return SearchProviderType.MOCK
    
    def _default_candidates(self) -> list[SearchCandidate]:
        """Default mock candidates for testing."""
        return [
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="mock_1",
                page_url="https://example.com/person1",
                image_url="https://example.com/person1.jpg",
                title="John Doe - Profile",
                snippet="John Doe professional profile",
                search_query="John Doe"
            ),
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="mock_2",
                page_url="https://example.com/person2",
                image_url="https://example.com/person2.jpg",
                title="Jane Smith - LinkedIn",
                snippet="Jane Smith software engineer",
                search_query="Jane Smith"
            ),
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="mock_3",
                page_url="https://example.com/person3",
                image_url="https://example.com/person3.jpg",
                title="Bob Wilson - Company Page",
                snippet="Bob Wilson CTO at TechCorp",
                search_query="Bob Wilson"
            ),
        ]
    
    def search(self, query: str, max_results: int = 10) -> SearchResult:
        import time
        start = time.perf_counter()
        
        # Filter candidates by query (simple mock)
        filtered = [c for c in self._candidates if query.lower() in (c.title or "").lower()]
        if not filtered:
            filtered = self._candidates[:max_results]
        
        results = filtered[:max_results]
        
        return SearchResult(
            query=query,
            candidates=tuple(results),
            provider=self.provider_type,
            total_results=len(results),
            search_time_ms=(time.perf_counter() - start) * 1000
        )
    
    def search_by_image(self, image_bytes: bytes, max_results: int = 10) -> SearchResult:
        import time
        start = time.perf_counter()
        
        results = self._candidates[:max_results]
        
        return SearchResult(
            query="[image_search]",
            candidates=tuple(results),
            provider=self.provider_type,
            total_results=len(results),
            search_time_ms=(time.perf_counter() - start) * 1000
        )


# Register the mock provider
SearchProviderFactory.register(SearchProviderType.MOCK, MockSearchProvider)