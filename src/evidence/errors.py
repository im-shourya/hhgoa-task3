from src.errors import AppError

class EvidenceError(AppError):
    pass

class EvidenceCanonicalizationError(EvidenceError):
    pass

class EvidenceVerificationError(EvidenceError):
    pass
