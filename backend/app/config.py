"""
Configuration management for the Customer Service AI application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # AWS Bedrock Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-west-2"
    
    # Application Configuration
    environment: str = "development"
    log_level: str = "INFO"
    
    # Vector Database
    chroma_persist_directory: str = "./chroma_db"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
