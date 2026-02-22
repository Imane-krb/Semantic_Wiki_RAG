# 🔍 RAG System – Digital Twin & Building Energy

A **Retrieval-Augmented Generation (RAG)** system that ingests structured knowledge from a MediaWiki ontology about digital twin technology and building energy consumption, retrieves relevant content per user query, generates grounded answers via an Ollama LLM, and logs full traceability for every interaction.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│  MediaWiki   │────▶│  Ingestion    │────▶│  Embedding   │
│  (Ontology)  │     │  (API Parse)  │     │  (MiniLM)    │
└─────────────┘     └───────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│  Streamlit   │◀───│  Generation   │◀───│  ChromaDB    │
│  (Web UI)    │    │  (Ollama LLM) │    │  (VectorDB)  │
└──────┬──────┘     └───────┬───────┘     └──────────────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────────────────┐
│         Traceability Logger              │
│  (JSON traces: query→retrieval→answer)   │
└──────────────────────────────────────────┘
```

### Data Flow

1. **Ingest**: Fetch all pages from MediaWiki API → Parse templates (Article, Author, Institution, Keyword) → Build rich-text documents
2. **Embed**: Chunk documents (1000 chars, 200 overlap) → Generate embeddings (all-MiniLM-L6-v2) → Store in ChromaDB
3. **Query**: User asks question → Embed query → Semantic search in ChromaDB → Retrieve top-k chunks
4. **Generate**: Build grounded prompt (system instruction + context + query) → Send to Ollama → Return answer
5. **Trace**: Log entire flow (query, retrieved docs, prompt, response, latency) to JSON file

---

## 📂 Project Structure

```
Partie RAG/
├── app.py                      # Streamlit web interface
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (wiki URL, Ollama URL)
├── README.md                   # This file
├── src/
│   ├── __init__.py
│   ├── config.py               # Centralized settings
│   ├── ingestion.py            # MediaWiki data extraction
│   ├── embeddings.py           # Text chunking + embedding
│   ├── vector_store.py         # ChromaDB vector store
│   ├── retrieval.py            # Semantic search
│   ├── generation.py           # Ollama LLM generation
│   ├── traceability.py         # JSON trace logging
│   └── rag_pipeline.py         # Pipeline orchestrator
├── data/
│   └── chroma_db/              # Persisted vector store
└── logs/
    └── traces/                 # JSON trace files (one per query)
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9+
- Access to the MediaWiki instance
- Ollama running with a model (e.g., `mistral`)

### Install Dependencies

```bash
cd "Partie RAG"
pip install -r requirements.txt
```

### Configure

Edit `.env` if URLs differ from defaults:

```
MEDIAWIKI_URL=http://10.3.17.196:8080
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
```

---

## 💻 Usage

### Web Interface (Recommended)

```bash
streamlit run app.py
```

1. Click **"Ingest from MediaWiki"** in the sidebar to load data
2. Type a question in the input box
3. View the answer, retrieved sources, and full traceability

### Programmatic Usage

```python
from src.rag_pipeline import RAGPipeline

# Initialize
pipeline = RAGPipeline()

# Ingest data from MediaWiki
pipeline.ingest()

# Ask a question
result = pipeline.query("What is digital twin technology in building energy?")
print(result["answer"])
print(f"Sources: {len(result['sources'])}")
print(f"Trace ID: {result['trace_id']}")
```

---

## 🔗 Traceability

Every query generates a JSON trace file in `logs/traces/`, containing:

| Field                 | Description                   |
| --------------------- | ----------------------------- |
| `trace_id`            | Unique identifier (UUID)      |
| `timestamp`           | ISO 8601 timestamp            |
| `user_query`          | Original question             |
| `retrieved_documents` | Chunks retrieved with scores  |
| `constructed_prompt`  | Full prompt sent to LLM       |
| `llm_response`        | Generated answer              |
| `model_used`          | LLM model name                |
| `latency_ms`          | Retrieval + generation timing |

Example trace location: `logs/traces/trace_abc123.json`

---

## 🧩 Components

| Component        | Technology                     | Purpose                                               |
| ---------------- | ------------------------------ | ----------------------------------------------------- |
| Knowledge Source | MediaWiki API                  | Structured ontology (articles, authors, institutions) |
| Embeddings       | sentence-transformers (MiniLM) | Semantic vector representations                       |
| Vector Store     | ChromaDB                       | Persistent similarity search                          |
| LLM              | Ollama (Mistral)               | Grounded answer generation                            |
| Traceability     | JSON files                     | Full pipeline logging                                 |
| Interface        | Streamlit                      | Interactive web UI                                    |

---

## 📊 MediaWiki Ontology

The knowledge base contains ~400 pages with 4 entity types:

- **Articles**: Research papers about digital twins, building energy, HVAC optimization (fields: title, abstract, DOI, authors, keywords, citation metrics)
- **Authors**: Researchers with affiliations, h-index, publication counts
- **Institutions**: Universities and organizations with country and type
- **Keywords**: Research topics linking articles together

---

## 👥 Team

Developed as part of the Semantic Web + Advanced Databases project.
