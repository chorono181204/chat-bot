"""App configuration từ .env file."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"  # "gemini" hoặc "ollama"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    EMBEDDING_MODEL: str = "keepitreal/vietnamese-sbert"
    CHUNK_SIZE: int = 256
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        import os
        from pathlib import Path
        env_file = Path(__file__).parent / ".env"


settings = Settings()
