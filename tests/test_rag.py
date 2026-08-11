"""End-to-end tests for the RAG pipeline: chunking, retrieval relevance,
citations, and the honesty guards (off-topic -> no answer, no key -> extractive)."""

import os
from pathlib import Path

import pytest

from appsec_rag import load_chunks, build_index, retrieve, answer

CORPUS = str(Path(__file__).resolve().parent.parent / "corpus")


# ---------- chunking (no deps beyond stdlib) ----------
def test_chunking_produces_cited_chunks():
    chunks = load_chunks(CORPUS)
    assert len(chunks) > 5
    for c in chunks:
        assert c.text.strip()
        assert c.source.endswith(".md")
        assert c.citation()          # "file.md › heading"
    # chunks stay within a sane size (chunking actually happened)
    assert max(len(c.text) for c in chunks) < 1500


# ---------- build the index once for the retrieval tests ----------
@pytest.fixture(scope="module", autouse=True)
def _index():
    n = build_index(CORPUS)
    assert n > 5
    yield


@pytest.mark.parametrize("question,expected_source", [
    ("how do I fix an SSRF", "ssrf.md"),
    ("stop a tenant from upgrading their own plan", "access-control.md"),
    ("prevent sql injection in my queries", "injection.md"),
    ("a leaked stripe key was committed to git", "secrets-and-crypto.md"),
    ("what keeps an agent tool from reading files outside the workspace", "mcp-and-agent-security.md"),
])
def test_retrieval_finds_the_right_doc(question, expected_source):
    results = retrieve(question, k=4)
    assert results, f"no results for {question!r}"
    # the right doc should surface in the top-k retrieved set
    sources = [r.source for r in results]
    assert expected_source in sources, f"{question!r} -> {sources}"


def test_scores_are_similarities_descending():
    results = retrieve("how do I fix an SSRF", k=4)
    scores = [r.score for r in results]
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_offtopic_question_returns_no_answer():
    # Nothing in an appsec corpus should clear the relevance floor for this.
    results = retrieve("what is the best recipe for banana bread", k=4)
    ans = answer("what is the best recipe for banana bread")
    assert results == [] or "don't have" in ans.text.lower()


def test_answer_is_grounded_and_cited():
    ans = answer("how do I fix an SSRF")
    assert ans.citations, "an answer from sources must carry citations"
    assert any("ssrf" in c.lower() for c in ans.citations)


def test_no_key_falls_back_to_extractive(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ans = answer("how do I fix an SSRF")
    assert ans.used_llm is False
    assert ans.citations           # still cites its source
    assert ans.text.strip()


# ---------- red-team regression: query size cap ----------
def test_huge_query_is_capped_and_fast():
    import time
    t = time.perf_counter()
    results = retrieve("ssrf " * 100000, k=3)   # capped before embedding
    assert time.perf_counter() - t < 3.0, "huge query was not capped (resource risk)"
    assert isinstance(results, list)


# ---------- red-team regressions (line-by-line pass) ----------
def test_oversized_paragraph_is_split():
    # a single unbroken paragraph larger than the window must not become one giant chunk.
    # (chunks may run to CHUNK_CHARS + OVERLAP_CHARS because each carries an overlap tail.)
    from appsec_rag.ingest import _window, CHUNK_CHARS, OVERLAP_CHARS
    chunks = _window("word " * 1000)            # ~5000 chars, no blank lines
    assert len(chunks) > 1                       # it actually got split
    assert max(len(c) for c in chunks) <= CHUNK_CHARS + OVERLAP_CHARS + 2


def test_empty_embed_batch_does_not_crash():
    from appsec_rag.embed import embed
    assert embed([]) == []


def test_retrieve_with_nonpositive_k_does_not_crash():
    # k <= 0 must be coerced, not passed through to Chroma (which raises)
    assert isinstance(retrieve("how do I fix an SSRF", k=0), list)
