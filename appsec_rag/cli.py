"""
CLI: build the index, then ask questions.

    python -m appsec_rag build
    python -m appsec_rag ask "how do I fix an SSRF?"
    python -m appsec_rag ask "what stops an agent tool from reading /etc/passwd?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .answer import answer
from .store import build_index

DEFAULT_CORPUS = str(Path(__file__).resolve().parent.parent / "corpus")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="appsec-rag",
                                description="RAG assistant for application security, with cited answers.")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="ingest the corpus and build the vector index")
    b.add_argument("--corpus", default=DEFAULT_CORPUS)

    a = sub.add_parser("ask", help="ask a question, get a cited answer")
    a.add_argument("question")
    a.add_argument("-k", type=int, default=4, help="how many chunks to retrieve")

    args = p.parse_args(argv)

    if args.cmd == "build":
        n = build_index(args.corpus)
        print(f"Indexed {n} chunks from {args.corpus}")
        return 0

    if args.cmd == "ask":
        try:
            ans = answer(args.question, k=args.k)
        except Exception as e:
            print(f"error: {e}\n(did you run `python -m appsec_rag build` first?)",
                  file=sys.stderr)
            return 1
        print(ans.render())
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
