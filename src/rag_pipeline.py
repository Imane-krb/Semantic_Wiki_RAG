"""
RAG Pipeline Orchestrator.

Ties together ingestion, embedding, vector store, retrieval,
generation, and traceability into a single coherent pipeline.
"""

import time
from typing import Dict, List, Optional
from src.config import TOP_K
from src.ingestion import MediaWikiIngester
from src.embeddings import EmbeddingEngine
from src.vector_store import VectorStore
from src.retrieval import Retriever
from src.generation import LLMGenerator
from src.traceability import TraceLogger


class RAGPipeline:
    """
    Main orchestrator for the RAG system.

    Usage:
        pipeline = RAGPipeline()
        pipeline.ingest()                    # Load data from MediaWiki
        result = pipeline.query("What is...") # Ask a question
    """

    def __init__(self):
        """Initialize all pipeline components."""
        print("=" * 60)
        print("  Initializing RAG Pipeline")
        print("=" * 60)

        self.ingester = MediaWikiIngester()
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore()
        self.retriever = Retriever(self.vector_store, self.embedding_engine)
        self.generator = LLMGenerator()
        self.trace_logger = TraceLogger()

        print("=" * 60)
        print("  RAG Pipeline Ready!")
        print("=" * 60)

    # ──────────────────────────────────────────
    # Data Ingestion
    # ──────────────────────────────────────────

    def ingest(self, force_reload: bool = False) -> Dict:
        """
        Ingest all documents from MediaWiki into the vector store.

        Args:
            force_reload: If True, clear existing data and reload

        Returns:
            Stats dict with document and chunk counts
        """
        if self.vector_store.count() > 0 and not force_reload:
            print(f"[Pipeline] Vector store already has "
                  f"{self.vector_store.count()} chunks. "
                  f"Use force_reload=True to re-ingest.")
            return {
                "status": "skipped",
                "existing_chunks": self.vector_store.count(),
            }

        if force_reload:
            self.vector_store.reset()

        try:
            print("\n[Pipeline] Step 1/3: Fetching documents from MediaWiki...")
            start = time.time()
            documents = self.ingester.fetch_all_documents()
            fetch_time = time.time() - start
            print(f"[Pipeline] Fetched {len(documents)} documents "
                  f"in {fetch_time:.1f}s")
        except (ConnectionError, Exception) as e:
            print(f"[Pipeline] ERROR: Could not connect to MediaWiki: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Could not connect to MediaWiki. "
                           "Please ensure the server is running and reachable.",
            }

        # Count by entity type
        entity_counts = {}
        for doc in documents:
            t = doc["entity_type"]
            entity_counts[t] = entity_counts.get(t, 0) + 1
        print(f"[Pipeline] Entity breakdown: {entity_counts}")

        print("\n[Pipeline] Step 2/3: Chunking documents...")
        chunks = self.embedding_engine.chunk_documents(documents)
        print(f"[Pipeline] Created {len(chunks)} chunks")

        print("\n[Pipeline] Step 3/3: Generating embeddings & storing...")
        start = time.time()
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_engine.generate_embeddings(texts)
        embed_time = time.time() - start
        print(f"[Pipeline] Embeddings generated in {embed_time:.1f}s")

        added = self.vector_store.add_documents(chunks, embeddings)

        return {
            "status": "completed",
            "documents_fetched": len(documents),
            "chunks_created": len(chunks),
            "chunks_stored": added,
            "entity_counts": entity_counts,
            "fetch_time_s": round(fetch_time, 1),
            "embedding_time_s": round(embed_time, 1),
        }

    # ──────────────────────────────────────────
    # Query Pipeline
    # ──────────────────────────────────────────

    def query(
        self,
        user_query: str,
        top_k: Optional[int] = None,
    ) -> Dict:
        """
        Execute the full RAG pipeline for a user query.

        Flow: Query → Retrieve → Build Prompt → Generate → Trace

        Args:
            user_query: The user's natural language question
            top_k: Override for number of documents to retrieve

        Returns:
            Dict with:
                - answer: str
                - sources: List[Dict]
                - trace_id: str
                - latency: Dict
        """
        k = top_k or TOP_K

        # Step 1: Retrieve relevant documents
        retrieve_start = time.time()
        retrieved_docs = self.retriever.retrieve(user_query, top_k=k)
        retrieval_time_ms = (time.time() - retrieve_start) * 1000

        # Step 2: Format context
        context = self.retriever.format_context(retrieved_docs)

        # Step 3: Generate answer
        gen_start = time.time()
        gen_result = self.generator.generate(user_query, context)
        generation_time_ms = (time.time() - gen_start) * 1000

        # Step 4: Log trace
        trace_id = self.trace_logger.log_trace(
            user_query=user_query,
            retrieved_documents=retrieved_docs,
            constructed_prompt=gen_result["full_prompt"],
            llm_response=gen_result["answer"],
            model_used=gen_result["model"],
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
        )

        return {
            "answer": gen_result["answer"],
            "sources": retrieved_docs,
            "trace_id": trace_id,
            "model": gen_result["model"],
            "full_prompt": gen_result["full_prompt"],
            "latency": {
                "retrieval_ms": round(retrieval_time_ms, 2),
                "generation_ms": round(generation_time_ms, 2),
                "total_ms": round(retrieval_time_ms + generation_time_ms, 2),
            },
        }
