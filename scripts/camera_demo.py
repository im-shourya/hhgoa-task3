#!/usr/bin/env python
"""
HH Goa 2026 — Phase 3 Camera Live Demo (Optimized, No Haar Dependency)

Capture face from webcam and run candidate verification pipeline.
Uses raw camera preview (max FPS), InsightFace only on capture.
"""

from __future__ import annotations
import argparse
import logging
import sys

import cv2
import numpy as np

from src.config import get_settings
from src.face.engine import FaceEngine
from src.verification import VerificationPipeline
from src.errors import NoFaceDetectedError, MultipleFacesError, NoEvaluatableCandidatesError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def capture_face_from_camera(camera_index: int = 0, preview: bool = True) -> bytes:
    """
    Capture a single frame from camera with fast raw preview.
    
    Shows raw camera feed for preview (max FPS), runs InsightFace only on capture.
    
    Returns:
        JPEG bytes of the captured frame
    """
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {camera_index}")
    
    # Lower resolution for faster preview
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
    
    logger.info("Camera opened. Press SPACE to capture, ESC to cancel.")
    logger.info("Preview shows raw feed. InsightFace runs only on SPACE press.")
    
    # Initialize InsightFace only when needed (lazy)
    face_engine = None
    
    def get_face_engine():
        nonlocal face_engine
        if face_engine is None:
            logger.info("Initializing InsightFace (first run downloads model ~280MB)...")
            face_engine = FaceEngine()
        return face_engine
    
    captured_frame = None
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Mirror for natural view
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            frame_count += 1
            
            # Status text (no face detection in preview for max speed)
            cv2.putText(display_frame, "Position face in frame", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, "Press SPACE to capture & verify", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            # FPS indicator
            cv2.putText(display_frame, f"Frame: {frame_count}", (10, 460),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if preview:
                cv2.imshow('Face Verification - SPACE=capture, ESC=quit', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                logger.info("Cancelled by user")
                return None
            
            elif key == 32:  # SPACE - Run InsightFace detection
                # Validate with InsightFace (accurate)
                try:
                    engine = get_face_engine()
                    _, buf = cv2.imencode('.jpg', frame)
                    engine.get_embedding(buf.tobytes())  # Validates single face
                    captured_frame = frame.copy()
                    logger.info("Face captured and validated!")
                    break
                except NoFaceDetectedError:
                    logger.warning("No face detected. Try better lighting/angle.")
                except MultipleFacesError:
                    logger.warning("Multiple faces detected. Show only one face.")
    
    finally:
        cap.release()
        if preview:
            cv2.destroyAllWindows()
    
    if captured_frame is None:
        return None
    
    _, buf = cv2.imencode('.jpg', captured_frame)
    return buf.tobytes()


def run_camera_verification(
    image_bytes: bytes,
    mode: str = "mock",
    query: str = "person",
    max_candidates: int = 5
):
    """Run verification pipeline on captured image."""
    
    settings = get_settings()
    settings.search_provider = mode
    settings.search_max_results = max_candidates
    
    logger.info(f"Running {mode.upper()} mode verification...")
    
    pipeline = VerificationPipeline()
    
    if mode == "mock":
        query_embedding = FaceEngine().get_embedding(image_bytes)
        result = pipeline.verify_from_embedding(
            query_embedding=query_embedding,
            search_query=query,
            max_candidates=max_candidates
        )
    else:
        result = pipeline.verify_from_image(
            query_image_bytes=image_bytes,
            max_candidates=max_candidates
        )
    
    return result


def print_result(result):
    """Print formatted verification result."""
    print("\n" + "=" * 60)
    print("PHASE 3 CAMERA VERIFICATION RESULT")
    print("=" * 60)
    
    print(f"\nQuery embedding: {result.query_embedding.dimension}D")
    print(f"Search provider: {result.search_result.provider.value}")
    print(f"Search results: {result.search_result.total_results}")
    print(f"Candidates evaluated: {result.evaluated_candidates}")
    print(f"Matches found: {result.matched_candidates}")
    
    print("\nRanked candidates:")
    print("-" * 60)
    for rc in result.ranking_result.ranked:
        status_map = {
            'MATCH': '✓ MATCH',
            'NON_MATCH': '✗ NON_MATCH',
            'NO_FACE': '⚠ NO_FACE',
            'MULTIPLE_FACES': '⚠ MULTI_FACE',
            'RETRIEVAL_FAILED': '✗ RETRIEVAL_FAIL',
            'INVALID_IMAGE': '✗ INVALID_IMG',
            'EMBEDDING_FAILED': '✗ EMBED_FAIL',
        }
        status = status_map.get(rc.status.value, rc.status.value)
        sim = f"{rc.similarity:.4f}" if rc.similarity else "N/A"
        print(f"  #{rc.rank:2d} | {status:18s} | Sim: {sim:>7} | {rc.candidate.image_url}")
        if rc.candidate.title:
            print(f"       {rc.candidate.title}")
    
    print("-" * 60)
    print(f"\nFinal: {result.verification_status}")
    
    if result.best_candidate:
        bc = result.best_candidate
        print(f"Best: #{bc.rank} | Sim: {bc.similarity:.4f}" if bc.similarity else "Best: N/A")
        print(f"URL: {bc.candidate.image_url}")
    
    print("=" * 60)
    
    if result.verification_status == "MATCH":
        print("✓ MATCHING CANDIDATE FOUND")
    elif result.verification_status == "NO_MATCH":
        print("✗ NO MATCH (below threshold)")
    else:
        print("⚠ NO EVALUATABLE CANDIDATES")


def main():
    parser = argparse.ArgumentParser(description="Camera-based face verification demo (optimized)")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Search mode")
    parser.add_argument("--query", type=str, default="person", help="Search query (mock mode)")
    parser.add_argument("--max-candidates", type=int, default=5, help="Max candidates to evaluate")
    parser.add_argument("--no-preview", action="store_true", help="Disable camera preview window")
    args = parser.parse_args()
    
    try:
        print("\nStarting camera capture (optimized)...")
        print("Position your face in the frame.")
        print("Press SPACE to capture when ready, ESC to quit.\n")
        
        image_bytes = capture_face_from_camera(
            camera_index=args.camera,
            preview=not args.no_preview
        )
        
        if image_bytes is None:
            print("No image captured. Exiting.")
            return 1
        
        print(f"\nCaptured image: {len(image_bytes)} bytes")
        
        result = run_camera_verification(
            image_bytes=image_bytes,
            mode=args.mode,
            query=args.query,
            max_candidates=args.max_candidates
        )
        
        print_result(result)
        
        return 0 if result.verification_status == "MATCH" else 1
        
    except NoFaceDetectedError:
        logger.error("No face detected in captured image")
        return 2
    except MultipleFacesError:
        logger.error("Multiple faces detected")
        return 3
    except NoEvaluatableCandidatesError as e:
        logger.error(f"No evaluatable candidates: {e}")
        return 4
    except RuntimeError as e:
        logger.error(f"Camera error: {e}")
        return 5
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 6


if __name__ == "__main__":
    sys.exit(main())