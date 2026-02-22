"""
RAG System - Streamlit Web Interface.

Provides an interactive UI for:
- Ingesting data from MediaWiki
- Asking questions with full RAG pipeline
- Viewing retrieved sources and traceability logs
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from src.rag_pipeline import RAGPipeline
from src.traceability import TraceLogger

# ──────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────
st.set_page_config(
    page_title="RAG System – Digital Twin & Building Energy",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# Custom CSS for Premium Styling
# ──────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }

    /* Source cards */
    .source-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #667eea;
    }
    .source-card h4 {
        margin: 0 0 0.4rem 0;
        color: #2c3e50;
        font-size: 0.95rem;
    }
    .source-card p {
        margin: 0;
        font-size: 0.85rem;
        color: #555;
        line-height: 1.5;
    }
    .source-card .meta {
        font-size: 0.75rem;
        color: #888;
        margin-top: 0.4rem;
    }

    /* Stats badges */
    .stat-badge {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .stat-badge h3 {
        margin: 0;
        font-size: 1.5rem;
        color: #2c3e50;
    }
    .stat-badge p {
        margin: 0.2rem 0 0 0;
        font-size: 0.8rem;
        color: #666;
    }

    /* Answer box */
    .answer-box {
        background: #304255;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #e9ecef;
        line-height: 1.7;
        font-size: 0.95rem;
    }

    /* Latency bar */
    .latency-info {
        display: flex;
        gap: 1.5rem;
        margin-top: 0.8rem;
        font-size: 0.8rem;
        color: #666;
    }

    /* Sidebar tweaks */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────

@st.cache_resource
def get_pipeline():
    """Initialize the RAG pipeline (cached across sessions)."""
    return RAGPipeline()


# ──────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ System Controls")

    pipeline = get_pipeline()

    # Data stats
    doc_count = pipeline.vector_store.count()
    trace_count = pipeline.trace_logger.get_trace_count()

    st.markdown("### 📊 Knowledge Base Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chunks", doc_count)
    with col2:
        st.metric("Traces", trace_count)

    st.markdown("---")

    # Ingest button
    st.markdown("### 📥 Data Ingestion")
    force_reload = st.checkbox("Force reload (clear & re-ingest)", value=False)

    if st.button("🚀 Ingest from MediaWiki", type="primary", use_container_width=True):
        with st.spinner("Fetching and embedding data from MediaWiki..."):
            stats = pipeline.ingest(force_reload=force_reload)
            if stats["status"] == "completed":
                st.success(
                    f"✅ Ingested {stats['documents_fetched']} documents → "
                    f"{stats['chunks_stored']} chunks"
                )
                st.json(stats)
            elif stats["status"] == "error":
                st.error(
                    f"❌ {stats.get('message', 'Ingestion failed.')} "
                    f"\n\n**Error:** {stats.get('error', 'Unknown')}"
                )
            else:
                st.info(
                    f"Already have {stats['existing_chunks']} chunks. "
                    f"Check 'Force reload' to re-ingest."
                )

    st.markdown("---")

    # LLM connection check
    st.markdown("### 🤖 LLM Status")
    if pipeline.generator.check_connection():
        models = pipeline.generator.list_models()
        st.success(f"✅ Ollama connected")
        if models:
            st.markdown(f"**Models:** {', '.join(models)}")
    else:
        st.error("❌ Cannot reach Ollama server")

    st.markdown("---")

    # Trace history
    st.markdown("### 📋 Recent Traces")
    traces = pipeline.trace_logger.list_traces(limit=5)
    if traces:
        for t in traces:
            with st.expander(f"🔍 {t['user_query'][:40]}..."):
                st.markdown(f"**Time:** {t['timestamp'][:19]}")
                st.markdown(f"**Sources:** {t['num_sources']}")
                st.markdown(f"**Latency:** {t['total_latency_ms']:.0f}ms")
                st.markdown(f"**ID:** `{t['trace_id'][:8]}...`")
    else:
        st.caption("No traces yet. Ask a question!")


# ──────────────────────────────────────────
# Main Content Area
# ──────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 RAG System – Digital Twin & Building Energy</h1>
    <p>Ask questions about digital twin technology, building energy consumption, HVAC systems, and related research.</p>
</div>
""", unsafe_allow_html=True)

# Check if data is ingested
if pipeline.vector_store.count() == 0:
    st.warning(
        "⚠️ The knowledge base is empty. "
        "Click **'Ingest from MediaWiki'** in the sidebar to load data first."
    )

# Query input
query = st.text_input(
    "📝 Ask a question:",
    placeholder="e.g., What is digital twin technology for building energy?",
    label_visibility="visible",
)

# Advanced options
with st.expander("⚡ Advanced Options"):
    top_k = st.slider("Number of sources to retrieve", 1, 15, 5)

# Process query
if query:
    if pipeline.vector_store.count() == 0:
        st.error("Please ingest data first using the sidebar button.")
    else:
        with st.spinner("🔎 Searching knowledge base & generating answer..."):
            result = pipeline.query(query, top_k=top_k)

        # ── Answer Section ──
        st.markdown("### 💡 Answer")
        st.markdown(f'<div class="answer-box">{result["answer"]}</div>',
                    unsafe_allow_html=True)

        # Latency info
        latency = result["latency"]
        st.markdown(
            f'<div class="latency-info">'
            f'<span>🔍 Retrieval: {latency["retrieval_ms"]:.0f}ms</span>'
            f'<span>🤖 Generation: {latency["generation_ms"]:.0f}ms</span>'
            f'<span>⏱️ Total: {latency["total_ms"]:.0f}ms</span>'
            f'<span>📄 Model: {result["model"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        # ── Sources Section ──
        st.markdown("### 📚 Retrieved Sources")
        for i, source in enumerate(result["sources"], 1):
            with st.expander(
                f"Source {i}: {source['page_title']} "
                f"(score: {source['similarity_score']:.2f})",
                expanded=(i <= 2),
            ):
                st.markdown(f"**Type:** {source['entity_type']}")
                st.markdown(f"**Score:** {source['similarity_score']:.4f}")
                st.markdown(f"**URL:** [{source['source_url']}]({source['source_url']})")
                st.markdown("---")
                st.markdown(f"**Content:**\n\n{source['text']}")

        # ── Traceability Section ──
        st.markdown("### 🔗 Traceability")
        with st.expander("View Full Trace (Query → Retrieval → Prompt → Response)", expanded=False):
            trace_data = pipeline.trace_logger.get_trace(result["trace_id"])
            if trace_data:
                st.markdown(f"**Trace ID:** `{trace_data['trace_id']}`")
                st.markdown(f"**Timestamp:** {trace_data['timestamp']}")

                st.markdown("#### Retrieved Documents Summary")
                for doc in trace_data["retrieved_documents"]:
                    st.markdown(
                        f"- **{doc['source_page']}** ({doc['entity_type']}) "
                        f"— score: {doc['similarity_score']:.4f}"
                    )

                st.markdown("#### Constructed Prompt")
                st.code(trace_data["constructed_prompt"], language="text")

                st.markdown("#### LLM Response")
                st.markdown(trace_data["llm_response"])

                st.markdown("#### Latency Breakdown")
                st.json(trace_data["latency_ms"])

                st.markdown("#### Full Trace JSON")
                st.json(trace_data)

        st.caption(f"Trace saved to: `logs/traces/trace_{result['trace_id']}.json`")
