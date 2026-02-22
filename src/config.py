"""
Configuration module for the RAG system.

Centralizes all settings: MediaWiki API URL, Ollama endpoint,
embedding model, ChromaDB paths, and retrieval parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ──────────────────────────────────────────────
# Project Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
LOGS_DIR = PROJECT_ROOT / "logs"
TRACES_DIR = LOGS_DIR / "traces"

# Ensure directories exist
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
TRACES_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# MediaWiki Settings
# ──────────────────────────────────────────────
MEDIAWIKI_URL = os.getenv("MEDIAWIKI_URL", "http://10.3.17.196:8080")
MEDIAWIKI_API = f"{MEDIAWIKI_URL}/api.php"

# ──────────────────────────────────────────────
# Ollama LLM Settings
# ──────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ──────────────────────────────────────────────
# Embedding Settings
# ──────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000        # characters per chunk
CHUNK_OVERLAP = 200      # overlap between chunks

# ──────────────────────────────────────────────
# Retrieval Settings
# ──────────────────────────────────────────────
TOP_K = 5                # number of documents to retrieve
COLLECTION_NAME = "mediawiki_rag"
