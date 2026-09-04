import base64
import httpx
from typing import List
from src.search.base import SearchProvider
from src.search.models import SearchCandidate
from src.search.errors import (
    SearchAuthenticationError,
    SearchRateLimitError,
    SearchTimeoutError,
    SearchResponseError
)

class GoogleVisionProvider(SearchProvider):
    def __init__(self, api_key: str, timeout: int = 30):
        if not api_key:
            raise SearchAuthenticationError("Google Vision API key is required.")
        self.api_key = api_key
        self.timeout = timeout
        self.url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"

    def search(self, image_bytes: bytes) -> List[SearchCandidate]:
        if not image_bytes:
            return []
            
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "requests": [
                {
                    "image": {"content": b64_image},
                    "features": [{"type": "WEB_DETECTION"}]
                }
            ]
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.url, json=payload)
        except httpx.TimeoutException:
            raise SearchTimeoutError("Google Vision API request timed out.")
        except httpx.RequestError as e:
            raise SearchResponseError(f"Google Vision API request failed: {e}")
            
        if response.status_code == 401 or response.status_code == 403:
            raise SearchAuthenticationError("Invalid Google Vision API credentials.")
        if response.status_code == 429:
            raise SearchRateLimitError("Google Vision API rate limit exceeded.")
        if response.status_code != 200:
            raise SearchResponseError(f"Google Vision API returned status {response.status_code}: {response.text}")
            
        try:
            data = response.json()
        except ValueError:
            raise SearchResponseError("Google Vision API returned invalid JSON.")
            
        candidates = []
        try:
            responses = data.get("requests", data.get("responses", []))
            if not responses:
                return []
                
            web_detection = responses[0].get("webDetection", {})
            
            # Extract pages with matching images
            for page in web_detection.get("pagesWithMatchingImages", []):
                page_url = page.get("url")
                page_title = page.get("pageTitle")
                
                # Each page can contain multiple matching images
                for img in page.get("fullMatchingImages", []) + page.get("partialMatchingImages", []):
                    img_url = img.get("url")
                    if page_url and img_url:
                        candidates.append(SearchCandidate(
                            url=page_url,
                            image_url=img_url,
                            title=page_title,
                            source_domain=page_url.split('/')[2] if '//' in page_url else None,
                            provider="GoogleVision",
                            metadata={"match_type": "page_with_matching_image"}
                        ))
                        
            # Also extract visually similar images (these often don't have a parent page context)
            for img in web_detection.get("visuallySimilarImages", []):
                img_url = img.get("url")
                if img_url:
                    candidates.append(SearchCandidate(
                        url=img_url, # Fallback to image URL as the page URL
                        image_url=img_url,
                        title="Visually Similar Image",
                        source_domain=img_url.split('/')[2] if '//' in img_url else None,
                        provider="GoogleVision",
                        metadata={"match_type": "visually_similar_image"}
                    ))
                    
        except Exception as e:
            raise SearchResponseError(f"Failed to parse Google Vision API response: {e}")
            
        return candidates
