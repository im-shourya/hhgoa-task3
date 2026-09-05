import os
import sys

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.search.models import CandidateMatch, SearchCandidate
from src.evidence import EvidenceManifest, canonicalize_evidence, hash_evidence

def main():
    print("\nPhase 4 Evidence Hashing Demonstration\n")
    
    # 1. Create a simulated Phase 3 candidate match
    candidate = SearchCandidate(
        url="https://example.com/profile/jane_doe",
        image_url="https://example.com/assets/jane.jpg",
        source_domain="example.com",
        title="Jane Doe - Profile",
        provider="google_vision",
        metadata={"vision_match_type": "fullMatchingImages"}
    )
    
    match = CandidateMatch(
        candidate=candidate,
        similarity=0.873421,
        face_detected=True,
        status="MATCH"
    )
    
    print("Original Phase 3 Output:")
    print(f"URL: {match.candidate.url}")
    print(f"Similarity: {match.similarity}")
    print(f"Status: {match.status}")
    print("-" * 50)
    
    # 2. Convert to Evidence Manifest
    evidence = EvidenceManifest.from_candidate_match(match)
    
    # 3. Canonicalize
    canonical_bytes = canonicalize_evidence(evidence)
    print("\nCanonicalized JSON (Deterministic UTF-8 bytes):")
    print(canonical_bytes.decode("utf-8"))
    
    # 4. Hash
    fingerprint = hash_evidence(evidence)
    print(f"\nSHA-256 Fingerprint:\n{fingerprint}")
    print("-" * 50)
    
    # 5. Tamper Demonstration
    print("\nTamper Demonstration:")
    print("Simulating a tampered similarity score (from 0.873421 to 0.999999)...")
    
    match.similarity = 0.999999
    tampered_evidence = EvidenceManifest.from_candidate_match(match)
    tampered_fingerprint = hash_evidence(tampered_evidence)
    
    print(f"\nOriginal SHA-256: {fingerprint}")
    print(f"Tampered SHA-256: {tampered_fingerprint}")
    
    if fingerprint != tampered_fingerprint:
        print("\n=> TAMPER DETECTED: Hashes do not match!")
    else:
        print("\n=> FAILURE: Hashes incorrectly matched.")
        sys.exit(1)

if __name__ == "__main__":
    main()
