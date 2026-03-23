"""Configuration for agents and vector store."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploaded_files"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Load .env from project root so API keys are available.
load_dotenv(BASE_DIR / ".env")

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_SERVER_URL = os.getenv("LLM_SERVER", "http://localhost:1234")
LLM_API_ENDPOINT = f"{LLM_SERVER_URL}/v1/chat/completions"
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
LLM_TIMEOUT = 10  # seconds

# Internet Search Configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_BASE_URL = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com/search.json")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = os.getenv("TAVILY_BASE_URL", "https://api.tavily.com/search")
WEB_SEARCH_TIMEOUT = int(os.getenv("WEB_SEARCH_TIMEOUT", "15"))

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
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
