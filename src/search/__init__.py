from .models import SearchCandidate, SearchResult, SearchProviderType
from .base import SearchProvider, SearchProviderFactory, MockSearchProvider
from .google_vision import GoogleVisionSearchProvider
from .google_lens import GoogleLensBrowserProvider

# Register the provider
SearchProviderFactory.register(SearchProviderType.GOOGLE_VISION, GoogleVisionSearchProvider)
SearchProviderFactory.register(SearchProviderType.GOOGLE_LENS, GoogleLensBrowserProvider)

__all__ = [
    "SearchCandidate",
    "SearchResult",
    "SearchProviderType",
    "SearchProvider",
    "SearchProviderFactory",
    "MockSearchProvider",
    "GoogleVisionSearchProvider",
]