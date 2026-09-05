from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass(frozen=True)
class FaceEmbedding:
    """Face embedding vector with metadata."""
    vector: np.ndarray
    dimension: int
    normalized: bool = True
    
    def __post_init__(self):
        if self.vector.ndim != 1:
            raise ValueError("Embedding vector must be 1-dimensional")
        if self.dimension != self.vector.shape[0]:
            raise ValueError("Dimension mismatch with vector shape")
    
    def to_bytes(self) -> bytes:
        return self.vector.astype(np.float32).tobytes()
    
    @classmethod
    def from_bytes(cls, data: bytes, dimension: int) -> FaceEmbedding:
        vector = np.frombuffer(data, dtype=np.float32)
        if vector.shape[0] != dimension:
            raise ValueError(f"Expected dimension {dimension}, got {vector.shape[0]}")
        return cls(vector=vector, dimension=dimension)


@dataclass(frozen=True)
class DetectedFace:
    """Represents a detected face in an image."""
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    landmark: Optional[np.ndarray] = None  # 5-point landmarks
    
    @property
    def x1(self) -> int:
        return self.bbox[0]
    
    @property
    def y1(self) -> int:
        return self.bbox[1]
    
    @property
    def x2(self) -> int:
        return self.bbox[2]
    
    @property
    def y2(self) -> int:
        return self.bbox[3]
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class FaceDetectionResult:
    """Result of face detection on an image."""
    faces: tuple[DetectedFace, ...]
    image_width: int
    image_height: int
    
    @property
    def count(self) -> int:
        return len(self.faces)
    
    def get_primary_face(self) -> DetectedFace:
        """Get the primary face (largest by area)."""
        if not self.faces:
            raise ValueError("No faces detected")
        return max(self.faces, key=lambda f: f.area)