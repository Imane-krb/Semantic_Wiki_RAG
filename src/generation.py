"""
LLM Generation Module.

Connects to the Ollama API and generates grounded answers
using the retrieved context and user query.
"""

import requests
import json
from typing import Dict, Optional
from src.config import OLLAMA_URL, OLLAMA_MODEL


# ──────────────────────────────────────────
# System Prompt for Grounded RAG Generation
# ──────────────────────────────────────────

SYSTEM_PROMPT = """You are a knowledgeable research assistant specializing in digital twin technology, building energy consumption, HVAC systems, and related academic topics.

Your role is to answer questions using ONLY the information provided in the CONTEXT below. Follow these rules strictly:

1. **Ground your answers**: Only use facts from the provided context. Do not make up information.
2. **Cite sources**: When referencing information, mention the source title (e.g., "According to [Source Title]...").
3. **Acknowledge limitations**: If the context does not contain enough information to fully answer the question, say so explicitly.
4. **Be structured**: Organize your response with clear paragraphs. Use bullet points when listing multiple items.
5. **Be concise**: Provide direct, informative answers without unnecessary filler.

If no relevant context is provided, respond with: "I don't have enough information in the knowledge base to answer this question."
"""


class LLMGenerator:
    """Generates answers using the Ollama LLM API."""

    def __init__(
        self,
        ollama_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
    ):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.generate_url = f"{self.ollama_url}/api/generate"

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def generate(
        self,
        query: str,
        context: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> Dict:
        """
        Generate a grounded answer using the LLM.

        Args:
            query: The user's question
            context: Formatted context from retrieved documents
            system_prompt: System instruction for the LLM

        Returns:
            Dict with:
                - answer: str (the generated response)
                - full_prompt: str (the complete prompt sent to the LLM)
                - model: str (model name used)
        """
        # Build the full prompt
        full_prompt = self._build_prompt(query, context, system_prompt)

        # Call the Ollama API
        answer = self._call_ollama(full_prompt)

        return {
            "answer": answer,
            "full_prompt": full_prompt,
            "model": self.model,
        }

    def check_connection(self) -> bool:
        """Check if the Ollama server is reachable."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        """List available models on the Ollama server."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    # ──────────────────────────────────────────
    # Internal: Prompt Construction
    # ──────────────────────────────────────────

    def _build_prompt(
        self, query: str, context: str, system_prompt: str
    ) -> str:
        """Construct the full prompt with system instructions, context, and query."""
        prompt = f"""{system_prompt}

--- CONTEXT START ---
{context}
--- CONTEXT END ---

USER QUESTION: {query}

Please provide a comprehensive, grounded answer based on the context above."""

        return prompt

    # ──────────────────────────────────────────
    # Internal: Ollama API Call
    # ──────────────────────────────────────────

    def _call_ollama(self, prompt: str) -> str:
        """
        Send a generation request to the Ollama API.

        Uses the /api/generate endpoint with streaming disabled.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,      # low temp for factual grounding
                "top_p": 0.9,
                "num_predict": 1024,     # max tokens in response
            },
        }

        try:
            resp = requests.post(
                self.generate_url,
                json=payload,
                timeout=120,  # LLM generation can be slow
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "Error: No response from LLM.")

        except requests.exceptions.ConnectionError:
            return (
                "Error: Could not connect to Ollama server at "
                f"{self.ollama_url}. Please ensure Ollama is running."
            )
        except requests.exceptions.Timeout:
            return "Error: LLM request timed out. Please try again."
        except Exception as e:
            return f"Error generating response: {str(e)}"
