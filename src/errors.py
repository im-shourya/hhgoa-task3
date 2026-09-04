class AppError(Exception):
    """Base class for all application errors."""
    pass

class ConfigurationError(AppError):
    pass

class ImageDecodeError(AppError):
    pass

class FaceNotFoundError(AppError):
    pass

class MultipleFacesError(AppError):
    pass

class ModelInitializationError(AppError):
    pass

class FaceProcessingError(AppError):
    pass

class InvalidEmbeddingError(AppError):
    pass
