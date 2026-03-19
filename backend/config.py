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