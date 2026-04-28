"""
embeddings.py
-------------
Creates vector embeddings for text chunks using a local sentence-transformers model.

Why local embeddings (not OpenAI/Anthropic)?
  - Documents are CONFIDENTIAL. Sending text to a remote API breaks privacy.
  - sentence-transformers runs entirely on your machine (CPU or GPU).
  - Model: 'all-MiniLM-L6-v2' — fast, accurate, 384-dim vectors, ~90MB download.

The model is downloaded once and cached locally by HuggingFace.
"""

import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Best balance of speed vs quality for document QA
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton so we only load the model once per process
_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    """Load (or return cached) sentence-transformer model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded.")
    return _model


def embed_texts(texts: List[str], batch_size: int = 64, show_progress: bool = True) -> np.ndarray:
    """
    Embed a list of strings and return an (N, D) float32 numpy array.

    Args:
        texts: List of text strings to embed.
        batch_size: Process this many texts at once (tune for your RAM).
        show_progress: Print a progress bar for large batches.

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    model = get_embedding_model()

    if not texts:
        raise ValueError("No texts provided for embedding.")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2-normalize for cosine similarity via dot product
    )

    logger.info(f"Embedded {len(texts)} texts → shape {embeddings.shape}")
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
    Returns shape (1, D) float32 array for FAISS compatibility.
    """
    model = get_embedding_model()
    vec = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vec.astype(np.float32)
