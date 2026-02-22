"""
Text Chunking and Embedding Module.

Splits long documents into overlapping chunks while preserving metadata,
then generates embeddings using sentence-transformers.
"""

from typing import Dict, List
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


class EmbeddingEngine:
    """Handles text chunking and embedding generation."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Load the sentence-transformer model."""
        print(f"[Embeddings] Loading model: {model_name} ...")
        self.model = SentenceTransformer(model_name)
        print("[Embeddings] Model loaded successfully.")

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Split documents into smaller chunks with metadata.

        Each chunk dict has:
            - chunk_id: str
            - text: str
            - page_title: str
            - entity_type: str
            - source_url: str
            - chunk_index: int
        """
        chunks = []

        for doc in documents:
            text = doc["text"]
            doc_chunks = self._split_text(text)

            for i, chunk_text in enumerate(doc_chunks):
                chunk = {
                    "chunk_id": f"{doc['page_id']}_{i}",
                    "text": chunk_text,
                    "page_title": doc["page_title"],
                    "entity_type": doc["entity_type"],
                    "source_url": doc["source_url"],
                    "chunk_index": i,
                }
                chunks.append(chunk)

        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.

        Returns a list of embedding vectors.
        """
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a single query string."""
        embedding = self.model.encode([query])
        return embedding[0].tolist()

    # ──────────────────────────────────────────
    # Internal: Text Splitting
    # ──────────────────────────────────────────

    def _split_text(
        self,
        text: str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> List[str]:
        """
        Split text into overlapping chunks.

        For short texts (under chunk_size), return as-is.
        For longer texts, split preferring sentence boundaries.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # If not at the very end, try to break at a sentence boundary
            # Only search in the last 20% of the chunk to keep chunks large
            if end < text_len:
                search_start = start + int(chunk_size * 0.8)
                for sep in ["\n", ". ", "; "]:
                    pos = text.rfind(sep, search_start, end)
                    if pos > start:
                        end = pos + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_len:
                break

            # Advance: step forward by (chunk_end - overlap)
            start = end - overlap

        return chunks
