from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

from ..config import get_settings
from ..face.engine import FaceEngine
from ..face.models import FaceEmbedding
from ..search import SearchProvider, SearchProviderFactory, SearchResult, SearchCandidate
from ..errors import (
    NoFaceDetectedError,
    MultipleFacesError,
    NoEvaluatableCandidatesError,
    NoMatchError,
)
from .retriever import CandidateImageRetriever, create_retriever
from .evaluator import CandidateEvaluator, CandidateMatch, EvaluationStatus
from .ranking import CandidateRanker, RankingResult, RankedCandidate

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerificationResult:
    """Complete result of the verification pipeline."""
    query_embedding: FaceEmbedding
    search_result: SearchResult
    ranking_result: RankingResult
    verification_status: str  # "MATCH", "NO_MATCH", "NO_EVALUATABLE_CANDIDATES"
    
    @property
    def best_candidate(self) -> Optional[RankedCandidate]:
        return self.ranking_result.best_match or self.ranking_result.best_evaluated
    
    @property
    def has_match(self) -> bool:
        return self.verification_status == "MATCH"
    
    @property
    def total_candidates(self) -> int:
        return self.ranking_result.total_candidates
    
    @property
    def evaluated_candidates(self) -> int:
        return self.ranking_result.evaluated_count
    
    @property
    def matched_candidates(self) -> int:
        return self.ranking_result.match_count
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "verification_status": self.verification_status,
            "search_result": {
                "query": self.search_result.query,
                "provider": self.search_result.provider.value,
                "total_results": self.search_result.total_results,
                "candidates_found": self.search_result.count,
            },
            "ranking": {
                "total_candidates": self.total_candidates,
                "evaluated": self.evaluated_candidates,
                "matches": self.matched_candidates,
                "best_candidate": self.best_candidate.match.to_dict() if self.best_candidate else None,
            },
            "top_candidates": [
                {
                    "rank": rc.rank,
                    "similarity": rc.similarity,
                    "status": rc.status.value,
                    "image_url": rc.candidate.image_url,
                    "page_url": rc.candidate.page_url,
                    "title": rc.candidate.title,
                }
                for rc in self.ranking_result.ranked[:5]
            ]
        }


class VerificationPipeline:
    """
    Complete candidate verification pipeline.
    
    Orchestrates:
    1. FaceEngine for query embedding
    2. SearchProvider for candidate discovery
    3. CandidateImageRetriever for image download
    4. CandidateEvaluator for face detection + embedding + similarity
    5. CandidateRanker for deterministic ranking
    6. Match decision
    """
    
    def __init__(
        self,
        face_engine: Optional[FaceEngine] = None,
        search_provider: Optional[SearchProvider] = None,
        retriever: Optional[CandidateImageRetriever] = None,
        evaluator: Optional[CandidateEvaluator] = None,
        ranker: Optional[CandidateRanker] = None,
        settings=None
    ):
        self._settings = settings or get_settings()
        self._face_engine = face_engine or FaceEngine(self._settings)
        self._search_provider = search_provider or SearchProviderFactory.create_from_settings()
        self._retriever = retriever or create_retriever()
        self._evaluator = evaluator or CandidateEvaluator(
            face_engine=self._face_engine,
            retriever=self._retriever,
            settings=self._settings
        )
        self._ranker = ranker or CandidateRanker()
    
    def verify_from_image(
        self,
        query_image_bytes: bytes,
        search_query: Optional[str] = None,
        max_candidates: Optional[int] = None
    ) -> VerificationResult:
        """
        Run full verification pipeline from query image.
        
        Args:
            query_image_bytes: Input face image bytes
            search_query: Optional search query (defaults to image-based search)
            max_candidates: Max candidates to evaluate (defaults to settings)
            
        Returns:
            VerificationResult with complete pipeline output
            
        Raises:
            NoFaceDetectedError: If no face in query image
            MultipleFacesError: If multiple faces in query image
            NoEvaluatableCandidatesError: If no candidates could be evaluated
            NoMatchError: If no candidate meets threshold
        """
        max_candidates = max_candidates or self._settings.search_max_results
        
        # Step 1: Generate query embedding
        logger.info("Generating query embedding...")
        query_embedding = self._face_engine.get_embedding(query_image_bytes)
        logger.info(f"Query embedding generated: dimension={query_embedding.dimension}")
        
        # Step 2: Search for candidates
        query = search_query or "face search"
        logger.info(f"Searching for candidates: '{query}'")
        search_result = self._search_provider.search_by_image(query_image_bytes, max_candidates)
        logger.info(f"Search returned {search_result.count} candidates")
        
        if search_result.count == 0:
            raise NoEvaluatableCandidatesError("Search returned no candidates")
        
        # Step 3: Evaluate candidates
        candidates = list(search_result.candidates)[:max_candidates]
        logger.info(f"Evaluating {len(candidates)} candidates...")
        matches = self._evaluator.evaluate_batch(query_embedding, candidates)
        
        # Step 4: Rank candidates
        logger.info("Ranking candidates...")
        ranking_result = self._ranker.rank(matches)
        
        # Step 5: Determine verification status
        if ranking_result.evaluated_count == 0:
            verification_status = "NO_EVALUATABLE_CANDIDATES"
        elif ranking_result.match_count > 0:
            verification_status = "MATCH"
        else:
            verification_status = "NO_MATCH"
        
        logger.info(f"Verification complete: {verification_status}")
        
        return VerificationResult(
            query_embedding=query_embedding,
            search_result=search_result,
            ranking_result=ranking_result,
            verification_status=verification_status
        )
    
    def verify_from_embedding(
        self,
        query_embedding: FaceEmbedding,
        search_query: str,
        max_candidates: Optional[int] = None
    ) -> VerificationResult:
        """
        Run verification pipeline from pre-computed query embedding.
        
        Args:
            query_embedding: Pre-computed query face embedding
            search_query: Search query text
            max_candidates: Max candidates to evaluate
            
        Returns:
            VerificationResult
        """
        max_candidates = max_candidates or self._settings.search_max_results
        
        # Search for candidates
        logger.info(f"Searching for candidates: '{search_query}'")
        search_result = self._search_provider.search(search_query, max_candidates)
        logger.info(f"Search returned {search_result.count} candidates")
        
        if search_result.count == 0:
            raise NoEvaluatableCandidatesError("Search returned no candidates")
        
        # Evaluate candidates
        candidates = list(search_result.candidates)[:max_candidates]
        logger.info(f"Evaluating {len(candidates)} candidates...")
        matches = self._evaluator.evaluate_batch(query_embedding, candidates)
        
        # Rank candidates
        logger.info("Ranking candidates...")
        ranking_result = self._ranker.rank(matches)
        
        # Determine status
        if ranking_result.evaluated_count == 0:
            verification_status = "NO_EVALUATABLE_CANDIDATES"
        elif ranking_result.match_count > 0:
            verification_status = "MATCH"
        else:
            verification_status = "NO_MATCH"
        
        logger.info(f"Verification complete: {verification_status}")
        
        return VerificationResult(
            query_embedding=query_embedding,
            search_result=search_result,
            ranking_result=ranking_result,
            verification_status=verification_status
        )


def create_pipeline() -> VerificationPipeline:
    """Factory function to create a verification pipeline with current settings."""
    return VerificationPipeline()