from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from src.search.models import CandidateMatch

@dataclass(frozen=True)
class EvidenceCandidate:
    page_url: str
    image_url: str
    domain: Optional[str]
    title: Optional[str]

@dataclass(frozen=True)
class EvidenceVerification:
    similarity: str
    decision: str

@dataclass(frozen=True)
class EvidenceProvenance:
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class EvidenceManifest:
    schema_version: str
    candidate: EvidenceCandidate
    verification: EvidenceVerification
    provenance: EvidenceProvenance

    @classmethod
    def from_candidate_match(cls, match: CandidateMatch) -> "EvidenceManifest":
        """Constructs an immutable EvidenceManifest from a Phase 3 CandidateMatch."""
        
        # Determine fixed-precision string representation for deterministic serialization
        similarity_str = f"{match.similarity:.6f}"
        
        return cls(
            schema_version="1.0",
            candidate=EvidenceCandidate(
                page_url=match.candidate.url,
                image_url=match.candidate.image_url,
                domain=match.candidate.source_domain,
                title=match.candidate.title,
            ),
            verification=EvidenceVerification(
                similarity=similarity_str,
                decision=match.status
            ),
            provenance=EvidenceProvenance(
                provider=match.candidate.provider,
                # Filter metadata to keep only deterministic scalar/primitive types if needed, 
                # but dicts in our implementation are simple
                metadata=match.candidate.metadata.copy() if match.candidate.metadata else {}
            )
        )
