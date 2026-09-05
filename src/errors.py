class FaceError(Exception):
    """Base exception for face processing errors."""
    pass


class InvalidImageError(FaceError):
    """Raised when an image is invalid or cannot be decoded."""
    pass


class NoFaceDetectedError(FaceError):
    """Raised when no face is detected in the image."""
    pass


class MultipleFacesError(FaceError):
    """Raised when multiple faces are detected and policy is to reject."""
    pass


class EmbeddingError(FaceError):
    """Raised when embedding generation fails."""
    pass


class ComparisonError(FaceError):
    """Raised when face comparison fails."""
    pass


class SearchError(Exception):
    """Base exception for search errors."""
    pass


class SearchProviderError(SearchError):
    """Raised when search provider returns an error."""
    pass


class NoResultsError(SearchError):
    """Raised when search returns no results."""
    pass


class CandidateError(Exception):
    """Base exception for candidate processing errors."""
    pass


class CandidateRetrievalError(CandidateError):
    """Raised when candidate image retrieval fails."""
    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class InvalidCandidateURLError(CandidateError):
    """Raised when candidate URL fails validation."""
    pass


class SSRFProtectionError(CandidateError):
    """Raised when URL is blocked by SSRF protection."""
    pass


class CandidateImageTooLargeError(CandidateError):
    """Raised when candidate image exceeds size limit."""
    pass


class CandidateImageInvalidError(CandidateError):
    """Raised when candidate image is not a valid image."""
    pass


class CandidateNoFaceError(CandidateError):
    """Raised when candidate image contains no detectable face."""
    pass


class CandidateMultipleFacesError(CandidateError):
    """Raised when candidate image contains multiple faces."""
    pass


class CandidateEmbeddingError(CandidateError):
    """Raised when candidate embedding generation fails."""
    pass


class EvaluationError(Exception):
    """Base exception for evaluation errors."""
    pass


class NoEvaluatableCandidatesError(EvaluationError):
    """Raised when no candidates can be evaluated."""
    pass


class NoMatchError(EvaluationError):
    """Raised when no candidate meets the match threshold."""
    pass