import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.search.models import SearchCandidate
from src.search.providers.google_vision import GoogleVisionProvider
from src.search.providers.mock import MockSearchProvider
from src.search.evaluator import SearchEvaluator
from src.search.errors import SearchAuthenticationError, SearchRateLimitError
import httpx

@pytest.fixture
def mock_face_engine():
    engine = MagicMock()
    # Assume query embedding is [1.0, 0.0]
    engine.get_embedding.return_value = np.array([1.0, 0.0])
    # Compare simply returns the dot product 
    engine.compare.side_effect = lambda a, b: float(np.dot(a, b))
    return engine

def test_google_vision_provider_missing_key():
    with pytest.raises(SearchAuthenticationError):
        GoogleVisionProvider(api_key="")

@patch('src.search.providers.google_vision.httpx.Client.post')
def test_google_vision_provider_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
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
                    ],
                    "visuallySimilarImages": [
                        {"url": "https://example.com/img2.jpg"}
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    provider = GoogleVisionProvider(api_key="dummy_key")
    candidates = provider.search(b"dummy_image_bytes")
    
    assert len(candidates) == 2
    assert candidates[0].url == "https://example.com/page1"
    assert candidates[0].image_url == "https://example.com/img1.jpg"
    assert candidates[1].image_url == "https://example.com/img2.jpg"

@patch('src.search.providers.google_vision.httpx.Client.post')
def test_google_vision_provider_rate_limit(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_post.return_value = mock_response

    provider = GoogleVisionProvider(api_key="dummy_key")
    with pytest.raises(SearchRateLimitError):
        provider.search(b"dummy")

def test_mock_search_provider():
    provider = MockSearchProvider()
    candidates = provider.search(b"dummy")
    assert len(candidates) == 1
    assert candidates[0].provider == "MockProvider"

@patch('src.search.evaluator.httpx.Client.get')
def test_search_evaluator_pipeline_success(mock_get, mock_face_engine):
    # Mock candidate image retrieval HTTP call
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.content = b"image_bytes_1"
    
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.content = b"image_bytes_2"
    
    # Return different bytes for different candidates
    mock_get.side_effect = [mock_response_1, mock_response_2]

    # Mock FaceEngine embedding generation for the candidates
    # query gets [1.0, 0.0]
    # candidate 1 gets [1.0, 0.0] -> sim 1.0 (MATCH)
    # candidate 2 gets [0.0, 1.0] -> sim 0.0 (NON_MATCH)
    def mock_get_embedding(bytes_in):
        if bytes_in == b"query":
            return np.array([1.0, 0.0])
        elif bytes_in == b"image_bytes_1":
            return np.array([1.0, 0.0])
        elif bytes_in == b"image_bytes_2":
            return np.array([0.0, 1.0])
        return np.array([1.0, 0.0])
        
    mock_face_engine.get_embedding.side_effect = mock_get_embedding

    candidates = [
        SearchCandidate(url="http://page1.com", image_url="http://img1.com"),
        SearchCandidate(url="http://page2.com", image_url="http://img2.com")
    ]
    
    mock_provider = MockSearchProvider(candidates=candidates)
    evaluator = SearchEvaluator(face_engine=mock_face_engine, search_provider=mock_provider)
    
    results = evaluator.run_pipeline(b"query")
    
    assert len(results) == 2
    # Ensure they are ranked
    assert results[0].candidate.url == "http://page1.com"
    assert results[0].status == "MATCH"
    assert results[0].similarity == 1.0
    
    assert results[1].candidate.url == "http://page2.com"
    assert results[1].status == "NON_MATCH"
    assert results[1].similarity == 0.0

@patch('src.search.evaluator.httpx.Client.get')
def test_search_evaluator_image_retrieval_failure(mock_get, mock_face_engine):
    mock_get.side_effect = httpx.RequestError("Failed to fetch")
    
    candidates = [SearchCandidate(url="http://page1.com", image_url="http://img1.com")]
    mock_provider = MockSearchProvider(candidates=candidates)
    
    evaluator = SearchEvaluator(face_engine=mock_face_engine, search_provider=mock_provider)
    results = evaluator.run_pipeline(b"query")
    
    assert len(results) == 1
    assert results[0].status == "IMAGE_RETRIEVAL_FAILED"

def test_search_evaluator_invalid_url(mock_face_engine):
    candidates = [SearchCandidate(url="http://page1.com", image_url="file:///etc/passwd")]
    mock_provider = MockSearchProvider(candidates=candidates)
    
    evaluator = SearchEvaluator(face_engine=mock_face_engine, search_provider=mock_provider)
    results = evaluator.run_pipeline(b"query")
    
    assert len(results) == 1
    assert results[0].status == "IMAGE_RETRIEVAL_FAILED"
