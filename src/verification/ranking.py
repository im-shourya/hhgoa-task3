from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

from .evaluator import CandidateMatch, EvaluationStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RankedCandidate:
    """A candidate with its rank position."""
    match: CandidateMatch
    rank: int
    
    @property
    def similarity(self) -> Optional[float]:
        return self.match.similarity
    
    @property
    def candidate(self):
        return self.match.candidate
    
    @property
    def status(self) -> EvaluationStatus:
        return self.match.status


@dataclass(frozen=True)
class RankingResult:
    """Result of ranking candidates."""
    ranked: tuple[RankedCandidate, ...]
    best_match: Optional[RankedCandidate]
    best_evaluated: Optional[RankedCandidate]
    total_candidates: int
    evaluated_count: int
    match_count: int
    
    @property
    def has_match(self) -> bool:
        return self.best_match is not None
    
    @property
    def has_evaluated(self) -> bool:
        return self.best_evaluated is not None


class CandidateRanker:
    """
    Ranks evaluated candidates by similarity.
    
    Ranking rules:
    1. Primary: similarity DESC (higher similarity first)
    2. Secondary: original provider result order (deterministic tie-break)
    3. Failed candidates ranked after all evaluated candidates
    """
    
    def rank(self, matches: list[CandidateMatch]) -> RankingResult:
        """
        Rank candidates by similarity.
        
        Args:
            matches: List of CandidateMatch results
            
        Returns:
            RankingResult with ranked candidates and best match
        """
        if not matches:
            return RankingResult(
                ranked=tuple(),
                best_match=None,
                best_evaluated=None,
                total_candidates=0,
                evaluated_count=0,
                match_count=0
            )
        
        # Separate evaluated and failed candidates
        evaluated = [m for m in matches if m.is_evaluated and m.similarity is not None]
        failed = [m for m in matches if not m.is_evaluated]
        
        # Sort evaluated by similarity DESC, then by original order (stable sort)
        # We use enumerate to preserve original index for tie-breaking
        evaluated_with_index = [(m, i) for i, m in enumerate(evaluated)]
        evaluated_with_index.sort(key=lambda x: (-x[0].similarity, x[1]))
        
        # Create ranked candidates
        ranked_list = []
        for rank, (match, orig_idx) in enumerate(evaluated_with_index, start=1):
            ranked_list.append(RankedCandidate(match=match, rank=rank))
        
        # Add failed candidates at the end (preserving original order)
        for match in failed:
            rank = len(ranked_list) + 1
            ranked_list.append(RankedCandidate(match=match, rank=rank))
        
        ranked = tuple(ranked_list)
        
        # Find best match (highest similarity among MATCH status)
        best_match = None
        for rc in ranked:
            if rc.status == EvaluationStatus.MATCH:
                best_match = rc
                break
        
        # Find best evaluated (highest similarity among all evaluated)
        best_evaluated = None
        for rc in ranked:
            if rc.status in (EvaluationStatus.MATCH, EvaluationStatus.NON_MATCH, EvaluationStatus.EVALUATED):
                best_evaluated = rc
                break
        
        match_count = sum(1 for m in matches if m.status == EvaluationStatus.MATCH)
        
        logger.info(f"Ranked {len(matches)} candidates: {len(evaluated)} evaluated, {len(failed)} failed, {match_count} matches")
        
        return RankingResult(
            ranked=ranked,
            best_match=best_match,
            best_evaluated=best_evaluated,
            total_candidates=len(matches),
            evaluated_count=len(evaluated),
            match_count=match_count
        )


def create_ranker() -> CandidateRanker:
    """Factory function to create a ranker."""
    return CandidateRanker()