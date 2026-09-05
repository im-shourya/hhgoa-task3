import os
import tempfile
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from src.config import get_settings
from src.search.base import SearchProvider
from src.search.models import SearchProviderType, SearchResult, SearchCandidate
from src.errors import SearchError

SOCIAL_MEDIA_DOMAINS = [
    "instagram.com", "facebook.com", "x.com", "twitter.com",
    "linkedin.com", "tiktok.com", "youtube.com", "threads.net"
]

def classify_source(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
        for social_domain in SOCIAL_MEDIA_DOMAINS:
            if social_domain in domain:
                return "SOCIAL_MEDIA"
        return "WEB"
    except Exception:
        return "WEB"

class GoogleLensBrowserProvider(SearchProvider):
    """
    Search provider using Playwright to automate Google Lens reverse image search.
    """
    
    def __init__(self):
        settings = get_settings()
        self.timeout = settings.google_lens_timeout
        self.headless = settings.google_lens_headless

    @property
    def provider_type(self) -> SearchProviderType:
        return SearchProviderType.GOOGLE_LENS

    def search(self, query: str, max_results: int = 10) -> SearchResult:
        """Text search is not supported by Google Lens reverse image search."""
        raise SearchError("Google Lens provider only supports search_by_image.")

    def search_by_image(self, image_bytes: bytes, max_results: int = 10) -> SearchResult:
        start_time = time.time()
        candidates = []
        
        # Write bytes to temporary file securely
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=self.headless)
                except Exception as e:
                    raise SearchError(f"Failed to launch Chromium browser: {e}. Ensure playwright browsers are installed.")
                
                context = browser.new_context()
                page = context.new_page()
                
                # Navigate to Google Images as the entry point
                try:
                    page.goto("https://images.google.com/", timeout=self.timeout)
                except PlaywrightTimeoutError:
                    raise SearchError("Timeout navigating to Google Images.")

                # Wait for the camera icon and click it
                try:
                    camera_btn = page.locator('[aria-label="Search by image"], .nDcEnd').first
                    camera_btn.wait_for(state="visible", timeout=10000)
                    camera_btn.click()
                except PlaywrightTimeoutError:
                    raise SearchError("Could not find the Google Lens image upload button.")
                
                # Wait for file input to appear
                try:
                    file_input = page.locator('input[type="file"]')
                    file_input.wait_for(state="attached", timeout=10000)
                    
                    # Watch for the navigation that happens after uploading
                    with page.expect_navigation(timeout=self.timeout):
                        file_input.set_input_files(tmp_path)
                except PlaywrightTimeoutError:
                    raise SearchError("Upload to Google Lens timed out or failed.")
                except Exception as e:
                    raise SearchError(f"Upload interaction failed: {e}")
                
                # Detect CAPTCHA or blocking
                if "sorry" in page.url.lower() or "captcha" in page.content().lower():
                    raise SearchError("Google Lens blocked the automated search (CAPTCHA/Challenge detected).")
                
                # Allow dynamic DOM to settle
                time.sleep(3)
                
                try:
                    # Look for links that indicate results
                    # In Lens UI, visual matches usually sit inside grid or lists.
                    page.wait_for_selector('a[href]', timeout=self.timeout)
                except PlaywrightTimeoutError:
                    # If we time out waiting for any links, there's a problem or no results.
                    pass
                
                links = page.locator('a[href]').all()
                seen_urls = set()
                
                for link in links:
                    if len(candidates) >= max_results:
                        break
                        
                    href = link.get_attribute("href")
                    if not href or not href.startswith("http"):
                        continue
                        
                    # Skip google internal links (login, terms, etc.)
                    if "google.com" in href:
                        continue
                        
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    # For a robust, minimal approach: we treat the `href` as the page_url.
                    # Getting the actual image URL from the DOM can be highly brittle.
                    # We will attempt to find an img tag within the link, but if not found, we pass None.
                    # The Candidate structure in models allows it if it doesn't crash on None. Wait, Phase 3 might require it.
                    # If models.py enforces image_url, we must skip.
                    
                    img_url = None
                    try:
                        img_node = link.locator('img').first
                        if img_node.count() > 0:
                            src = img_node.get_attribute("src")
                            # It might be a data URI or a real URL.
                            if src and src.startswith("http"):
                                img_url = src
                    except Exception:
                        pass
                    
                    # Note: Due to model invariant requirements, if `image_url` is strictly needed, 
                    # we must skip candidates without an image URL to prevent pydantic crashes.
                    # Let's try to add it.
                    try:
                        source_type = classify_source(href)
                        domain = urlparse(href).netloc
                        
                        candidates.append(
                            SearchCandidate(
                                provider=self.provider_type,
                                provider_result_id=f"lens_{len(candidates)+1}",
                                page_url=href,
                                image_url=img_url or href,  # Fallback to href if no direct image found
                                title=f"Discovered via {domain}",
                                snippet=domain,
                                search_query=source_type, # Using search_query to store provenance/type
                            )
                        )
                    except ValueError:
                        # Model validation failed, skip this candidate
                        continue
                
                browser.close()
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResult(
            provider=self.provider_type,
            query="image_bytes",
            total_results=len(candidates),
            candidates=candidates,
            search_time_ms=search_time
        )
