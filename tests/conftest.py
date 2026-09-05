import pytest
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings singleton between tests."""
    from src.config import reload_settings
    reload_settings()
    yield
    reload_settings()