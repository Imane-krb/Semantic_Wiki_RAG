"""
Retrieval Module.

Performs semantic search over the vector store and formats
retrieved results for LLM prompt construction.
"""

from typing import Dict, List, Optional
from src.config import TOP_K
from src.embeddings import EmbeddingEngine
from src.vector_store import VectorStore


class Retriever:
    """Handles semantic retrieval from the vector store."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_engine: EmbeddingEngine,
        top_k: int = TOP_K,
    ):
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.top_k = top_k

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        entity_type_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve the most relevant document chunks for a query.

        Args:
            query: The user's natural language query
            top_k: Override for number of results
            entity_type_filter: Optional filter (article, author, etc.)

        Returns:
            List of result dicts, each with:
                - chunk_id: str
                - text: str
                - page_title: str
                - entity_type: str
                - source_url: str
                - similarity_score: float  (0 to 1, higher = more similar)
        """
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.embedding_engine.embed_query(query)

        # Query the vector store
        results = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=k,
            entity_type_filter=entity_type_filter,
        )

        # Format results
        retrieved = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # ChromaDB returns cosine distance; convert to similarity
                distance = results["distances"][0][i]
                similarity = 1 - distance  # cosine similarity = 1 - cosine distance

                retrieved.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "page_title": results["metadatas"][0][i]["page_title"],
                    "entity_type": results["metadatas"][0][i]["entity_type"],
                    "source_url": results["metadatas"][0][i]["source_url"],
                    "similarity_score": round(similarity, 4),
                })

        return retrieved

    def format_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into a context string for the LLM prompt.

        Each source is clearly labeled with its title and type.
        """
        if not retrieved_docs:
            return "No relevant documents found in the knowledge base."

        context_parts = []

        for i, doc in enumerate(retrieved_docs, 1):
            header = (
                f"[Source {i}] {doc['page_title']} "
                f"(Type: {doc['entity_type']}, "
                f"Relevance: {doc['similarity_score']:.2f})"
            )
            context_parts.append(f"{header}\n{doc['text']}")

        return "\n\n---\n\n".join(context_parts)
