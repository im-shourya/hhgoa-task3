import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Face Engine Configuration
    face_model_name: str = Field(default="buffalo_l", description="InsightFace model pack name")
    face_det_size: tuple[int, int] = Field(default=(640, 640), description="Detection input size")
    face_ctx_id: int = Field(default=0, description="GPU context ID (-1 for CPU)")
    face_det_thresh: float = Field(default=0.5, description="Face detection confidence threshold")
    
    # Face Matching Threshold
    face_match_threshold: float = Field(default=0.45, description="Cosine similarity threshold for match")
    
    # Image Retrieval Configuration
    retrieval_timeout: int = Field(default=10, description="HTTP timeout in seconds")
    retrieval_max_size: int = Field(default=10 * 1024 * 1024, description="Max response size in bytes (10MB)")
    retrieval_allowed_schemes: tuple[str, ...] = Field(default=("https",), description="Allowed URL schemes")
    retrieval_blocked_hosts: tuple[str, ...] = Field(
        default=(
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "169.254.169.254",  # AWS metadata
            "metadata.google.internal",  # GCP metadata
        ),
        description="Blocked hostnames for SSRF protection"
    )
    retrieval_blocked_private_ranges: bool = Field(default=True, description="Block private IP ranges")
    
    # Search Provider Configuration
    search_provider: str = Field(default="mock", description="Search provider: mock, duckduckgo, google")
    search_max_results: int = Field(default=10, description="Maximum search results to process")
    search_api_key: Optional[str] = Field(default=None, description="API key for search provider")
    search_cx: Optional[str] = Field(default=None, description="Custom search engine ID for Google")
    
    # General
    log_level: str = Field(default="INFO", description="Logging level")
    env_file: str = Field(default=".env", description="Environment file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    global _settings
    _settings = Settings()
    return _settings