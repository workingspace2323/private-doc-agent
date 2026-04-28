"""
agent.py
--------
The RAG (Retrieval-Augmented Generation) agent.

Why LangChain (not LlamaIndex)?
  - LangChain has first-class Anthropic support and simpler chain composition.
  - Better streaming support for real-time UX.
  - More flexible prompt templating for our strict "docs only" constraint.
  - LlamaIndex is excellent for indexing but LangChain wins for agentic pipelines.

The agent is STRICTLY constrained:
  - It receives only the retrieved chunks as context.
  - The system prompt forbids using outside knowledge.
  - If chunks don't contain the answer, it must say so explicitly.
"""

import logging
import os
from typing import List, Dict, Any, Generator

import anthropic

from core.retriever import Retriever

logger = logging.getLogger(__name__)

# ─── Strict RAG System Prompt ──────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a precise document assistant. Your ONLY job is to answer questions \
using the document excerpts provided below. You have NO other knowledge.

STRICT RULES — follow these without exception:
1. Answer ONLY from the provided document excerpts.
2. If the answer is not in the excerpts, respond with exactly:
   "Answer not found in documents."
3. NEVER use your training knowledge, general knowledge, or make assumptions.
4. NEVER guess, infer beyond the text, or say "typically" or "generally".
5. Always cite which document(s) you found the information in.
6. Be concise and direct. Quote relevant passages when helpful.
7. If excerpts partially answer the question, share what IS there and note what's missing.

When citing, use the format: [Source: filename, Chunk N]"""


def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into a readable context block for the LLM."""
    if not chunks:
        return "No relevant document excerpts found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = (
            f"--- Excerpt {i} | Source: {chunk['filename']} "
            f"| Chunk {chunk['chunk_index']+1}/{chunk['total_chunks']} "
            f"| Relevance: {chunk['similarity']:.0%} ---"
        )
        parts.append(f"{header}\n{chunk['text']}")

    return "\n\n".join(parts)


class DocumentAgent:
    """
    The main agent class.

    Usage:
        agent = DocumentAgent(retriever)
        response = agent.answer("What is the refund policy?")
        # response is a dict with 'answer', 'sources', 'chunks'
    """

    def __init__(self, retriever: Retriever, top_k: int = 5):
        self.retriever = retriever
        self.top_k = top_k
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def answer(self, question: str) -> Dict[str, Any]:
        """
        Answer a question from documents. Returns:
        {
            "answer": str,
            "sources": list of unique filenames cited,
            "chunks": list of chunk dicts used,
            "found": bool  (False if "not found in documents")
        }
        """
        # 1. Retrieve relevant chunks
        chunks = self.retriever.retrieve(question, top_k=self.top_k)

        # 2. If no chunks at all, short-circuit
        if not chunks:
            return {
                "answer": "Answer not found in documents.",
                "sources": [],
                "chunks": [],
                "found": False,
            }

        # 3. Build context
        context = build_context_block(chunks)

        # 4. Build user message
        user_message = (
            f"DOCUMENT EXCERPTS:\n\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            f"Answer strictly from the excerpts above."
        )

        # 5. Call Claude API
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            answer_text = response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"LLM call failed: {e}") from e

        # 6. Determine if answer was found
        not_found_phrases = [
            "answer not found in documents",
            "not found in the documents",
            "not present in the provided",
            "cannot find",
            "no information",
        ]
        found = not any(p in answer_text.lower() for p in not_found_phrases)

        # 7. Extract unique sources
        sources = list(dict.fromkeys(c["filename"] for c in chunks))

        return {
            "answer": answer_text,
            "sources": sources,
            "chunks": chunks,
            "found": found,
        }

    def answer_stream(self, question: str) -> Generator[str, None, None]:
        """
        Streaming version of answer(). Yields text tokens as they arrive.
        Use this for the UI to show real-time responses.

        Note: Sources/chunks are retrieved synchronously before streaming starts.
        """
        # Retrieve chunks first
        chunks = self.retriever.retrieve(question, top_k=self.top_k)

        if not chunks:
            yield "Answer not found in documents."
            return

        context = build_context_block(chunks)
        user_message = (
            f"DOCUMENT EXCERPTS:\n\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            f"Answer strictly from the excerpts above."
        )

        # Stream from Claude
        with self.client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text

        # After stream, yield a special sentinel with source info (JSON-encoded)
        import json
        sources = list(dict.fromkeys(c["filename"] for c in chunks))
        meta = {
            "__meta__": True,
            "sources": sources,
            "chunks": [
                {
                    "filename": c["filename"],
                    "chunk_index": c["chunk_index"],
                    "similarity": c["similarity"],
                    "text_preview": c["text"][:120] + "...",
                }
                for c in chunks
            ],
        }
        yield f"\n__SOURCE_META__{json.dumps(meta)}__END_META__"
