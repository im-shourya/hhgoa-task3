import pytest
import hashlib
from src.search.models import SearchCandidate
from src.verification.evaluator import CandidateMatch, EvaluationStatus
from src.evidence.models import EvidenceManifest, EvidenceCandidate, EvidenceVerification, EvidenceProvenance
from src.evidence.canonical import canonicalize_evidence
from src.evidence.hasher import hash_evidence, verify_evidence_hash
from src.evidence.errors import EvidenceVerificationError

@pytest.fixture
def sample_match():
    candidate = SearchCandidate(
        page_url="https://example.com/post123",
        image_url="https://example.com/img123.jpg",
        title="Found Person",
        provider_result_id="vision_99",
        provider="google_vision"
    )
    return CandidateMatch(
        candidate=candidate,
        similarity=0.8734219,
        status=EvaluationStatus.MATCH
    )

def test_evidence_manifest_creation(sample_match):
    evidence = EvidenceManifest.from_candidate_match(sample_match)
    
    assert evidence.schema_version == "1.0"
    assert evidence.candidate.page_url == "https://example.com/post123"
    assert evidence.candidate.image_url == "https://example.com/img123.jpg"
    assert evidence.candidate.domain == "example.com"
    assert evidence.verification.similarity == "0.873422" # Rounded due to .6f formatting
    assert evidence.verification.decision == "MATCH"
    assert evidence.provenance.provider == "google_vision"
    assert evidence.provenance.metadata["provider_result_id"] == "vision_99"
    
def test_canonicalization_deterministic(sample_match):
    evidence1 = EvidenceManifest.from_candidate_match(sample_match)
    evidence2 = EvidenceManifest.from_candidate_match(sample_match)
    
    canonical1 = canonicalize_evidence(evidence1)
    canonical2 = canonicalize_evidence(evidence2)
    
    assert canonical1 == canonical2
    
def test_dictionary_order_independence():
    # If the JSON serialization is strictly ordered, different initial kwargs 
    # will still produce identical keys in the resulting bytes.
    # Python dataclasses have a fixed field order, but for nested metadata dicts:
    prov1 = EvidenceProvenance(provider="prov", metadata={"a": 1, "b": 2})
    prov2 = EvidenceProvenance(provider="prov", metadata={"b": 2, "a": 1})
    
    cand = EvidenceCandidate(page_url="A", image_url="B", domain="C", title="D")
    veri = EvidenceVerification(similarity="1.0", decision="MATCH")
    
    ev1 = EvidenceManifest(schema_version="1", candidate=cand, verification=veri, provenance=prov1)
    ev2 = EvidenceManifest(schema_version="1", candidate=cand, verification=veri, provenance=prov2)
    
    assert canonicalize_evidence(ev1) == canonicalize_evidence(ev2)

def test_sha256_known_value():
    cand = EvidenceCandidate(page_url="A", image_url="B", domain="C", title="D")
    veri = EvidenceVerification(similarity="1.000000", decision="MATCH")
    prov = EvidenceProvenance(provider="prov", metadata={})
    ev = EvidenceManifest(schema_version="1.0", candidate=cand, verification=veri, provenance=prov)
    
    expected_json = '{"candidate":{"domain":"C","image_url":"B","page_url":"A","title":"D"},"provenance":{"metadata":{},"provider":"prov"},"schema_version":"1.0","verification":{"decision":"MATCH","similarity":"1.000000"}}'
    assert canonicalize_evidence(ev).decode("utf-8") == expected_json
    
    expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
    assert hash_evidence(ev) == expected_hash

def test_modified_evidence_different_hash(sample_match):
    ev1 = EvidenceManifest.from_candidate_match(sample_match)
    hash1 = hash_evidence(ev1)
    
    import dataclasses
    sample_match = dataclasses.replace(sample_match, similarity=0.999999)
    ev2 = EvidenceManifest.from_candidate_match(sample_match)
    hash2 = hash_evidence(ev2)
    
    assert hash1 != hash2

def test_hash_format(sample_match):
    ev = EvidenceManifest.from_candidate_match(sample_match)
    h = hash_evidence(ev)
    
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)

def test_verify_evidence_hash(sample_match):
    ev = EvidenceManifest.from_candidate_match(sample_match)
    h = hash_evidence(ev)
    
    # Valid verification
    assert verify_evidence_hash(ev, h) is True
    
    # Tampered verification
    assert verify_evidence_hash(ev, "0" * 64) is False
    
    with pytest.raises(EvidenceVerificationError):
        verify_evidence_hash(ev, "invalid_length")

def test_no_biometric_data(sample_match):
    ev = EvidenceManifest.from_candidate_match(sample_match)
    canonical = canonicalize_evidence(ev).decode("utf-8")
    
    assert "embedding" not in canonical
    assert "face" not in canonical  # No raw face data
    assert "image_bytes" not in canonical
