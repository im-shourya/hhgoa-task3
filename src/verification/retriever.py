from __future__ import annotations
import logging
import ipaddress
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_settings
from ..errors import (
    CandidateRetrievalError,
    InvalidCandidateURLError,
    SSRFProtectionError,
    CandidateImageTooLargeError,
    CandidateImageInvalidError,
)
from ..search.models import SearchCandidate

logger = logging.getLogger(__name__)


class CandidateImageRetriever:
    """
    Secure candidate image retriever.
    
    Implements:
    - URL validation (scheme, structure)
    - SSRF protection (block private IPs, localhost, metadata endpoints)
    - Response size limits (streaming with max size)
    - Content validation (must be valid image)
    - Timeout handling
    """
    
    def __init__(self, settings=None):
        self._settings = settings or get_settings()
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy and timeout."""
        session = requests.Session()
        
        # Configure retry strategy - only retry on specific transient errors
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _validate_url(self, url: str) -> urlparse.ParseResult:
        """
        Validate URL structure and scheme.
        
        Args:
            url: URL to validate
            
        Returns:
            Parsed URL components
            
        Raises:
            InvalidCandidateURLError: If URL is invalid
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise InvalidCandidateURLError(f"Invalid URL format: {e}")
        
        # Check scheme
        if parsed.scheme not in self._settings.retrieval_allowed_schemes:
            raise InvalidCandidateURLError(
                f"URL scheme '{parsed.scheme}' not allowed. Allowed: {self._settings.retrieval_allowed_schemes}"
            )
        
        # Check hostname
        if not parsed.netloc:
            raise InvalidCandidateURLError("URL missing hostname")
        
        return parsed
    
    def _check_ssrf(self, parsed_url: urlparse.ParseResult) -> None:
        """
        Check for SSRF vulnerabilities.
        
        Args:
            parsed_url: Parsed URL components
            
        Raises:
            SSRFProtectionError: If URL is blocked
        """
        hostname = parsed_url.hostname or ""
        hostname_lower = hostname.lower()
        
        # Check blocked hostnames
        for blocked in self._settings.retrieval_blocked_hosts:
            if hostname_lower == blocked.lower():
                raise SSRFProtectionError(f"Blocked hostname: {hostname}")
        
        # Check private IP ranges if enabled
        if self._settings.retrieval_blocked_private_ranges:
            try:
                # Resolve hostname to IP if needed
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise SSRFProtectionError(f"Blocked private/reserved IP: {ip}")
            except ValueError:
                # Not an IP address, that's fine - we only check if it IS an IP
                pass
        
        # Additional check for metadata endpoints by hostname pattern
        metadata_patterns = [
            "metadata.",
            "169.254.169.254",
            ".internal",
            "localhost",
        ]
        for pattern in metadata_patterns:
            if pattern in hostname_lower:
                raise SSRFProtectionError(f"Blocked metadata endpoint pattern: {hostname}")
    
    def _validate_image_content(self, content: bytes) -> None:
        """
        Validate that content is a valid image.
        
        Args:
            content: Image bytes
            
        Raises:
            CandidateImageInvalidError: If content is not a valid image
        """
        if not content:
            raise CandidateImageInvalidError("Empty image content")
        
        # Check magic bytes for common image formats
        magic_bytes = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'RIFF': 'WEBP',  # RIFF header for WebP
            b'BM': 'BMP',
        }
        
        is_valid = False
        for magic, fmt in magic_bytes.items():
            if content.startswith(magic):
                if fmt == 'WEBP' and len(content) >= 12:
                    # Additional check for WebP
                    if content[8:12] == b'WEBP':
                        is_valid = True
                        break
                else:
                    is_valid = True
                    break
        
        if not is_valid:
            # Try to decode with OpenCV as fallback
            import cv2
            import numpy as np
            nparr = np.frombuffer(content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise CandidateImageInvalidError("Content is not a valid image format")
    
    def retrieve(self, candidate: SearchCandidate) -> bytes:
        """
        Retrieve candidate image with full security validation.
        
        Args:
            candidate: SearchCandidate with image_url
            
        Returns:
            Image bytes
            
        Raises:
            InvalidCandidateURLError: If URL validation fails
            SSRFProtectionError: If URL is blocked by SSRF protection
            CandidateRetrievalError: If HTTP request fails
            CandidateImageTooLargeError: If response exceeds size limit
            CandidateImageInvalidError: If content is not a valid image
        """
        # Validate URL
        parsed_url = self._validate_url(candidate.image_url)
        
        # SSRF protection
        self._check_ssrf(parsed_url)
        
        logger.info(f"Retrieving candidate image from: {candidate.image_url}")
        
        try:
            # Stream the response to enforce size limit
            response = self._session.get(
                candidate.image_url,
                timeout=self._settings.retrieval_timeout,
                stream=True,
                headers={
                    "User-Agent": "HH-Goa-2026-CandidateVerifier/1.0",
                    "Accept": "image/*,*/*;q=0.8",
                }
            )
            response.raise_for_status()
            
            # Check content length if provided
            content_length = response.headers.get('Content-Length')
            if content_length:
                try:
                    cl = int(content_length)
                    if cl > self._settings.retrieval_max_size:
                        raise CandidateImageTooLargeError(
                            f"Content-Length {cl} exceeds limit {self._settings.retrieval_max_size}"
                        )
                except ValueError:
                    pass  # Invalid Content-Length, we'll enforce during streaming
            
            # Stream download with size limit
            content = bytearray()
            max_size = self._settings.retrieval_max_size
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content.extend(chunk)
                    if len(content) > max_size:
                        raise CandidateImageTooLargeError(
                            f"Downloaded content exceeds limit {max_size} bytes"
                        )
            
            image_bytes = bytes(content)
            
            # Validate image content
            self._validate_image_content(image_bytes)
            
            logger.info(f"Successfully retrieved {len(image_bytes)} bytes from {candidate.image_url}")
            return image_bytes
            
        except requests.Timeout:
            raise CandidateRetrievalError(
                f"Timeout retrieving image from {candidate.image_url}",
                url=candidate.image_url
            )
        except requests.HTTPError as e:
            raise CandidateRetrievalError(
                f"HTTP error {e.response.status_code}: {e}",
                status_code=e.response.status_code,
                url=candidate.image_url
            )
        except requests.RequestException as e:
            raise CandidateRetrievalError(
                f"Request failed: {e}",
                url=candidate.image_url
            )
        except (CandidateImageTooLargeError, CandidateImageInvalidError, SSRFProtectionError, InvalidCandidateURLError):
            raise
        except Exception as e:
            raise CandidateRetrievalError(
                f"Unexpected error: {e}",
                url=candidate.image_url
            )


def create_retriever() -> CandidateImageRetriever:
    """Factory function to create a retriever with current settings."""
    return CandidateImageRetriever()