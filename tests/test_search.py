import pytest
from datetime import datetime

from src.search.models import SearchCandidate, SearchResult, SearchProviderType
from src.search import MockSearchProvider, SearchProviderFactory
from src.errors import SearchError


class TestSearchCandidate:
    def test_valid_candidate(self):
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
            title="Test Person",
            snippet="Test snippet",
        )
        assert candidate.provider == SearchProviderType.MOCK
        assert candidate.provider_result_id == "test_1"
        assert candidate.page_url == "https://example.com/page"
        assert candidate.image_url == "https://example.com/image.jpg"
    
    def test_missing_page_url_raises(self):
        with pytest.raises(ValueError, match="page_url is required"):
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="test_1",
                page_url="",
                image_url="https://example.com/image.jpg",
            )
    
    def test_missing_image_url_raises(self):
        with pytest.raises(ValueError, match="image_url is required"):
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="test_1",
                page_url="https://example.com/page",
                image_url="",
            )
    
    def test_missing_provider_result_id_raises(self):
        with pytest.raises(ValueError, match="provider_result_id is required"):
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="",
                page_url="https://example.com/page",
                image_url="https://example.com/image.jpg",
            )


class TestSearchResult:
    def test_search_result(self):
        candidates = (
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="1",
                page_url="https://example.com/1",
                image_url="https://example.com/1.jpg",
            ),
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="2",
                page_url="https://example.com/2",
                image_url="https://example.com/2.jpg",
            ),
        )
        result = SearchResult(
            query="test query",
            candidates=candidates,
            provider=SearchProviderType.MOCK,
            total_results=2,
            search_time_ms=100.0,
        )
        assert result.count == 2
        assert len(result) == 2
        assert result[0].provider_result_id == "1"
        assert result[1].provider_result_id == "2"
        assert list(result) == list(candidates)


class TestMockSearchProvider:
    def test_provider_type(self):
        provider = MockSearchProvider()
        assert provider.provider_type == SearchProviderType.MOCK
    
    def test_search_returns_candidates(self):
        provider = MockSearchProvider()
        result = provider.search("John Doe", max_results=5)
        
        assert result.provider == SearchProviderType.MOCK
        assert result.query == "John Doe"
        assert result.count > 0
        assert result.total_results > 0
        assert result.search_time_ms > 0
    
    def test_search_by_image(self):
        provider = MockSearchProvider()
        result = provider.search_by_image(b"fake image bytes", max_results=5)
        
        assert result.provider == SearchProviderType.MOCK
        assert result.query == "[image_search]"
        assert result.count > 0
    
    def test_custom_candidates(self):
        custom = [
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="custom_1",
                page_url="https://custom.com/1",
                image_url="https://custom.com/1.jpg",
            ),
        ]
        provider = MockSearchProvider(candidates=custom)
        result = provider.search("anything", max_results=10)
        
        assert result.count == 1
        assert result.candidates[0].provider_result_id == "custom_1"


class TestSearchProviderFactory:
    def test_create_mock(self):
        provider = SearchProviderFactory.create(SearchProviderType.MOCK)
        assert isinstance(provider, MockSearchProvider)
        assert provider.provider_type == SearchProviderType.MOCK
    
    def test_create_unknown_raises(self):
        with pytest.raises(SearchError, match="Unknown search provider"):
            SearchProviderFactory.create("unknown_provider")
    
    def test_register_custom_provider(self):
        class CustomProvider:
            provider_type = SearchProviderType.MOCK
            
            def search(self, query, max_results=10):
                pass
            
            def search_by_image(self, image_bytes, max_results=10):
                pass
        
        SearchProviderFactory.register(SearchProviderType.MOCK, CustomProvider)
        provider = SearchProviderFactory.create(SearchProviderType.MOCK)
        assert isinstance(provider, CustomProvider)