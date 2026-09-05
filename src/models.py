from dataclasses import dataclass
import numpy as np
from src.errors import InvalidEmbeddingError

@dataclass
class FaceEmbedding:
    vector: np.ndarray
    
    def __post_init__(self):
        if self.vector is None or not isinstance(self.vector, np.ndarray) or self.vector.size == 0:
            raise InvalidEmbeddingError("Embedding vector cannot be empty.")
        if not np.isfinite(self.vector).all():
            raise InvalidEmbeddingError("Embedding vector contains non-finite values.")
