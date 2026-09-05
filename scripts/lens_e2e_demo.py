import argparse
import sys
import os
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import dotenv
dotenv.load_dotenv()

from src.config import get_settings
from src.search import SearchProviderFactory
from src.search.models import SearchProviderType
from src.face.engine import FaceEngine
from src.verification.retriever import CandidateImageRetriever
from src.evidence.models import EvidenceManifest, EvidenceCandidate, EvidenceVerification, EvidenceProvenance
from src.evidence.hasher import hash_evidence
from src.blockchain.client import BlockchainClient
from src.blockchain.registry import EvidenceRegistryClient
from src.verification.reverify import EvidenceReverificationService

def print_header(title):
    print(f"\n{title}")
    print("─" * len(title))

def main():
    print("╔══════════════════════════════════════╗")
    print("║ HH GOA TASK 3                       ║")
    print("║ Face Identification & Verification  ║")
    print("╚══════════════════════════════════════╝")
    
    parser = argparse.ArgumentParser(description="End-to-End Google Lens Search & Blockchain Anchoring")
    parser.add_argument("--image", type=str, required=True, help="Path to local image")
    args = parser.parse_args()
    
    settings = get_settings()
    
    print_header("INPUT")
    print(f"Image: {os.path.basename(args.image)}")
    
    if not os.path.exists(args.image):
        print("Error: Image not found.")
        sys.exit(1)
        
    with open(args.image, "rb") as f:
        image_bytes = f.read()
        
    engine = FaceEngine()
    try:
        query_embedding = engine.get_embedding(image_bytes)
        print("Face detected: YES")
    except Exception as e:
        print(f"Face detected: NO ({e})")
        sys.exit(1)
        
    print_header("WEB SEARCH")
    print("Provider: Google Lens")
    
    os.environ["GOOGLE_LENS_HEADLESS"] = "False"
    
    provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_LENS)
    try:
        search_result = provider.search_by_image(image_bytes, max_results=10)
        print(f"Candidates discovered: {search_result.total_results}")
    except Exception as e:
        print(f"Search failed: {e}")
        sys.exit(1)
        
    if search_result.total_results == 0:
        print("No candidates discovered. Exiting.")
        sys.exit(0)
        
    # We want to prioritize SOCIAL_MEDIA
    candidates = sorted(search_result.candidates, key=lambda c: 0 if c.search_query == "SOCIAL_MEDIA" else 1)
    
    retriever = CandidateImageRetriever()
    best_match = None
    best_sim = 0.0
    best_candidate_bytes = None
    best_candidate = None
    
    print_header("CANDIDATE")
    
    for candidate in candidates:
        print(f"Source: {candidate.snippet or 'Unknown'} ({candidate.search_query})")
        print(f"URL: {candidate.page_url}")
        
        try:
            cand_bytes = retriever.retrieve(candidate.image_url)
            print("Image retrieved: YES")
            
            try:
                cand_embedding = engine.get_embedding(cand_bytes)
                sim = engine.compare(query_embedding, cand_embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_candidate = candidate
                    best_candidate_bytes = cand_bytes
                    
                if sim >= settings.face_match_threshold:
                    print(f"\nFound match with similarity: {sim:.4f}")
                    break
            except Exception:
                pass
                
        except Exception:
            print("Image retrieved: NO")
            
        print("---")
        
    if not best_candidate:
        print("\nNo face matches found among candidates.")
        sys.exit(0)
        
    print_header("FACE VERIFICATION")
    print(f"Similarity: {best_sim:.4f}")
    print(f"Threshold: {settings.face_match_threshold}")
    is_match = best_sim >= settings.face_match_threshold
    print(f"Result: {'MATCH' if is_match else 'NO MATCH'}")
    
    if not is_match:
        sys.exit(0)
        
    print_header("EVIDENCE")
    ev_candidate = EvidenceCandidate(
        page_url=best_candidate.page_url,
        image_url=best_candidate.image_url,
        domain=best_candidate.snippet or "unknown",
        title=best_candidate.title or ""
    )
    ev_verification = EvidenceVerification(
        similarity_score=best_sim,
        threshold_used=settings.face_match_threshold,
        model_name="buffalo_l",
        is_match=True
    )
    ev_provenance = EvidenceProvenance(
        search_provider="google_lens",
        query_type="image_upload",
        timestamp=int(time.time())
    )
    manifest = EvidenceManifest(
        candidate=ev_candidate,
        verification=ev_verification,
        provenance=ev_provenance
    )
    
    evidence_hash = hash_evidence(manifest)
    print("SHA-256:")
    print(evidence_hash.hex())
    
    print_header("BLOCKCHAIN")
    print(f"Network: {settings.blockchain_network}")
    
    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
    if not private_key:
        print("Registered: NO (Missing BLOCKCHAIN_PRIVATE_KEY)")
    else:
        try:
            bc_client = BlockchainClient()
            registry = EvidenceRegistryClient(bc_client)
            
            tx_receipt = registry.register_evidence(evidence_hash, private_key)
            print("Registered: YES")
            print(f"Transaction: {tx_receipt.transactionHash.hex()}")
            
            print_header("RE-VERIFICATION")
            reverifier = EvidenceReverificationService(registry)
            result = reverifier.reverify_evidence(manifest)
            
            print(f"Original evidence: {'VERIFIED' if result.is_valid else 'FAILED'}")
            
            # Tamper test
            tampered_manifest = EvidenceManifest(
                candidate=ev_candidate,
                verification=EvidenceVerification(
                    similarity_score=best_sim + 0.1, # mutated
                    threshold_used=settings.face_match_threshold,
                    model_name="buffalo_l",
                    is_match=True
                ),
                provenance=ev_provenance
            )
            tampered_result = reverifier.reverify_evidence(tampered_manifest)
            print("\nAfter modification:")
            print("TAMPERED" if not tampered_result.is_valid else "VERIFIED (Unexpected)")
            
        except Exception as e:
            print(f"Registered: FAILED ({e})")

if __name__ == "__main__":
    main()
