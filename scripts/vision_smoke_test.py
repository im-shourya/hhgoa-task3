import os
import sys
import argparse

# Add the project root to sys.path so we can import src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.config import get_settings
from src.search import SearchProviderFactory
from src.search.models import SearchProviderType

def main():
    print("================================================")
    print("PHASE 2 — GOOGLE CLOUD VISION SMOKE TEST")
    print("================================================\n")
    
    parser = argparse.ArgumentParser(description="Run Google Cloud Vision Web Detection Smoke Test")
    parser.add_argument("--image", type=str, help="Path to local image for testing (creates dummy if omitted)")
    args = parser.parse_args()

    import dotenv
    dotenv.load_dotenv()
    settings = get_settings()

    if not settings.search_api_key:
        print("[ERROR] No API key configured. Please set SEARCH_API_KEY in your .env file.")
        sys.exit(1)

    if settings.search_provider != "google_vision":
        print(f"[!] Warning: Configured search provider is '{settings.search_provider}', overriding to 'google_vision' for smoke test.")

    # Initialize Provider
    try:
        provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_VISION, api_key=settings.search_api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize provider: {e}")
        sys.exit(1)
        
    print(f"[✓] Provider initialized: {provider.provider_type.value}")

    # Load or create image
    if args.image and os.path.exists(args.image):
        print(f"[*] Loading image from {args.image}")
        with open(args.image, "rb") as f:
            image_bytes = f.read()
    else:
        print("[*] No image provided. Generating a 1x1 black PNG dummy image for testing...")
        # A minimal valid 1x1 transparent PNG
        image_bytes = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082")

    print("[*] Sending request to Google Cloud Vision API...")
    
    try:
        result = provider.search_by_image(image_bytes, max_results=50)
    except Exception as e:
        print(f"[ERROR] API request failed: {e}")
        sys.exit(1)
        
    print(f"[✓] Search successful (Time: {result.search_time_ms:.2f}ms)")
    print(f"[*] Discovered {result.total_results} candidates.")
    
    # Categorize by provenance
    categories = {
        "pages_with_matching_images": 0,
        "visually_similar_images": 0
    }
    
    print("\nCandidate URLs:")
    for i, candidate in enumerate(result.candidates, 1):
        provenance = candidate.search_query
        if provenance in categories:
            categories[provenance] += 1
            
        print(f"  {i}. [URL] {candidate.image_url}")
        print(f"     [Origin] {candidate.page_url}")
        print(f"     [Type] {provenance}")
        print()
        
    print("\nSummary by Source:")
    for source, count in categories.items():
        print(f"  - {source}: {count}")

    print("\n================================================")
    print("SMOKE TEST COMPLETE")
    print("================================================\n")

if __name__ == "__main__":
    main()
