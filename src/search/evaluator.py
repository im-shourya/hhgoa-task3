import httpx
from typing import List, Optional
from urllib.parse import urlparse
import numpy as np

from src.face import FaceEngine
from src.errors import FaceNotFoundError, MultipleFacesError, ImageDecodeError, InvalidEmbeddingError
from src.config import Config
from src.search.models import SearchCandidate, CandidateMatch
from src.search.base import SearchProvider

class SearchEvaluator:
    def __init__(self, face_engine: FaceEngine, search_provider: SearchProvider, timeout: int = Config.REQUEST_TIMEOUT):
        self.face_engine = face_engine
        self.provider = search_provider
        self.timeout = timeout
        
    def _is_safe_url(self, url: str) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"]

    def retrieve_candidate_image(self, candidate: SearchCandidate) -> Optional[bytes]:
        if not self._is_safe_url(candidate.image_url):
            return None
            
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(candidate.image_url)
                if response.status_code == 200 and len(response.content) <= Config.MAX_IMAGE_SIZE:
                    return response.content
        except Exception:
            # Silently catch timeouts and connection errors to gracefully skip the candidate
            return None
        return None

    def evaluate_candidates(self, query_embedding: np.ndarray, candidates: List[SearchCandidate]) -> List[CandidateMatch]:
        results = []
        
        # Basic deduplication
        seen_urls = set()
        unique_candidates = []
        for c in candidates:
            # We deduplicate by image_url since that is what we process
            if c.image_url not in seen_urls:
                seen_urls.add(c.image_url)
                unique_candidates.append(c)

        for candidate in unique_candidates:
            match = CandidateMatch(candidate=candidate, similarity=0.0, face_detected=False, status="PENDING")
            
            image_bytes = self.retrieve_candidate_image(candidate)
            if not image_bytes:
                match.status = "IMAGE_RETRIEVAL_FAILED"
                results.append(match)
                continue
                
            try:
                candidate_embedding = self.face_engine.get_embedding(image_bytes)
                similarity = self.face_engine.compare(query_embedding, candidate_embedding)
                
                match.face_detected = True
                match.similarity = similarity
                
                if similarity >= Config.FACE_MATCH_THRESHOLD:
                    match.status = "MATCH"
                else:
                    match.status = "NON_MATCH"
                    
            except FaceNotFoundError:
                match.status = "NO_FACE"
            except MultipleFacesError:
                # Per Phase 1 policy, MultipleFacesError means we reject it.
                match.status = "MULTIPLE_FACES"
            except ImageDecodeError:
                match.status = "INVALID_IMAGE"
            except InvalidEmbeddingError:
                match.status = "EMBEDDING_FAILED"
            except Exception:
                match.status = "EVALUATION_ERROR"
                
            results.append(match)
            
        # Rank by similarity descending
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results

    def run_pipeline(self, query_image_bytes: bytes) -> List[CandidateMatch]:
        # Step 1: Extract query embedding (will raise error if invalid input)
        query_embedding = self.face_engine.get_embedding(query_image_bytes)
        
        # Step 2: Search for candidates
        candidates = self.provider.search(query_image_bytes)
        
        if not candidates:
            return []
            
        # Step 3: Evaluate candidates
        return self.evaluate_candidates(query_embedding, candidates)
