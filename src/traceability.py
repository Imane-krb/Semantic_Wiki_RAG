"""
Traceability Module.

Logs each RAG query flow to a separate JSON file for
complete traceability: query → retrieval → prompt → generation.

This enables easy tracking and future statistical analysis.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from src.config import TRACES_DIR


class TraceLogger:
    """
    Logs detailed traces for each RAG pipeline invocation.

    Each trace is saved as a separate JSON file in the traces directory,
    enabling easy review, debugging, and statistical analysis.
    """

    def __init__(self, traces_dir: str = str(TRACES_DIR)):
        self.traces_dir = Path(traces_dir)
        self.traces_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def log_trace(
        self,
        user_query: str,
        retrieved_documents: List[Dict],
        constructed_prompt: str,
        llm_response: str,
        model_used: str,
        retrieval_time_ms: float,
        generation_time_ms: float,
    ) -> str:
        """
        Save a complete trace of a RAG pipeline invocation.

        Args:
            user_query: Original user question
            retrieved_documents: List of retrieved chunk dicts
            constructed_prompt: Full prompt sent to the LLM
            llm_response: LLM's generated answer
            model_used: Name of the LLM model
            retrieval_time_ms: Time taken for retrieval (ms)
            generation_time_ms: Time taken for generation (ms)

        Returns:
            trace_id: The unique identifier for this trace
        """
        trace_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build the trace document
        trace = {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "user_query": user_query,
            "retrieved_documents": [
                {
                    "chunk_id": doc.get("chunk_id", ""),
                    "source_page": doc.get("page_title", ""),
                    "entity_type": doc.get("entity_type", ""),
                    "source_url": doc.get("source_url", ""),
                    "similarity_score": doc.get("similarity_score", 0.0),
                    "content_preview": doc.get("text", "")[:300],
                }
                for doc in retrieved_documents
            ],
            "constructed_prompt": constructed_prompt,
            "llm_response": llm_response,
            "model_used": model_used,
            "latency_ms": {
                "retrieval": round(retrieval_time_ms, 2),
                "generation": round(generation_time_ms, 2),
                "total": round(retrieval_time_ms + generation_time_ms, 2),
            },
            "num_sources_retrieved": len(retrieved_documents),
        }

        # Save to file
        filename = f"trace_{trace_id}.json"
        filepath = self.traces_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)

        return trace_id

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Load a specific trace by its ID."""
        filepath = self.traces_dir / f"trace_{trace_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_traces(self, limit: int = 20) -> List[Dict]:
        """
        List recent traces (summary only) sorted by timestamp descending.

        Returns a list of dicts with trace_id, timestamp, user_query, and latency.
        """
        traces = []
        trace_files = sorted(
            self.traces_dir.glob("trace_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for filepath in trace_files[:limit]:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    traces.append({
                        "trace_id": data["trace_id"],
                        "timestamp": data["timestamp"],
                        "user_query": data["user_query"],
                        "num_sources": data.get("num_sources_retrieved", 0),
                        "total_latency_ms": data["latency_ms"]["total"],
                    })
            except Exception:
                continue

        return traces

    def get_trace_count(self) -> int:
        """Return the total number of traces stored."""
        return len(list(self.traces_dir.glob("trace_*.json")))
