import base64
import time
import httpx
from typing import Optional, Dict, Any, List

from src.config import get_settings
from src.search.base import SearchProvider
from src.search.models import SearchProviderType, SearchResult, SearchCandidate
from src.errors import SearchError


class GoogleVisionSearchProvider(SearchProvider):
    """
    Search provider using Google Cloud Vision Web Detection for reverse image search.
    """
    
    API_URL = "https://vision.googleapis.com/v1/images:annotate"

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.search_api_key
        self.timeout = settings.retrieval_timeout
        if not self.api_key:
            raise SearchError("Google Cloud Vision API key is not configured.")

    @property
    def provider_type(self) -> SearchProviderType:
        return SearchProviderType.GOOGLE_VISION

    def search(self, query: str, max_results: int = 10) -> SearchResult:
        """
        Textual search is unsupported by Google Cloud Vision Web Detection.
        """
        raise SearchError("Textual search is unsupported by Google Cloud Vision Web Detection. Use search_by_image instead.")

    def search_by_image(self, image_bytes: bytes, max_results: int = 10) -> SearchResult:
        """
        Reverse image search using Google Vision WEB_DETECTION.
        """
        if not image_bytes:
            raise SearchError("Input image bytes cannot be empty.")
            
        start_time = time.perf_counter()
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": encoded_image
                    },
                    "features": [
                        {
                            "type": "WEB_DETECTION",
                            "maxResults": max_results
                        }
                    ]
                }
            ]
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.API_URL,
                    params={"key": self.api_key},
                    json=payload
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            # Handle Google API error responses
            try:
                error_details = e.response.json().get("error", {})
                error_msg = error_details.get("message", str(e))
            except Exception:
                error_msg = str(e)
            raise SearchError(f"Google Vision API error: {error_msg}")
        except httpx.RequestError as e:
            raise SearchError(f"Network failure during Google Vision request: {str(e)}")
        except Exception as e:
            raise SearchError(f"Unexpected error during search request: {str(e)}")
            
        # Validate response format
        responses = data.get("responses", [])
        if not responses:
            raise SearchError("Malformed response: Missing 'responses' array.")
            
        vision_response = responses[0]
        if "error" in vision_response:
            err = vision_response["error"]
            raise SearchError(f"Google Vision API returned an error: {err.get('message', 'Unknown error')}")
            
        web_detection = vision_response.get("webDetection", {})
        
        # We will parse candidates from the WEB_DETECTION results
        candidates = self._parse_web_detection(web_detection, max_results)
        
        search_time_ms = (time.perf_counter() - start_time) * 1000
        
        return SearchResult(
            query="[image_search]",
            candidates=tuple(candidates),
            provider=self.provider_type,
            total_results=len(candidates),
            search_time_ms=search_time_ms
        )

    def _parse_web_detection(self, web_detection: Dict[str, Any], max_results: int) -> List[SearchCandidate]:
        candidates: List[SearchCandidate] = []
        candidate_ids = set() # Prevent exact duplicate URL combinations
        
        def add_candidate(page_url: str, image_url: str, title: Optional[str] = None, provenance: Optional[str] = None):
            if len(candidates) >= max_results:
                return
            if not page_url or not image_url:
                return
            
            # Use hash of the URLs for unique identification
            cand_id = f"{page_url}::{image_url}"
            if cand_id in candidate_ids:
                return
            candidate_ids.add(cand_id)
            
            candidates.append(
                SearchCandidate(
                    provider=self.provider_type,
                    provider_result_id=cand_id,
                    page_url=page_url,
                    image_url=image_url,
                    title=title,
                    search_query=provenance  # Storing provenance in search_query field as per prompt example
                )
            )

        # 1. Parse pagesWithMatchingImages
        # These are pages that contain matching images.
        pages = web_detection.get("pagesWithMatchingImages", [])
        for page in pages:
            page_url = page.get("url")
            if not page_url:
                continue
                
            page_title = page.get("pageTitle")
            
            # Prefer full matching images, then partial matching images.
            # If neither exist, we cannot fabricate an image URL or use the input base64.
            # Thus, we only create a candidate if we find an actual image URL.
            
            images = page.get("fullMatchingImages", []) + page.get("partialMatchingImages", [])
            for img in images:
                img_url = img.get("url")
                if img_url:
                    add_candidate(
                        page_url=page_url,
                        image_url=img_url,
                        title=page_title,
                        provenance="pages_with_matching_images"
                    )

        # 2. Parse visuallySimilarImages
        # These are standalone image URLs, but SearchCandidate requires a page_url.
        # We'll use the image_url as the page_url if no page context is available,
        # but realistically, Cloud Vision doesn't provide the host page for visuallySimilarImages.
        similar_images = web_detection.get("visuallySimilarImages", [])
        for img in similar_images:
            img_url = img.get("url")
            if img_url:
                add_candidate(
                    page_url=img_url, # Fallback page_url to the image itself
                    image_url=img_url,
                    title="Visually Similar Image",
                    provenance="visually_similar_images"
                )
                
        # 3. Parse webEntities
        # Entities are metadata concepts (e.g. "Eiffel Tower"). They rarely have a direct image URL,
        # but if we needed to represent them, we'd need page & image URLs. Since they don't provide URLs,
        # they are typically skipped for direct candidate verification, unless they have associated images.
        # The prompt asks: "webEntities extraction if represented by SearchCandidate".
        # Entities only contain: entityId, score, description. So no URLs to extract.
        # We skip them for image verification candidates.

        return candidates
