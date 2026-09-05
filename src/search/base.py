from typing import Protocol, List
from src.search.models import SearchCandidate

class SearchProvider(Protocol):
    def search(self, image_bytes: bytes) -> List[SearchCandidate]:
        """
        Executes a reverse image search using the provided image bytes.
        Returns a list of normalized SearchCandidate objects.
        """
        ...
