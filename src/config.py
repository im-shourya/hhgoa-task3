import os
from dotenv import load_dotenv
from src.errors import ConfigurationError

load_dotenv()

class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    PIPELINE_MODE = os.getenv("PIPELINE_MODE", "local")
    
    try:
        FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.45"))
    except ValueError:
        raise ConfigurationError("FACE_MATCH_THRESHOLD must be a float.")
        
    FACE_MODEL = os.getenv("FACE_MODEL", "buffalo_l")
    
    try:
        MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "10485760")) # 10MB default
    except ValueError:
        raise ConfigurationError("MAX_IMAGE_SIZE must be an integer.")

    try:
        REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    except ValueError:
        raise ConfigurationError("REQUEST_TIMEOUT must be an integer.")
