import pytest
import httpx
from unittest.mock import patch, MagicMock
from src.search.google_vision import GoogleVisionSearchProvider
from src.search.models import SearchProviderType
from src.errors import SearchError

@pytest.fixture
def provider():
    # Provide a dummy key so it initializes
    return GoogleVisionSearchProvider(api_key="test_key")

def test_initialization_no_key():
    with patch("src.search.google_vision.get_settings") as mock_settings:
        settings = MagicMock()
        settings.search_api_key = None
        mock_settings.return_value = settings
        with pytest.raises(SearchError, match="Google Cloud Vision API key is not configured"):
            GoogleVisionSearchProvider()

def test_provider_type(provider):
    assert provider.provider_type == SearchProviderType.GOOGLE_VISION

def test_unsupported_textual_search(provider):
    with pytest.raises(SearchError, match="Textual search is unsupported"):
        provider.search("query")

def test_input_validation(provider):
    with pytest.raises(SearchError, match="Input image bytes cannot be empty"):
        provider.search_by_image(b"")

def test_successful_web_detection_response(provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {
                    "pagesWithMatchingImages": [
                        {
                            "url": "https://example.com/page1",
                            "pageTitle": "Test Page 1",
                            "fullMatchingImages": [{"url": "https://example.com/img1.jpg"}]
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test_image_bytes")
        assert result.provider == SearchProviderType.GOOGLE_VISION
        assert result.count == 1
        assert result.candidates[0].page_url == "https://example.com/page1"
        assert result.candidates[0].image_url == "https://example.com/img1.jpg"
        assert result.candidates[0].title == "Test Page 1"
        assert result.candidates[0].search_query == "pages_with_matching_images"

def test_pages_with_matching_images_extraction(provider):
    # Tests extraction with multiple types of matching images on one page
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {
                    "pagesWithMatchingImages": [
                        {
                            "url": "https://example.com/page1",
                            "fullMatchingImages": [{"url": "https://example.com/img1.jpg"}],
                            "partialMatchingImages": [{"url": "https://example.com/img2.jpg"}]
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test")
        assert result.count == 2
        assert result.candidates[0].image_url == "https://example.com/img1.jpg"
        assert result.candidates[1].image_url == "https://example.com/img2.jpg"
        
def test_missing_image_url_handling(provider):
    # A page is found, but no image URL is provided in full/partial arrays
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {
                    "pagesWithMatchingImages": [
                        {
                            "url": "https://example.com/page_no_img",
                            # Missing image arrays
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test")
        # Since we must return an actual discovered image, this should result in 0 candidates
        assert result.count == 0

def test_visually_similar_images_extraction(provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {
                    "visuallySimilarImages": [
                        {"url": "https://example.com/similar.jpg"}
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test")
        assert result.count == 1
        assert result.candidates[0].image_url == "https://example.com/similar.jpg"
        assert result.candidates[0].page_url == "https://example.com/similar.jpg"
        assert result.candidates[0].search_query == "visually_similar_images"

def test_empty_web_detection_response(provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {}
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test")
        assert result.count == 0

def test_google_api_error_response(provider):
    # Simulates a Google API error returned inside a 200 OK wrapper (sometimes happens)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "error": {
                    "message": "Invalid API key"
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        with pytest.raises(SearchError, match="Invalid API key"):
            provider.search_by_image(b"test")

def test_http_network_failure(provider):
    with patch("httpx.Client.post", side_effect=httpx.RequestError("Network is down")):
        with pytest.raises(SearchError, match="Network failure during Google Vision request"):
            provider.search_by_image(b"test")

def test_malformed_response(provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {"invalid": "schema"}
    
    with patch("httpx.Client.post", return_value=mock_response):
        with pytest.raises(SearchError, match="Malformed response: Missing 'responses' array."):
            provider.search_by_image(b"test")

def test_http_status_error(provider):
    # Simulates an HTTP 403 error
    class MockHTTPError(httpx.HTTPStatusError):
        def __init__(self):
            request = httpx.Request("POST", "http://fake")
            response = httpx.Response(403, request=request, json={"error": {"message": "Permission Denied"}})
            super().__init__("HTTP 403", request=request, response=response)

    with patch("httpx.Client.post", side_effect=MockHTTPError()):
        with pytest.raises(SearchError, match="Google Vision API error: Permission Denied"):
            provider.search_by_image(b"test")

def test_candidate_provenance(provider):
    # Ensures provenance is preserved in search_query field
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "responses": [
            {
                "webDetection": {
                    "pagesWithMatchingImages": [
                        {
                            "url": "https://example.com/p",
                            "fullMatchingImages": [{"url": "https://example.com/i"}]
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.Client.post", return_value=mock_response):
        result = provider.search_by_image(b"test")
        assert result.candidates[0].search_query == "pages_with_matching_images"
