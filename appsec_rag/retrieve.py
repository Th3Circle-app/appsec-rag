"""
Retrieval.

Embed the question with the same model used for the chunks, then ask Chroma for
the nearest chunks by cosine similarity. Returns results with a similarity score
and the citation label, and applies a minimum-similarity floor so an off-topic
question comes back empty instead of dragging in irrelevant text (the first line
of defense against a confidently wrong answer).
"""

from __future__ import annotations

from dataclasses import dataclass

from .embed import embed_one
from .store import get_collection

MIN_SIMILARITY = 0.25   # below this, a chunk is not really relevant
MAX_QUERY_CHARS = 4000  # cap the query so a giant input can't burn CPU embedding it


@dataclass
class Result:
    text: str
    source: str
    heading: str
    score: float         # cosine similarity in [0, 1], higher is closer

    def citation(self) -> str:
        return f"{self.source} › {self.heading}" if self.heading else self.source


def retrieve(question: str, k: int = 4, db_path: str | None = None) -> list[Result]:
    col = get_collection(db_path) if db_path else get_collection()
    k = max(1, int(k))                           # Chroma rejects n_results <= 0
    qv = embed_one(question[:MAX_QUERY_CHARS])   # bounded input, no resource blowup
    res = col.query(query_embeddings=[qv], n_results=k,
                    include=["documents", "metadatas", "distances"])

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    out: list[Result] = []
    for doc, meta, dist in zip(docs, metas, dists):
        # Chroma cosine "distance" is 1 - similarity; convert back.
        sim = 1.0 - float(dist)
        if sim < MIN_SIMILARITY:
            continue
        out.append(Result(text=doc, source=(meta or {}).get("source", "?"),
                          heading=(meta or {}).get("heading", ""), score=round(sim, 3)))
    return out
