from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SearchProviderType(str, Enum):
    """Types of search providers."""
    MOCK = "mock"
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"
    GOOGLE_VISION = "google_vision"
    GOOGLE_LENS = "google_lens"


@dataclass(frozen=True)
class SearchCandidate:
    """
    Represents a candidate from search results.
    
    This is the primary output of Phase 2 search and input to Phase 3 verification.
    """
    # Provider information
    provider: SearchProviderType
    provider_result_id: str  # Unique ID from the search provider
    
    # Candidate URLs
    page_url: str  # URL of the page where candidate was found
    image_url: str  # Direct URL to candidate image
    
    # Metadata
    title: Optional[str] = None
    snippet: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Provenance
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    search_query: Optional[str] = None
    
    # Optional: pre-computed face location if available from search
    face_bbox: Optional[tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    
    def __post_init__(self):
        if not self.page_url:
            raise ValueError("page_url is required")
        if not self.image_url:
            raise ValueError("image_url is required")
        if not self.provider_result_id:
            raise ValueError("provider_result_id is required")


@dataclass(frozen=True)
class SearchResult:
    """Container for search results."""
    query: str
    candidates: tuple[SearchCandidate, ...]
    provider: SearchProviderType
    total_results: int
    search_time_ms: float
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def count(self) -> int:
        return len(self.candidates)
    
    def __len__(self) -> int:
        return self.count
    
    def __iter__(self):
        return iter(self.candidates)
    
    def __getitem__(self, index):
        return self.candidates[index]