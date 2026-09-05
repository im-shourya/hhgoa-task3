class SearchProviderError(Exception):
    pass

class SearchAuthenticationError(SearchProviderError):
    pass

class SearchRateLimitError(SearchProviderError):
    pass

class SearchTimeoutError(SearchProviderError):
    pass

class SearchResponseError(SearchProviderError):
    pass

class CandidateRetrievalError(Exception):
    pass

class CandidateImageError(Exception):
    pass

class CandidateEvaluationError(Exception):
    pass
