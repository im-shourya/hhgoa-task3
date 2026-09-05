import cv2
import numpy as np
from insightface.app import FaceAnalysis
from src.errors import (
    ModelInitializationError,
    ImageDecodeError,
    FaceNotFoundError,
    MultipleFacesError,
    InvalidEmbeddingError
)
from src.config import Config
from src.models import FaceEmbedding

class FaceEngine:
    def __init__(self, model_name: str = Config.FACE_MODEL):
        self.model_name = model_name
        try:
            self.app = FaceAnalysis(name=self.model_name, providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize face model {model_name}: {e}")

    def get_embedding(self, image_bytes: bytes) -> np.ndarray:
        if not image_bytes:
            raise ImageDecodeError("Empty image bytes provided.")
            
        if len(image_bytes) > Config.MAX_IMAGE_SIZE:
            raise ImageDecodeError(f"Image size exceeds maximum limit of {Config.MAX_IMAGE_SIZE} bytes.")
            
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            raise ImageDecodeError(f"Failed to decode image bytes: {e}")
            
        if img is None:
            raise ImageDecodeError("Failed to decode image into a valid format.")
            
        # Detect faces
        faces = self.app.get(img)
        
        if len(faces) == 0:
            raise FaceNotFoundError("No face detected in the image.")
        elif len(faces) > 1:
            raise MultipleFacesError(f"Detected {len(faces)} faces; expected exactly 1.")
            
        face = faces[0]
        embedding = face.normed_embedding
        
        # Validates and creates a FaceEmbedding object to ensure invariants
        face_emb = FaceEmbedding(vector=embedding)
        return face_emb.vector

    def compare(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        if emb1 is None or emb2 is None:
            raise InvalidEmbeddingError("Cannot compare None embeddings.")
        if not isinstance(emb1, np.ndarray) or not isinstance(emb2, np.ndarray):
            raise InvalidEmbeddingError("Embeddings must be NumPy arrays.")
        if emb1.size == 0 or emb2.size == 0:
            raise InvalidEmbeddingError("Cannot compare empty embeddings.")
        if emb1.shape != emb2.shape:
            raise InvalidEmbeddingError(f"Embedding shape mismatch: {emb1.shape} vs {emb2.shape}")
        if not np.isfinite(emb1).all() or not np.isfinite(emb2).all():
            raise InvalidEmbeddingError("Cannot compare non-finite embeddings.")
            
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            raise InvalidEmbeddingError("Cannot compare zero-vector embeddings.")
            
        similarity = np.dot(emb1, emb2) / (norm1 * norm2)
        return float(similarity)
