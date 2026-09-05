from typing import List
from src.search.base import SearchProvider
from src.search.models import SearchCandidate

class MockSearchProvider(SearchProvider):
    def __init__(self, candidates: List[SearchCandidate] = None):
        if candidates is None:
            self.candidates = [
                SearchCandidate(
                    url="https://example.com/mock-post-1",
                    image_url="https://example.com/mock-image-1.jpg",
                    title="Mock Target Post",
                    source_domain="example.com",
                    provider="MockProvider"
                )
            ]
        else:
            self.candidates = candidates

    def search(self, image_bytes: bytes) -> List[SearchCandidate]:
        # Ignores input and returns deterministic fixture data
        return self.candidates
