from src.errors import AppError

class SearchProviderError(AppError):
    pass

class SearchAuthenticationError(SearchProviderError):
    pass

class SearchRateLimitError(SearchProviderError):
    pass

class SearchTimeoutError(SearchProviderError):
    pass

class SearchResponseError(SearchProviderError):
    pass

class CandidateRetrievalError(AppError):
    pass

class CandidateImageError(AppError):
    pass

class CandidateEvaluationError(AppError):
    pass
