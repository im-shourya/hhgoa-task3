import pytest
from unittest.mock import Mock, patch
import numpy as np

from src.config import Settings
from src.face.models import FaceEmbedding
from src.face.engine import FaceEngine
from src.search.models import SearchCandidate, SearchProviderType
from src.verification.retriever import CandidateImageRetriever
from src.verification.evaluator import CandidateEvaluator, CandidateMatch, EvaluationStatus
from src.verification.ranking import CandidateRanker
from src.verification.pipeline import VerificationPipeline
from src.errors import (
    InvalidCandidateURLError,
    SSRFProtectionError,
    CandidateImageTooLargeError,
    CandidateImageInvalidError,
    CandidateRetrievalError,
    CandidateNoFaceError,
    CandidateMultipleFacesError,
    NoEvaluatableCandidatesError,
)


class TestCandidateImageRetriever:
    @pytest.fixture
    def settings(self):
        return Settings(
            retrieval_timeout=5,
            retrieval_max_size=1024,
            retrieval_allowed_schemes=("https",),
            retrieval_blocked_hosts=("localhost", "127.0.0.1"),
            retrieval_blocked_private_ranges=True,
        )
    
    @pytest.fixture
    def retriever(self, settings):
        return CandidateImageRetriever(settings)
    
    def test_validate_url_valid_https(self, retriever):
        parsed = retriever._validate_url("https://example.com/image.jpg")
        assert parsed.scheme == "https"
        assert parsed.netloc == "example.com"
    
    def test_validate_url_invalid_scheme(self, retriever):
        with pytest.raises(InvalidCandidateURLError, match="not allowed"):
            retriever._validate_url("http://example.com/image.jpg")
    
    def test_validate_url_file_scheme(self, retriever):
        with pytest.raises(InvalidCandidateURLError, match="not allowed"):
            retriever._validate_url("file:///etc/passwd")
    
    def test_validate_url_data_scheme(self, retriever):
        with pytest.raises(InvalidCandidateURLError, match="not allowed"):
            retriever._validate_url("data:image/png;base64,abc")
    
    def test_validate_url_javascript_scheme(self, retriever):
        with pytest.raises(InvalidCandidateURLError, match="not allowed"):
            retriever._validate_url("javascript:alert(1)")
    
    def test_validate_url_missing_hostname(self, retriever):
        with pytest.raises(InvalidCandidateURLError, match="missing hostname"):
            retriever._validate_url("https:///path.jpg")
    
    def test_ssrf_localhost(self, retriever):
        parsed = retriever._validate_url("https://localhost/image.jpg")
        with pytest.raises(SSRFProtectionError, match="Blocked hostname"):
            retriever._check_ssrf(parsed)
    
    def test_ssrf_private_ip(self, retriever):
        parsed = retriever._validate_url("https://192.168.1.1/image.jpg")
        with pytest.raises(SSRFProtectionError, match="private"):
            retriever._check_ssrf(parsed)
    
    def test_ssrf_loopback(self, retriever):
        parsed = retriever._validate_url("https://127.0.0.1/image.jpg")
        with pytest.raises(SSRFProtectionError, match="Blocked hostname"):
            retriever._check_ssrf(parsed)
    
    def test_ssrf_metadata_endpoint(self, retriever):
        parsed = retriever._validate_url("https://169.254.169.254/latest/meta-data/")
        with pytest.raises(SSRFProtectionError, match="private/reserved IP"):
            retriever._check_ssrf(parsed)
    
    def test_validate_image_jpeg(self, retriever):
        # Valid JPEG magic bytes
        jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        retriever._validate_image_content(jpeg)  # Should not raise
    
    def test_validate_image_png(self, retriever):
        png = b'\x89PNG\r\n\x1a\n'
        retriever._validate_image_content(png)  # Should not raise
    
    def test_validate_image_invalid(self, retriever):
        with pytest.raises(CandidateImageInvalidError):
            retriever._validate_image_content(b"not an image")
    
    def test_validate_image_empty(self, retriever):
        with pytest.raises(CandidateImageInvalidError, match="Empty"):
            retriever._validate_image_content(b"")
    
    @patch('src.verification.retriever.requests.Session.get')
    def test_retrieve_success(self, mock_get, retriever):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '100'}
        mock_response.iter_content.return_value = [b'\xff\xd8\xff\xe0', b'fake image data']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
        
        result = retriever.retrieve(candidate)
        assert len(result) > 0
        mock_get.assert_called_once()
    
    @patch('src.verification.retriever.requests.Session.get')
    def test_retrieve_timeout(self, mock_get, retriever):
        import requests
        mock_get.side_effect = requests.Timeout()
        
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
        
        with pytest.raises(CandidateRetrievalError, match="Timeout"):
            retriever.retrieve(candidate)
    
    @patch('src.verification.retriever.requests.Session.get')
    def test_retrieve_http_error(self, mock_get, retriever):
        import requests
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.HTTPError("404", response=mock_response)
        
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
        
        with pytest.raises(CandidateRetrievalError, match="HTTP error 404"):
            retriever.retrieve(candidate)
    
    @patch('src.verification.retriever.requests.Session.get')
    def test_retrieve_oversized(self, mock_get, retriever):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        # Return more than max_size (1024)
        mock_response.iter_content.return_value = [b'x' * 2000]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
        
        with pytest.raises(CandidateImageTooLargeError):
            retriever.retrieve(candidate)


class TestCandidateEvaluator:
    @pytest.fixture
    def mock_face_engine(self):
        engine = Mock(spec=FaceEngine)
        return engine
    
    @pytest.fixture
    def mock_retriever(self):
        retriever = Mock(spec=CandidateImageRetriever)
        return retriever
    
    @pytest.fixture
    def evaluator(self, mock_face_engine, mock_retriever):
        return CandidateEvaluator(face_engine=mock_face_engine, retriever=mock_retriever)
    
    @pytest.fixture
    def query_embedding(self):
        vec = np.random.rand(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return FaceEmbedding(vector=vec, dimension=512)
    
    @pytest.fixture
    def candidate(self):
        return SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
    
    def test_evaluate_retrieval_failed(self, evaluator, mock_retriever, query_embedding, candidate):
        from src.errors import CandidateRetrievalError
        mock_retriever.retrieve.side_effect = CandidateRetrievalError("Network error")
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.RETRIEVAL_FAILED
        assert result.similarity is None
        assert result.error_message == "Network error"
    
    def test_evaluate_no_face(self, evaluator, mock_retriever, mock_face_engine, query_embedding, candidate):
        mock_retriever.retrieve.return_value = b"fake image"
        mock_face_engine.get_embedding.side_effect = CandidateNoFaceError("No face")
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.NO_FACE
        assert result.similarity is None
    
    def test_evaluate_multiple_faces(self, evaluator, mock_retriever, mock_face_engine, query_embedding, candidate):
        mock_retriever.retrieve.return_value = b"fake image"
        mock_face_engine.get_embedding.side_effect = CandidateMultipleFacesError("Multiple faces")
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.MULTIPLE_FACES
    
    def test_evaluate_embedding_failed(self, evaluator, mock_retriever, mock_face_engine, query_embedding, candidate):
        mock_retriever.retrieve.return_value = b"fake image"
        mock_face_engine.get_embedding.side_effect = Exception("Embedding failed")
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.EMBEDDING_FAILED
    
    def test_evaluate_match(self, evaluator, mock_retriever, mock_face_engine, query_embedding, candidate):
        mock_retriever.retrieve.return_value = b"fake image"
        
        candidate_emb = FaceEmbedding(
            vector=np.random.rand(512).astype(np.float32),
            dimension=512
        )
        mock_face_engine.get_embedding.return_value = candidate_emb
        mock_face_engine.compare.return_value = 0.8
        mock_face_engine.is_match.return_value = True
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.MATCH
        assert result.similarity == 0.8
        assert result.embedding is not None
    
    def test_evaluate_non_match(self, evaluator, mock_retriever, mock_face_engine, query_embedding, candidate):
        mock_retriever.retrieve.return_value = b"fake image"
        
        candidate_emb = FaceEmbedding(
            vector=np.random.rand(512).astype(np.float32),
            dimension=512
        )
        mock_face_engine.get_embedding.return_value = candidate_emb
        mock_face_engine.compare.return_value = 0.3
        mock_face_engine.is_match.return_value = False
        
        result = evaluator.evaluate(query_embedding, candidate)
        
        assert result.status == EvaluationStatus.NON_MATCH
        assert result.similarity == 0.3
    
    def test_evaluate_batch(self, evaluator, mock_retriever, mock_face_engine, query_embedding):
        candidates = [
            SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id=f"test_{i}",
                page_url=f"https://example.com/page{i}",
                image_url=f"https://example.com/image{i}.jpg",
            )
            for i in range(3)
        ]
        
        mock_retriever.retrieve.return_value = b"fake image"
        mock_face_engine.get_embedding.return_value = FaceEmbedding(
            vector=np.random.rand(512).astype(np.float32),
            dimension=512
        )
        mock_face_engine.compare.return_value = 0.5
        mock_face_engine.is_match.return_value = True
        
        results = evaluator.evaluate_batch(query_embedding, candidates)
        
        assert len(results) == 3
        assert all(r.status == EvaluationStatus.MATCH for r in results)


class TestCandidateRanker:
    def test_rank_empty(self):
        ranker = CandidateRanker()
        result = ranker.rank([])
        
        assert result.total_candidates == 0
        assert result.evaluated_count == 0
        assert result.match_count == 0
        assert result.best_match is None
        assert result.best_evaluated is None
    
    def test_rank_by_similarity_desc(self):
        ranker = CandidateRanker()
        
        matches = []
        for i, sim in enumerate([0.3, 0.8, 0.5, 0.9]):
            candidate = SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id=f"test_{i}",
                page_url=f"https://example.com/page{i}",
                image_url=f"https://example.com/image{i}.jpg",
            )
            match = CandidateMatch(
                candidate=candidate,
                similarity=sim,
                status=EvaluationStatus.MATCH if sim >= 0.45 else EvaluationStatus.NON_MATCH
            )
            matches.append(match)
        
        result = ranker.rank(matches)
        
        assert result.total_candidates == 4
        assert result.evaluated_count == 4
        assert result.match_count == 3  # 0.8, 0.5, 0.9 >= 0.45
        
        # Check ranking order: 0.9, 0.8, 0.5, 0.3
        assert result.ranked[0].similarity == 0.9
        assert result.ranked[1].similarity == 0.8
        assert result.ranked[2].similarity == 0.5
        assert result.ranked[3].similarity == 0.3
        
        # Best match should be first (0.9)
        assert result.best_match.similarity == 0.9
        assert result.best_match.status == EvaluationStatus.MATCH
    
    def test_rank_failed_candidates_last(self):
        ranker = CandidateRanker()
        
        # Evaluated candidates
        evaluated = CandidateMatch(
            candidate=SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="eval_1",
                page_url="https://example.com/page1",
                image_url="https://example.com/image1.jpg",
            ),
            similarity=0.7,
            status=EvaluationStatus.MATCH
        )
        
        # Failed candidate
        failed = CandidateMatch(
            candidate=SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="fail_1",
                page_url="https://example.com/page2",
                image_url="https://example.com/image2.jpg",
            ),
            similarity=None,
            status=EvaluationStatus.RETRIEVAL_FAILED
        )
        
        result = ranker.rank([failed, evaluated])
        
        assert result.ranked[0].match.candidate.provider_result_id == "eval_1"
        assert result.ranked[1].match.candidate.provider_result_id == "fail_1"
    
    def test_rank_deterministic_tie_break(self):
        ranker = CandidateRanker()
        
        # Two candidates with same similarity
        matches = []
        for i in range(2):
            candidate = SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id=f"test_{i}",
                page_url=f"https://example.com/page{i}",
                image_url=f"https://example.com/image{i}.jpg",
            )
            match = CandidateMatch(
                candidate=candidate,
                similarity=0.75,
                status=EvaluationStatus.MATCH
            )
            matches.append(match)
        
        result = ranker.rank(matches)
        
        # Original order should be preserved for ties
        assert result.ranked[0].match.candidate.provider_result_id == "test_0"
        assert result.ranked[1].match.candidate.provider_result_id == "test_1"
    
    def test_no_match_status(self):
        ranker = CandidateRanker()
        
        matches = [
            CandidateMatch(
                candidate=SearchCandidate(
                    provider=SearchProviderType.MOCK,
                    provider_result_id="test_1",
                    page_url="https://example.com/page1",
                    image_url="https://example.com/image1.jpg",
                ),
                similarity=0.3,
                status=EvaluationStatus.NON_MATCH
            ),
            CandidateMatch(
                candidate=SearchCandidate(
                    provider=SearchProviderType.MOCK,
                    provider_result_id="test_2",
                    page_url="https://example.com/page2",
                    image_url="https://example.com/image2.jpg",
                ),
                similarity=0.2,
                status=EvaluationStatus.NON_MATCH
            ),
        ]
        
        result = ranker.rank(matches)
        
        assert result.match_count == 0
        assert result.best_match is None
        assert result.best_evaluated is not None
        assert result.best_evaluated.similarity == 0.3  # Highest among non-matches


class TestVerificationPipeline:
    @pytest.fixture
    def mock_face_engine(self):
        engine = Mock(spec=FaceEngine)
        engine.get_embedding.return_value = FaceEmbedding(
            vector=np.random.rand(512).astype(np.float32),
            dimension=512
        )
        engine.is_match.return_value = True
        engine.compare.return_value = 0.8
        return engine
    
    @pytest.fixture
    def mock_search_provider(self):
        provider = Mock()
        candidate = SearchCandidate(
            provider=SearchProviderType.MOCK,
            provider_result_id="test_1",
            page_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
        )
        provider.search_by_image.return_value = Mock(
            candidates=(candidate,),
            count=1,
            provider=SearchProviderType.MOCK,
            total_results=1,
            search_time_ms=100.0,
            query="[image_search]"
        )
        provider.search.return_value = provider.search_by_image.return_value
        return provider
    
    @pytest.fixture
    def mock_evaluator(self):
        evaluator = Mock()
        match = CandidateMatch(
            candidate=SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="test_1",
                page_url="https://example.com/page",
                image_url="https://example.com/image.jpg",
            ),
            similarity=0.8,
            status=EvaluationStatus.MATCH
        )
        evaluator.evaluate_batch.return_value = [match]
        return evaluator
    
    def test_verify_from_image_success(self, mock_face_engine, mock_search_provider, mock_evaluator):
        pipeline = VerificationPipeline(
            face_engine=mock_face_engine,
            search_provider=mock_search_provider,
            evaluator=mock_evaluator,
        )
        
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        result = pipeline.verify_from_image(buf.tobytes())
        
        assert result.verification_status == "MATCH"
        assert result.has_match is True
        assert result.total_candidates == 1
        assert result.evaluated_candidates == 1
        assert result.matched_candidates == 1
    
    def test_verify_no_candidates(self, mock_face_engine, mock_search_provider, mock_evaluator):
        mock_search_provider.search_by_image.return_value = Mock(
            candidates=(),
            count=0,
            provider=SearchProviderType.MOCK,
            total_results=0,
            search_time_ms=100.0,
            query="[image_search]"
        )
        
        pipeline = VerificationPipeline(
            face_engine=mock_face_engine,
            search_provider=mock_search_provider,
            evaluator=mock_evaluator,
        )
        
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        with pytest.raises(NoEvaluatableCandidatesError):
            pipeline.verify_from_image(buf.tobytes())
    
    def test_verify_no_match(self, mock_face_engine, mock_search_provider, mock_evaluator):
        match = CandidateMatch(
            candidate=SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="test_1",
                page_url="https://example.com/page",
                image_url="https://example.com/image.jpg",
            ),
            similarity=0.3,
            status=EvaluationStatus.NON_MATCH
        )
        mock_evaluator.evaluate_batch.return_value = [match]
        
        pipeline = VerificationPipeline(
            face_engine=mock_face_engine,
            search_provider=mock_search_provider,
            evaluator=mock_evaluator,
        )
        
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        result = pipeline.verify_from_image(buf.tobytes())
        
        assert result.verification_status == "NO_MATCH"
        assert result.has_match is False
    
    def test_verify_no_evaluatable(self, mock_face_engine, mock_search_provider, mock_evaluator):
        match = CandidateMatch(
            candidate=SearchCandidate(
                provider=SearchProviderType.MOCK,
                provider_result_id="test_1",
                page_url="https://example.com/page",
                image_url="https://example.com/image.jpg",
            ),
            similarity=None,
            status=EvaluationStatus.RETRIEVAL_FAILED
        )
        mock_evaluator.evaluate_batch.return_value = [match]
        
        pipeline = VerificationPipeline(
            face_engine=mock_face_engine,
            search_provider=mock_search_provider,
            evaluator=mock_evaluator,
        )
        
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        result = pipeline.verify_from_image(buf.tobytes())
        
        assert result.verification_status == "NO_EVALUATABLE_CANDIDATES"
        assert result.has_match is False