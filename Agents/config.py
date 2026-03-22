"""Configuration for agents and vector store."""
import os
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploaded_files"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_SERVER_URL = os.getenv("LLM_SERVER", "https://medium-helps-justin-hub.trycloudflare.com")
LLM_API_ENDPOINT = f"{LLM_SERVER_URL}/v1/chat/completions"
LLM_MODEL = "local-model"

# ChromaDB Configuration
CHROMA_COLLECTION_PREFIX = "semantic_search"
CHROMA_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight embedding model
CHROMA_PERSIST_DIR = str(CHROMA_DB_DIR)  # Persistent local file

# File Processing Configuration
SUPPORTED_FILE_TYPES = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "csv": "text/csv",
    "json": "application/json",
    "md": "text/markdown"
}

# Chunk Configuration for semantic search
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
