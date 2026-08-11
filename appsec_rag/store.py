"""
Vector store (ChromaDB).

Embeds each chunk and persists it in a local Chroma collection with its citation
metadata. Persistent on disk, so you build the index once and query it many times.
"""

from __future__ import annotations

from pathlib import Path

from .embed import embed
from .ingest import Chunk, load_chunks

DEFAULT_DB = str(Path(__file__).resolve().parent.parent / ".chroma")
COLLECTION = "appsec"


def _client(db_path: str):
    import chromadb
    return chromadb.PersistentClient(path=db_path)


def build_index(corpus_dir: str, db_path: str = DEFAULT_DB) -> int:
    """Ingest the corpus, embed every chunk, and (re)build the vector store.
    Returns the number of chunks indexed."""
    chunks: list[Chunk] = load_chunks(corpus_dir)
    if not chunks:
        raise RuntimeError(f"no .md chunks found in {corpus_dir}")

    client = _client(db_path)
    # Fresh build each time so the index always matches the corpus on disk.
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    vectors = embed([c.text for c in chunks])
    col.add(
        ids=[c.id for c in chunks],
        embeddings=vectors,
        documents=[c.text for c in chunks],
        metadatas=[{"source": c.source, "heading": c.heading} for c in chunks],
    )
    return len(chunks)


class IndexNotBuilt(RuntimeError):
    """Raised when a query hits a store that has not been built yet."""


def get_collection(db_path: str = DEFAULT_DB):
    try:
        return _client(db_path).get_collection(COLLECTION)
    except Exception as e:
        # Chroma raises an internal NotFoundError; translate it into a clear,
        # actionable message instead of leaking a library-internal exception.
        raise IndexNotBuilt(
            f"No index found at {db_path!r}. Run `python -m appsec_rag build` first."
        ) from e
