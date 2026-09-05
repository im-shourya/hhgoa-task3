from .models import SearchCandidate, SearchResult, SearchProviderType
from .base import SearchProvider, SearchProviderFactory, MockSearchProvider
from .google_vision import GoogleVisionSearchProvider

# Register the provider
SearchProviderFactory.register(SearchProviderType.GOOGLE_VISION, GoogleVisionSearchProvider)

__all__ = [
    "SearchCandidate",
    "SearchResult",
    "SearchProviderType",
    "SearchProvider",
    "SearchProviderFactory",
    "MockSearchProvider",
    "GoogleVisionSearchProvider",
]