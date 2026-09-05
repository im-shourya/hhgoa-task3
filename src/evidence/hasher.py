import hashlib
from src.evidence.models import EvidenceManifest
from src.evidence.canonical import canonicalize_evidence
from src.evidence.errors import EvidenceVerificationError

def hash_evidence(evidence: EvidenceManifest) -> str:
    """
    Computes the SHA-256 fingerprint of the canonicalized evidence.
    Returns a 64-character hexadecimal digest.
    """
    canonical_bytes = canonicalize_evidence(evidence)
    return hashlib.sha256(canonical_bytes).hexdigest()

def verify_evidence_hash(evidence: EvidenceManifest, expected_hash: str) -> bool:
    """
    Recomputes the hash of the provided evidence and compares it to expected_hash.
    """
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise EvidenceVerificationError("Expected hash must be a 64-character hex string.")
        
    actual_hash = hash_evidence(evidence)
    return actual_hash == expected_hash
