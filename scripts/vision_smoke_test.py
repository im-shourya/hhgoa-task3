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
    print("========================================")
    print("GOOGLE VISION LIVE SEARCH TEST")
    print("========================================\n")
    
    parser = argparse.ArgumentParser(description="Run Google Cloud Vision Web Detection Smoke Test")
    parser.add_argument("--image", type=str, help="Path to local image for testing (creates dummy if omitted)")
    args = parser.parse_args()

    import dotenv
    dotenv.load_dotenv()
    settings = get_settings()

    if not settings.search_api_key:
        print("FAIL — SEARCH_API_KEY is required for Google Vision live mode.")
        sys.exit(1)

    print("Provider:")
    print("GoogleVisionSearchProvider\n")
    
    # Initialize Provider
    try:
        provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_VISION, api_key=settings.search_api_key)
    except Exception as e:
        print(f"Provider Initialization Failed: {e}")
        sys.exit(1)
        
    image_path = args.image if args.image else "dummy 1x1 image"
    print("Input:")
    print(f"{image_path}\n")
    
    print("API:")
    print("Google Cloud Vision WEB_DETECTION\n")

    # Load or create image
    if args.image and os.path.exists(args.image):
        with open(args.image, "rb") as f:
            image_bytes = f.read()
    else:
        # A minimal valid 1x1 transparent PNG
        image_bytes = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082")

    try:
        result = provider.search_by_image(image_bytes, max_results=50)
        print("API request:")
        print("SUCCESS\n")
    except Exception as e:
        print("API request:")
        print(f"FAILED ({e})\n")
        print("========================================")
        print("LIVE GOOGLE VISION SEARCH FAILED")
        print("========================================")
        sys.exit(1)
        
    print("Web detection:")
    print("SUCCESS\n")
    
    # Categorize by provenance
    categories = {
        "pages_with_matching_images": 0,
        "visually_similar_images": 0
    }
    
    for candidate in result.candidates:
        provenance = candidate.search_query
        if provenance in categories:
            categories[provenance] += 1
            
    print("Pages discovered:")
    print(f"{categories['pages_with_matching_images']}\n")
    
    print("Images discovered:")
    print(f"{categories['visually_similar_images']}\n")
    
    print("Candidates generated:")
    print(f"{result.total_results}\n")

    for i, candidate in enumerate(result.candidates, 1):
        provenance = candidate.search_query
        print(f"Candidate #{i}")
        print(f"Source: {provenance}")
        if candidate.page_url != candidate.image_url:
            print(f"Page: {candidate.page_url}")
        print(f"Image: {candidate.image_url}\n")
        
    print("========================================")
    print("LIVE GOOGLE VISION SEARCH VERIFIED")
    print("========================================")

if __name__ == "__main__":
    main()
