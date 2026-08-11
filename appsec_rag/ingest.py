"""
Ingestion + chunking.

RAG lives or dies on chunking: too big and retrieval drags in noise, too small
and a chunk loses the context that makes it answerable. This splits each markdown
doc on its `##` headings (a natural semantic unit for reference material), then
packs paragraphs into overlapping windows so a fact that straddles a boundary is
still recoverable. Every chunk carries its source file and heading so an answer
can cite exactly where a claim came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

CHUNK_CHARS = 900        # target window size
OVERLAP_CHARS = 150      # carry-over so boundary facts survive


@dataclass
class Chunk:
    id: str
    text: str
    source: str          # file name, e.g. "ssrf.md"
    heading: str         # nearest ## heading, e.g. "How to fix it"

    def citation(self) -> str:
        return f"{self.source} › {self.heading}" if self.heading else self.source

    def to_dict(self) -> dict:
        return asdict(self)


def _sections(md: str) -> list[tuple[str, str]]:
    """Split a markdown doc into (heading, body) sections on '##' headings.
    Text before the first '##' is attributed to the '#' title if present."""
    lines = md.splitlines()
    sections: list[tuple[str, list[str]]] = []
    title = ""
    current_heading = ""
    buf: list[str] = []
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            current_heading = title
            continue
        if line.startswith("## "):
            if buf:
                sections.append((current_heading, buf))
            current_heading = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections.append((current_heading, buf))
    return [(h, "\n".join(b).strip()) for h, b in sections if "\n".join(b).strip()]


def _window(text: str) -> list[str]:
    """Pack a section's text into overlapping char windows, splitting on
    paragraph boundaries where possible so chunks stay readable."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    cur = ""
    for p in paras:
        if cur and len(cur) + len(p) + 2 > CHUNK_CHARS:
            chunks.append(cur.strip())
            # start next window with an overlap tail of the previous one
            cur = (cur[-OVERLAP_CHARS:] + "\n\n" + p) if OVERLAP_CHARS else p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def load_chunks(corpus_dir: str | Path) -> list[Chunk]:
    corpus = Path(corpus_dir)
    out: list[Chunk] = []
    for md_path in sorted(corpus.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        for heading, body in _sections(text):
            for i, piece in enumerate(_window(body)):
                cid = f"{md_path.name}::{heading}::{i}"
                out.append(Chunk(id=cid, text=piece, source=md_path.name, heading=heading))
    return out
