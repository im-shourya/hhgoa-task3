import pytest
from unittest.mock import MagicMock

from src.search.google_lens import GoogleLensBrowserProvider, classify_source
from src.search.models import SearchProviderType, SearchResult
from src.errors import SearchError
from src.search import SearchProviderFactory

@pytest.fixture
def mock_settings(mocker):
    settings = mocker.patch("src.search.google_lens.get_settings")
    settings.return_value.google_lens_timeout = 5000
    settings.return_value.google_lens_headless = True
    return settings.return_value

@pytest.fixture
def dummy_image():
    return b"fake_image_bytes"

@pytest.fixture
def mock_playwright(mocker):
    # Mock the sync_playwright context manager
    mock_sync = mocker.patch("src.search.google_lens.sync_playwright")
    
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_sync.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    # Setup some default safe behaviors for page
    mock_page.url = "https://lens.google.com/search?p=123"
    mock_page.content.return_value = "<html><body></body></html>"
    
    return mock_page, mock_p

def test_provider_initializes(mock_settings):
    provider = GoogleLensBrowserProvider()
    assert provider.provider_type == SearchProviderType.GOOGLE_LENS
    assert provider.timeout == 5000

def test_correct_provider_selected(mock_settings, mocker):
    mocker.patch("src.config.get_settings").return_value.search_provider = "google_lens"
    provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_LENS)
    assert isinstance(provider, GoogleLensBrowserProvider)

def test_never_falls_back_to_mock(mock_settings, mocker):
    mocker.patch("src.config.get_settings").return_value.search_provider = "google_lens"
    provider = SearchProviderFactory.create(SearchProviderType.GOOGLE_LENS)
    assert not isinstance(provider, SearchProviderFactory._providers[SearchProviderType.MOCK])

def test_browser_launch_failure(mock_settings, dummy_image, mock_playwright):
    mock_page, mock_p = mock_playwright
    mock_p.chromium.launch.side_effect = Exception("Browser missing")
    
    provider = GoogleLensBrowserProvider()
    with pytest.raises(SearchError, match="Failed to launch Chromium browser"):
        provider.search_by_image(dummy_image)

def test_timeout_handled_on_navigation(mock_settings, dummy_image, mock_playwright):
    from playwright.sync_api import TimeoutError
    mock_page, mock_p = mock_playwright
    mock_page.goto.side_effect = TimeoutError("Timeout")
    
    provider = GoogleLensBrowserProvider()
    with pytest.raises(SearchError, match="Timeout navigating to Google Images"):
        provider.search_by_image(dummy_image)

def test_upload_operation_attempted_and_timeout(mock_settings, dummy_image, mock_playwright):
    from playwright.sync_api import TimeoutError
    mock_page, mock_p = mock_playwright
    
    # Make locator wait_for fail
    mock_locator = MagicMock()
    mock_locator.wait_for.side_effect = TimeoutError("Timeout")
    mock_page.locator.return_value = mock_locator
    
    provider = GoogleLensBrowserProvider()
    with pytest.raises(SearchError, match="Upload to Google Lens timed out or failed"):
        provider.search_by_image(dummy_image)

def test_captcha_handled(mock_settings, dummy_image, mock_playwright):
    mock_page, mock_p = mock_playwright
    mock_page.url = "https://www.google.com/sorry/index"
    
    provider = GoogleLensBrowserProvider()
    with pytest.raises(SearchError, match="CAPTCHA/Challenge detected"):
        provider.search_by_image(dummy_image)

def test_no_results_handled(mock_settings, dummy_image, mock_playwright):
    mock_page, mock_p = mock_playwright
    mock_locator = MagicMock()
    mock_locator.all.return_value = []
    
    def locator_side_effect(selector):
        if selector == 'a[href]':
            return mock_locator
        # For upload flow
        upl_loc = MagicMock()
        upl_loc.first = upl_loc
        return upl_loc
        
    mock_page.locator.side_effect = locator_side_effect
    
    provider = GoogleLensBrowserProvider()
    result = provider.search_by_image(dummy_image)
    assert result.total_results == 0
    assert len(result.candidates) == 0

def test_fake_html_fixture_parsed_correctly(mock_settings, dummy_image, mock_playwright):
    mock_page, mock_p = mock_playwright
    
    mock_link1 = MagicMock()
    mock_link1.get_attribute.return_value = "https://instagram.com/user1"
    
    mock_link2 = MagicMock()
    mock_link2.get_attribute.return_value = "https://example.com/page2"
    
    # Setup image locators for links
    mock_img1 = MagicMock()
    mock_img1.count.return_value = 1
    mock_img1.get_attribute.return_value = "https://instagram.com/img1.jpg"
    mock_link1.locator.return_value.first = mock_img1
    
    mock_img2 = MagicMock()
    mock_img2.count.return_value = 0 # No image
    mock_link2.locator.return_value.first = mock_img2
    
    mock_a_locator = MagicMock()
    mock_a_locator.all.return_value = [mock_link1, mock_link2]
    
    def locator_side_effect(selector):
        if selector == 'a[href]':
            return mock_a_locator
        upl_loc = MagicMock()
        upl_loc.first = upl_loc
        return upl_loc
        
    mock_page.locator.side_effect = locator_side_effect
    
    provider = GoogleLensBrowserProvider()
    result = provider.search_by_image(dummy_image)
    
    assert result.total_results == 2
    c1, c2 = result.candidates
    
    # Image URL preserved, Page URL preserved, Social media classified
    assert c1.page_url == "https://instagram.com/user1"
    assert c1.image_url == "https://instagram.com/img1.jpg"
    assert c1.search_query == "SOCIAL_MEDIA"
    assert c1.snippet == "instagram.com"
    
    # No image fabricated, Web classified
    assert c2.page_url == "https://example.com/page2"
    assert c2.image_url == "https://example.com/page2" # Fallback is href if None
    assert c2.search_query == "WEB"
    assert c2.snippet == "example.com"
    
    # SearchResult conforms
    assert isinstance(result, SearchResult)

def test_domain_classification():
    assert classify_source("https://instagram.com/p/123") == "SOCIAL_MEDIA"
    assert classify_source("https://www.tiktok.com/@user") == "SOCIAL_MEDIA"
    assert classify_source("https://wikipedia.org/wiki/Face") == "WEB"
    assert classify_source("invalid_url") == "WEB"
