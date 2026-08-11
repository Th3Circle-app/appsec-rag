"""Shared embedding model.

Uses ChromaDB's built-in ONNX embedder (all-MiniLM-L6-v2 via onnxruntime): the same
384-dim sentence embeddings you'd get from sentence-transformers, but with no torch
dependency, so the install is light and reproducible and nothing leaves the machine.
Loaded once, cached. No API key, free to run."""

from __future__ import annotations

from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2 (ONNX)"   # 384-dim, local, CPU


@lru_cache(maxsize=1)
def _ef():
    # Chroma's default embedding function IS all-MiniLM-L6-v2 exported to ONNX.
    from chromadb.utils import embedding_functions
    return embedding_functions.DefaultEmbeddingFunction()


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings into 384-dim vectors."""
    vecs = _ef()(list(texts))
    return [list(map(float, v)) for v in vecs]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
