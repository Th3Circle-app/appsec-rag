"""appsec-rag: a small, honest RAG assistant for application security.

Pipeline: markdown corpus -> heading-aware chunking -> local sentence-transformer
embeddings -> ChromaDB vector store -> cosine retrieval with a relevance floor ->
grounded, cited answers (bring-your-own Claude key, extractive fallback with none).
"""

__version__ = "0.1.0"

from .ingest import Chunk, load_chunks
from .store import build_index, get_collection
from .retrieve import Result, retrieve
from .answer import Answer, answer

__all__ = [
    "Chunk", "load_chunks", "build_index", "get_collection",
    "Result", "retrieve", "Answer", "answer", "__version__",
]
