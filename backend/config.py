import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "financial_documents"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str = ""

    # --- RAG Configuration (from feature/RAG) ---
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o-mini"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    VECTOR_DB_PATH: str = "./vector_store"

    class Config:
        env_file = ".env"


settings = Settings()