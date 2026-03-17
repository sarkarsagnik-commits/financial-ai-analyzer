<<<<<<< HEAD
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "financial_documents"

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
=======
import os

# LLM configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"

# LLM model
LLM_MODEL = "gpt-4o-mini"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Vector database
VECTOR_DB_PATH = "./vector_store"
>>>>>>> feature/RAG
