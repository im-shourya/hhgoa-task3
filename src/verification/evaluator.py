from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..config import get_settings
from ..face.engine import FaceEngine
from ..face.models import FaceEmbedding
from ..search.models import SearchCandidate
from ..errors import (
    CandidateError,
    CandidateNoFaceError,
    CandidateMultipleFacesError,
    CandidateEmbeddingError,
)
from .retriever import CandidateImageRetriever, create_retriever

logger = logging.getLogger(__name__)


class EvaluationStatus(str, Enum):
    """Status of candidate evaluation."""
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    INVALID_IMAGE = "INVALID_IMAGE"
    NO_FACE = "NO_FACE"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    EVALUATED = "EVALUATED"
    MATCH = "MATCH"
    NON_MATCH = "NON_MATCH"


@dataclass(frozen=True)
class CandidateMatch:
    """
    Result of candidate evaluation.
    
    Contains the candidate, similarity score, and evaluation status.
    """
    candidate: SearchCandidate
    similarity: Optional[float]
    status: EvaluationStatus
    error_message: Optional[str] = None
    embedding: Optional[FaceEmbedding] = None  # Not serialized in production
    
    @property
    def is_match(self) -> bool:
        return self.status == EvaluationStatus.MATCH
    
    @property
    def is_evaluated(self) -> bool:
        return self.status in (EvaluationStatus.MATCH, EvaluationStatus.NON_MATCH, EvaluationStatus.EVALUATED)
    
    @property
    def has_embedding(self) -> bool:
        return self.embedding is not None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization (excludes embedding)."""
        return {
            "candidate": {
                "provider": self.candidate.provider.value,
                "provider_result_id": self.candidate.provider_result_id,
                "page_url": self.candidate.page_url,
                "image_url": self.candidate.image_url,
                "title": self.candidate.title,
                "snippet": self.candidate.snippet,
            },
            "similarity": self.similarity,
            "status": self.status.value,
            "error_message": self.error_message,
        }


class CandidateEvaluator:
    """
    Evaluates search candidates against a query embedding.
    
    Pipeline:
    1. Retrieve candidate image
    2. Detect face using FaceEngine
    3. Generate candidate embedding
    4. Compare with query embedding
    5. Return CandidateMatch with similarity and status
    """
    
    def __init__(
        self,
        face_engine: Optional[FaceEngine] = None,
        retriever: Optional[CandidateImageRetriever] = None,
        settings=None
    ):
        self._settings = settings or get_settings()
        self._face_engine = face_engine or FaceEngine(self._settings)
        self._retriever = retriever or create_retriever()
    
    def evaluate(
        self,
        query_embedding: FaceEmbedding,
        candidate: SearchCandidate
    ) -> CandidateMatch:
        """
        Evaluate a single candidate against the query embedding.
        
        Args:
            query_embedding: Query face embedding (pre-computed)
            candidate: Search candidate to evaluate
            
        Returns:
            CandidateMatch with similarity score and status
        """
        # Step 1: Retrieve image
        try:
            image_bytes = self._retriever.retrieve(candidate)
        except Exception as e:
            logger.warning(f"Retrieval failed for {candidate.image_url}: {e}")
            return CandidateMatch(
                candidate=candidate,
                similarity=None,
                status=EvaluationStatus.RETRIEVAL_FAILED,
                error_message=str(e)
            )
        
        # Step 2: Get candidate embedding (includes face detection)
        try:
            candidate_embedding = self._face_engine.get_embedding(image_bytes)
        except CandidateNoFaceError as e:
            return CandidateMatch(
                candidate=candidate,
                similarity=None,
                status=EvaluationStatus.NO_FACE,
                error_message=str(e)
            )
        except CandidateMultipleFacesError as e:
            return CandidateMatch(
                candidate=candidate,
                similarity=None,
                status=EvaluationStatus.MULTIPLE_FACES,
                error_message=str(e)
            )
        except Exception as e:
            logger.warning(f"Embedding failed for {candidate.image_url}: {e}")
            return CandidateMatch(
                candidate=candidate,
                similarity=None,
                status=EvaluationStatus.EMBEDDING_FAILED,
                error_message=str(e)
            )
        
        # Step 3: Compare embeddings
        try:
            similarity = self._face_engine.compare(query_embedding, candidate_embedding)
        except Exception as e:
            logger.warning(f"Comparison failed for {candidate.image_url}: {e}")
            return CandidateMatch(
                candidate=candidate,
                similarity=None,
                status=EvaluationStatus.EMBEDDING_FAILED,
                error_message=f"Comparison error: {e}"
            )
        
        # Step 4: Determine match status
        is_match = self._face_engine.is_match(similarity)
        status = EvaluationStatus.MATCH if is_match else EvaluationStatus.NON_MATCH
        
        logger.info(f"Candidate {candidate.provider_result_id}: similarity={similarity:.4f}, status={status.value}")
        
        return CandidateMatch(
            candidate=candidate,
            similarity=similarity,
            status=status,
            embedding=candidate_embedding
        )
    
    def evaluate_batch(
        self,
        query_embedding: FaceEmbedding,
        candidates: list[SearchCandidate]
    ) -> list[CandidateMatch]:
        """
        Evaluate multiple candidates sequentially.
        
        Args:
            query_embedding: Query face embedding
            candidates: List of candidates to evaluate
            
        Returns:
            List of CandidateMatch results in same order
        """
        results = []
        for candidate in candidates:
            match = self.evaluate(query_embedding, candidate)
            results.append(match)
        return results