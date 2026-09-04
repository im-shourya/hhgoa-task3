from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class SearchCandidate:
    url: str
    image_url: str
    title: Optional[str] = None
    source_domain: Optional[str] = None
    provider: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class CandidateMatch:
    candidate: SearchCandidate
    similarity: float = 0.0
    face_detected: bool = False
    status: str = "PENDING"
