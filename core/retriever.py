"""
retriever.py
------------
Given a user question, retrieves the most relevant document chunks
from the FAISS vector store.

Process:
  1. Embed the user query (same model used during ingestion).
  2. Search FAISS index for top-k nearest neighbors.
  3. Return ranked list of chunks with similarity scores.
  4. Optionally de-duplicate: if two chunks from the same file are
     nearly identical (very high score), keep only the best.
"""

import logging
from typing import List, Dict, Any, Tuple

from core.embeddings import embed_query
from core.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Minimum similarity score to include a chunk (0–1 scale, cosine similarity)
MIN_SIMILARITY_THRESHOLD = 0.25


class Retriever:
    """
    Wraps a VectorStore and provides a high-level retrieve() method.
    """

    def __init__(self, vector_store: VectorStore, top_k: int = 5):
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(
        self, query: str, top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant chunks for a query.

        Returns a list of dicts, each with:
          - text: chunk text
          - filename: source file name
          - source: full file path
          - chunk_index: position in document
          - similarity: cosine similarity score (0–1)
        """
        k = top_k or self.top_k

        # Step 1: Embed the query
        query_vec = embed_query(query)

        # Step 2: Search vector store
        raw_results: List[Tuple[Dict, float]] = self.vector_store.search(
            query_vec, top_k=k * 2  # over-fetch for deduplication
        )

        # Step 3: Filter by minimum threshold
        filtered = [
            (chunk, score)
            for chunk, score in raw_results
            if score >= MIN_SIMILARITY_THRESHOLD
        ]

        # Step 4: Deduplicate — if same file has near-identical chunks,
        # keep only the highest scoring one per (file, chunk_index) pair
        seen = set()
        deduped = []
        for chunk, score in filtered:
            key = (chunk["filename"], chunk["chunk_index"])
            if key not in seen:
                seen.add(key)
                deduped.append(
                    {
                        "text": chunk["text"],
                        "filename": chunk["filename"],
                        "source": chunk["source"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk.get("total_chunks", "?"),
                        "similarity": round(score, 4),
                    }
                )

        # Step 5: Return top-k after dedup, sorted by score descending
        results = sorted(deduped, key=lambda x: x["similarity"], reverse=True)[:k]

        logger.info(
            f"Query: '{query[:60]}...' → {len(results)} chunks retrieved "
            f"(top score: {results[0]['similarity'] if results else 'N/A'})"
        )
        return results

    def has_relevant_results(self, results: List[Dict]) -> bool:
        """Returns True if any result meets the confidence threshold."""
        return len(results) > 0 and results[0]["similarity"] >= MIN_SIMILARITY_THRESHOLD
