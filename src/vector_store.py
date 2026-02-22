"""
Vector Store Module.

Manages the ChromaDB persistent vector store for storing
and querying document embeddings.
"""

import chromadb
from typing import Dict, List, Optional
from src.config import CHROMA_DB_DIR, COLLECTION_NAME


class VectorStore:
    """ChromaDB-backed vector store for document chunks."""

    def __init__(
        self,
        persist_dir: str = str(CHROMA_DB_DIR),
        collection_name: str = COLLECTION_NAME,
    ):
        """Initialize the ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
        print(f"[VectorStore] Collection '{collection_name}' ready "
              f"({self.collection.count()} documents).")

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def add_documents(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
    ) -> int:
        """
        Add document chunks with their embeddings to the collection.

        Args:
            chunks: List of chunk dicts (chunk_id, text, metadata fields)
            embeddings: Corresponding embedding vectors

        Returns:
            Number of documents added.
        """
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "page_title": chunk["page_title"],
                "entity_type": chunk["entity_type"],
                "source_url": chunk["source_url"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]

        # Add in batches to avoid memory issues
        batch_size = 100
        added = 0

        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
            )
            added += batch_end - i

        print(f"[VectorStore] Added {added} chunks. "
              f"Total: {self.collection.count()}")
        return added

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        entity_type_filter: Optional[str] = None,
    ) -> Dict:
        """
        Query the vector store for the most similar chunks.

        Args:
            query_embedding: The query embedding vector
            top_k: Number of results to return
            entity_type_filter: Optional filter by entity type

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        where_filter = None
        if entity_type_filter:
            where_filter = {"entity_type": entity_type_filter}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        return results

    def reset(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("[VectorStore] Collection reset.")

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()
