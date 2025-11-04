"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    openai_api_key: str = ""
    chroma_db_path: str = "./data/chroma_db"
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
