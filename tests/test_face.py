import pytest
import numpy as np
import insightface.app
from unittest.mock import Mock, patch, MagicMock

from src.face.models import FaceEmbedding, DetectedFace, FaceDetectionResult
from src.face.engine import FaceEngine
from src.errors import (
    InvalidImageError,
    NoFaceDetectedError,
    MultipleFacesError,
    EmbeddingError,
    ComparisonError,
)


class TestFaceEmbedding:
    def test_valid_embedding(self):
        vec = np.random.rand(512).astype(np.float32)
        emb = FaceEmbedding(vector=vec, dimension=512)
        assert emb.dimension == 512
        assert emb.vector.shape == (512,)
        assert emb.normalized is True
    
    def test_dimension_mismatch_raises(self):
        vec = np.random.rand(512).astype(np.float32)
        with pytest.raises(ValueError, match="Dimension mismatch"):
            FaceEmbedding(vector=vec, dimension=256)
    
    def test_2d_vector_raises(self):
        vec = np.random.rand(1, 512).astype(np.float32)
        with pytest.raises(ValueError, match="1-dimensional"):
            FaceEmbedding(vector=vec, dimension=512)
    
    def test_to_bytes_roundtrip(self):
        vec = np.random.rand(512).astype(np.float32)
        emb = FaceEmbedding(vector=vec, dimension=512)
        data = emb.to_bytes()
        emb2 = FaceEmbedding.from_bytes(data, 512)
        np.testing.assert_array_almost_equal(emb.vector, emb2.vector)


class TestDetectedFace:
    def test_properties(self):
        face = DetectedFace(bbox=(10, 20, 110, 120), confidence=0.95)
        assert face.x1 == 10
        assert face.y1 == 20
        assert face.x2 == 110
        assert face.y2 == 120
        assert face.width == 100
        assert face.height == 100
        assert face.area == 10000


class TestFaceDetectionResult:
    def test_count(self):
        faces = (
            DetectedFace(bbox=(0, 0, 10, 10), confidence=0.9),
            DetectedFace(bbox=(20, 20, 30, 30), confidence=0.8),
        )
        result = FaceDetectionResult(faces=faces, image_width=100, image_height=100)
        assert result.count == 2
    
    def test_get_primary_face(self):
        faces = (
            DetectedFace(bbox=(0, 0, 10, 10), confidence=0.9),  # area=100
            DetectedFace(bbox=(20, 20, 50, 50), confidence=0.8),  # area=900
        )
        result = FaceDetectionResult(faces=faces, image_width=100, image_height=100)
        primary = result.get_primary_face()
        assert primary.area == 900
    
    def test_get_primary_face_empty_raises(self):
        result = FaceDetectionResult(faces=(), image_width=100, image_height=100)
        with pytest.raises(ValueError, match="No faces detected"):
            result.get_primary_face()


class TestFaceEngine:
    @pytest.fixture
    def mock_insightface(self):
        with patch('insightface.app.FaceAnalysis') as mock_face_analysis:
            mock_app = Mock()
            mock_face_analysis.return_value = mock_app
            # Make the mock iterable for get() method
            mock_app.get.return_value = []
            yield mock_app
    
    def test_initialize(self, mock_insightface):
        engine = FaceEngine()
        engine._initialize()
        assert engine._initialized is True
        # FaceAnalysis is called during initialization
        import insightface.app
        insightface.app.FaceAnalysis.assert_called_once()
        mock_insightface.prepare.assert_called_once()
    
    def test_decode_image_invalid(self):
        engine = FaceEngine()
        with pytest.raises(InvalidImageError):
            engine._decode_image(b"not an image")
    
    def test_compare_identical_embeddings(self):
        engine = FaceEngine()
        vec = np.random.rand(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        emb1 = FaceEmbedding(vector=vec, dimension=512)
        emb2 = FaceEmbedding(vector=vec.copy(), dimension=512)
        sim = engine.compare(emb1, emb2)
        assert abs(sim - 1.0) < 1e-5
    
    def test_compare_orthogonal_embeddings(self):
        engine = FaceEngine()
        vec1 = np.zeros(512, dtype=np.float32)
        vec1[0] = 1.0
        vec2 = np.zeros(512, dtype=np.float32)
        vec2[1] = 1.0
        emb1 = FaceEmbedding(vector=vec1, dimension=512)
        emb2 = FaceEmbedding(vector=vec2, dimension=512)
        sim = engine.compare(emb1, emb2)
        assert abs(sim - 0.0) < 1e-5
    
    def test_compare_dimension_mismatch(self):
        engine = FaceEngine()
        emb1 = FaceEmbedding(vector=np.random.rand(512).astype(np.float32), dimension=512)
        emb2 = FaceEmbedding(vector=np.random.rand(256).astype(np.float32), dimension=256)
        with pytest.raises(ComparisonError, match="dimension mismatch"):
            engine.compare(emb1, emb2)
    
    def test_is_match_threshold(self):
        engine = FaceEngine()
        # Default threshold is 0.45
        assert engine.is_match(0.5) is True
        assert engine.is_match(0.45) is True  # >= threshold
        assert engine.is_match(0.44) is False
        assert engine.is_match(0.0) is False
    
    def test_get_embedding_no_face(self, mock_insightface):
        engine = FaceEngine()
        mock_insightface.get.return_value = []
        
        # Create a minimal valid JPEG
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        with pytest.raises(NoFaceDetectedError):
            engine.get_embedding(buf.tobytes())
    
    def test_get_embedding_multiple_faces(self, mock_insightface):
        engine = FaceEngine()
        
        # Create two mock faces
        mock_face1 = Mock()
        mock_face1.det_score = 0.9
        mock_face1.embedding = np.random.rand(512).astype(np.float32)
        mock_face1.bbox = np.array([0, 0, 50, 50])
        mock_face1.kps = None
        
        mock_face2 = Mock()
        mock_face2.det_score = 0.8
        mock_face2.embedding = np.random.rand(512).astype(np.float32)
        mock_face2.bbox = np.array([60, 60, 110, 110])
        mock_face2.kps = None
        
        mock_insightface.get.return_value = [mock_face1, mock_face2]
        
        import cv2
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        with pytest.raises(MultipleFacesError):
            engine.get_embedding(buf.tobytes())
    
    def test_get_embedding_success(self, mock_insightface):
        engine = FaceEngine()
        
        mock_face = Mock()
        mock_face.det_score = 0.9
        embedding_vec = np.random.rand(512).astype(np.float32)
        mock_face.embedding = embedding_vec
        mock_face.bbox = np.array([10, 10, 60, 60])
        mock_face.kps = None
        
        mock_insightface.get.return_value = [mock_face]
        
        import cv2
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buf = cv2.imencode('.jpg', img)
        
        emb = engine.get_embedding(buf.tobytes())
        assert emb.dimension == 512
        assert emb.normalized is True
        # Check it's normalized
        assert abs(np.linalg.norm(emb.vector) - 1.0) < 1e-5