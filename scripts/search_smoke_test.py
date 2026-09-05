#!/usr/bin/env python
"""
HH Goa 2026 — Phase 3 Live Demonstration Script

This script demonstrates the complete candidate verification pipeline:
1. Load input image
2. Generate query embedding (Phase 1)
3. Execute live search (Phase 2)
4. Retrieve candidate images
5. Evaluate candidate faces
6. Calculate similarities
7. Rank candidates
8. Print best candidate and match status

Usage:
    python scripts/search_smoke_test.py --image path/to/image.jpg [--mode live|mock]

Modes:
    live  - Use real search provider (requires API keys)
    mock  - Use mock provider for offline testing (default)
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

import cv2
import numpy as np

from src.config import get_settings
from src.face.engine import FaceEngine
from src.verification import (
    VerificationPipeline,
    VerificationResult,
)
from src.errors import (
    NoFaceDetectedError,
    MultipleFacesError,
    NoEvaluatableCandidatesError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_image(image_path: str) -> bytes:
    """Load image from file and return bytes."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")
    
    _, buf = cv2.imencode('.jpg', img)
    return buf.tobytes()


def create_sample_image(output_path: str = "fixtures/sample_query.jpg") -> bytes:
    """Create a sample face image for testing (synthetic)."""
    # Create a simple synthetic face-like image
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Draw a simple face oval
    cv2.ellipse(img, (150, 150), (100, 120), 0, 0, 360, (200, 180, 160), -1)
    # Eyes
    cv2.circle(img, (110, 130), 15, (50, 50, 50), -1)
    cv2.circle(img, (190, 130), 15, (50, 50, 50), -1)
    # Nose
    cv2.ellipse(img, (150, 160), (15, 20), 0, 0, 360, (180, 150, 130), -1)
    # Mouth
    cv2.ellipse(img, (150, 200), (30, 15), 0, 0, 180, (100, 50, 50), -1)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, img)
    
    _, buf = cv2.imencode('.jpg', img)
    return buf.tobytes()


def print_verification_result(result: VerificationResult, mode: str) -> None:
    """Print formatted verification results."""
    print("\n" + "=" * 60)
    print(f"PHASE 3 CANDIDATE VERIFICATION — {mode.upper()} MODE")
    print("=" * 60)
    
    print("\nInput:")
    print(f"    Query embedding dimension: {result.query_embedding.dimension}")
    print(f"    Query embedding normalized: {result.query_embedding.normalized}")
    
    print("\nSearch provider:")
    print(f"    {result.search_result.provider.value}")
    
    print("\nSearch results:")
    print(f"    Total results: {result.search_result.total_results}")
    print(f"    Candidates retrieved: {result.search_result.count}")
    
    print("\nCandidate evaluation:")
    print(f"    Candidates evaluated: {result.evaluated_candidates}")
    print(f"    Candidates with matches: {result.matched_candidates}")
    print(f"    Total candidates processed: {result.total_candidates}")
    
    print("\nRanked candidates:")
    print("-" * 60)
    for rc in result.ranking_result.ranked:
        status_symbol = {
            'MATCH': '✓ MATCH',
            'NON_MATCH': '✗ NON_MATCH',
            'NO_FACE': '⚠ NO_FACE',
            'MULTIPLE_FACES': '⚠ MULTIPLE_FACES',
            'RETRIEVAL_FAILED': '✗ RETRIEVAL_FAILED',
            'INVALID_IMAGE': '✗ INVALID_IMAGE',
            'EMBEDDING_FAILED': '✗ EMBEDDING_FAILED',
            'EVALUATED': '? EVALUATED',
        }.get(rc.status.value, rc.status.value)
        
        sim_str = f"{rc.similarity:.4f}" if rc.similarity is not None else "N/A"
        print(f"  #{rc.rank:2d} | {status_symbol:20s} | Sim: {sim_str:>7} | {rc.candidate.image_url}")
        if rc.candidate.title:
            print(f"       Title: {rc.candidate.title}")
        if rc.candidate.page_url != rc.candidate.image_url:
            print(f"       Page:  {rc.candidate.page_url}")
    
    print("-" * 60)
    
    print("\nFinal Result:")
    print(f"    Verification Status: {result.verification_status}")
    
    if result.best_candidate:
        bc = result.best_candidate
        print(f"    Best Candidate: #{bc.rank}")
        print(f"    Best Similarity: {bc.similarity:.4f}" if bc.similarity else "    Best Similarity: N/A")
        print(f"    Best Status: {bc.status.value}")
        print(f"    Image URL: {bc.candidate.image_url}")
        print(f"    Page URL: {bc.candidate.page_url}")
        if bc.candidate.title:
            print(f"    Title: {bc.candidate.title}")
    
    print("\n" + "=" * 60)
    
    if result.verification_status == "MATCH":
        print("✓ REAL MATCHING CANDIDATE DEMONSTRATED")
    elif result.verification_status == "NO_MATCH":
        print("✗ NO MATCH FOUND (best candidate below threshold)")
    elif result.verification_status == "NO_EVALUATABLE_CANDIDATES":
        print("⚠ NO EVALUATABLE CANDIDATES")
    print("=" * 60 + "\n")


def run_mock_demo(image_bytes: bytes, query: str = "test person") -> VerificationResult:
    """Run demonstration with mock provider."""
    logger.info("Running MOCK mode demonstration...")
    
    settings = get_settings()
    settings.search_provider = "mock"
    settings.search_max_results = 5
    
    # Create pipeline with mock provider
    pipeline = VerificationPipeline()
    
    # Use text search for mock demo
    result = pipeline.verify_from_embedding(
        query_embedding=FaceEngine().get_embedding(image_bytes),
        search_query=query,
        max_candidates=5
    )
    
    return result


def run_live_demo(image_bytes: bytes) -> VerificationResult:
    """Run demonstration with live search provider."""
    logger.info("Running LIVE mode demonstration...")
    logger.warning("LIVE MODE: This will make real HTTP requests to search providers")
    
    settings = get_settings()
    
    # Check if live provider is configured
    if settings.search_provider == "mock":
        logger.warning("Live provider not configured, falling back to mock")
        settings.search_provider = "mock"
    
    pipeline = VerificationPipeline()
    
    result = pipeline.verify_from_image(image_bytes)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa 2026 — Phase 3 Candidate Verification Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to input face image (JPG/PNG)",
    )
    parser.add_argument(
        "--mode",
        choices=["live", "mock"],
        default="mock",
        help="Demo mode: live (real search) or mock (offline test)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="person",
        help="Search query for text-based search (mock mode)"
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=10,
        help="Maximum candidates to evaluate"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create a sample face image and exit"
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        sample_path = "fixtures/sample_query.jpg"
        image_bytes = create_sample_image(sample_path)
        print(f"Created sample image: {sample_path}")
        return 0
    
    if not args.image:
        # Try to use sample image
        sample_path = "fixtures/sample_query.jpg"
        if Path(sample_path).exists():
            logger.info(f"No image provided, using sample: {sample_path}")
            args.image = sample_path
        else:
            logger.info("No image provided, creating sample...")
            image_bytes = create_sample_image(sample_path)
            args.image = sample_path
    
    try:
        # Load image
        logger.info(f"Loading image: {args.image}")
        image_bytes = load_image(args.image)
        logger.info(f"Loaded image: {len(image_bytes)} bytes")
        
        # Run appropriate demo
        if args.mode == "live":
            result = run_live_demo(image_bytes)
        else:
            result = run_mock_demo(image_bytes, args.query)
        
        # Print results
        print_verification_result(result, args.mode)
        
        # Exit code based on result
        if result.verification_status == "MATCH":
            return 0
        elif result.verification_status == "NO_MATCH":
            return 1
        else:
            return 2
            
    except NoFaceDetectedError:
        logger.error("No face detected in input image")
        return 3
    except MultipleFacesError:
        logger.error("Multiple faces detected in input image")
        return 4
    except NoEvaluatableCandidatesError as e:
        logger.error(f"No evaluatable candidates: {e}")
        return 5
    except FileNotFoundError as e:
        logger.error(str(e))
        return 6
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 7


if __name__ == "__main__":
    # Import here to avoid circular import
    
    sys.exit(main())