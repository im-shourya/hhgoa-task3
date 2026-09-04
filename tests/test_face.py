import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.face import FaceEngine
from src.errors import (
    ImageDecodeError,
    FaceNotFoundError,
    MultipleFacesError,
    InvalidEmbeddingError
)

@pytest.fixture
def mock_face_engine():
    with patch('src.face.FaceAnalysis') as MockFaceAnalysis:
        mock_app = MockFaceAnalysis.return_value
        engine = FaceEngine(model_name="mock_model")
        engine.app = mock_app
        return engine

def test_get_embedding_empty_bytes(mock_face_engine):
    with pytest.raises(ImageDecodeError):
        mock_face_engine.get_embedding(b"")

def test_get_embedding_invalid_image(mock_face_engine):
    with pytest.raises(ImageDecodeError):
        mock_face_engine.get_embedding(b"random_invalid_bytes")

def test_get_embedding_no_face(mock_face_engine):
    mock_face_engine.app.get.return_value = []
    # Provide a valid-looking 1x1 PNG image
    img_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    with pytest.raises(FaceNotFoundError):
        mock_face_engine.get_embedding(img_bytes)

def test_get_embedding_multiple_faces(mock_face_engine):
    face1 = MagicMock()
    face2 = MagicMock()
    mock_face_engine.app.get.return_value = [face1, face2]
    img_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    with pytest.raises(MultipleFacesError):
        mock_face_engine.get_embedding(img_bytes)

def test_get_embedding_success(mock_face_engine):
    face_mock = MagicMock()
    face_mock.normed_embedding = np.array([1.0, 0.0, 0.0])
    mock_face_engine.app.get.return_value = [face_mock]
    img_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    emb = mock_face_engine.get_embedding(img_bytes)
    assert isinstance(emb, np.ndarray)
    assert np.array_equal(emb, np.array([1.0, 0.0, 0.0]))

def test_compare_identical(mock_face_engine):
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([1.0, 0.0])
    sim = mock_face_engine.compare(emb1, emb2)
    assert np.isclose(sim, 1.0)

def test_compare_orthogonal(mock_face_engine):
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([0.0, 1.0])
    sim = mock_face_engine.compare(emb1, emb2)
    assert np.isclose(sim, 0.0)

def test_compare_zero_vector(mock_face_engine):
    emb1 = np.array([0.0, 0.0])
    emb2 = np.array([1.0, 0.0])
    with pytest.raises(InvalidEmbeddingError):
        mock_face_engine.compare(emb1, emb2)

def test_compare_shape_mismatch(mock_face_engine):
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([1.0, 0.0, 0.0])
    with pytest.raises(InvalidEmbeddingError):
        mock_face_engine.compare(emb1, emb2)

def test_compare_invalid_types(mock_face_engine):
    emb1 = np.array([1.0, 0.0])
    with pytest.raises(InvalidEmbeddingError):
        mock_face_engine.compare(emb1, None)
