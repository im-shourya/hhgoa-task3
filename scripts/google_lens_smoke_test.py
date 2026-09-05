import argparse
import sys
import os

# Add project root to python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.config import get_settings
from src.search import SearchProviderFactory
from src.search.models import SearchProviderType

def main():
    print("========================================")
    print("GOOGLE LENS LIVE SEARCH TEST")
    print("========================================\n")
    
    parser = argparse.ArgumentParser(description="Run Google Lens Browser Provider Smoke Test")
    parser.add_argument("--image", type=str, required=True, help="Path to local image for testing")
    args = parser.parse_args()

    import dotenv
    dotenv.load_dotenv()
    
    # We force headless=False for the demo to see it
    os.environ["GOOGLE_LENS_HEADLESS"] = "False"
    
    settings = get_settings()
    
    print("Input:")
    print(f"{args.image}\n")
    
    print("Browser:")
    print("Chromium\n")

    if not os.path.exists(args.image):
        print(f"Error: image {args.image} not found.")
        sys.exit(1)
        
    with open(args.image, "rb") as f:
        image_bytes = f.read()

    # Initialize Provider
    try:
        provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_LENS)
    except Exception as e:
        print(f"Provider Initialization Failed: {e}")
        sys.exit(1)
        
    try:
        result = provider.search_by_image(image_bytes, max_results=50)
        print("Upload:")
        print("SUCCESS\n")
        print("Google Lens search:")
        print("SUCCESS\n")
    except Exception as e:
        print("Upload:")
        print("FAILED\n")
        print(f"Google Lens search:\nFAILED ({e})\n")
        sys.exit(1)
        
    print("Candidates discovered:")
    print(f"{result.total_results}\n")

    if result.total_results == 0:
        print("No candidates discovered.")
    else:
        for i, candidate in enumerate(result.candidates, 1):
            print(f"Candidate #{i}")
            print(f"URL: {candidate.page_url}")
            print(f"Source: {candidate.snippet}")
            print(f"Type: {candidate.search_query}\n") # provenance mapped to Type
            
            # Print image URL separately if it's different and available
            if candidate.image_url and candidate.image_url != candidate.page_url:
                print(f"Image: {candidate.image_url}\n")
        
    print("========================================")
    print("LIVE GOOGLE LENS SEARCH COMPLETED")
    print("========================================")

if __name__ == "__main__":
    main()
