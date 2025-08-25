from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HR Resume Formatter"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".doc", ".docx", ".pdf"]
    UPLOAD_DIR: str = "uploads"
    TEMPLATES_DIR: str = "templates"
    OUTPUT_DIR: str = "output"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OCR Settings
    TESSERACT_CMD: Optional[str] = None  # Will use system default
    
    # Processing Settings
    MAX_CONCURRENT_JOBS: int = 10
    JOB_TIMEOUT: int = 300  # 5 minutes
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOAD_DIR, settings.TEMPLATES_DIR, settings.OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)
