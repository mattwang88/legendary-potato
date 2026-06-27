"""CLI: python -m legendary_potato "query" [--docs DIR] [-k N] [--color auto|always|never]"""
from __future__ import annotations

import argparse
import re
import sys

from .search import citation, search

_HL, _RST = "\033[30;43m", "\033[0m"   # black on yellow


def _highlighter(query: str, enabled: bool):
    terms = [re.escape(t) for t in re.findall(r"\w+", query) if len(t) >= 2]
    if not enabled or not terms:
        return lambda s: s
    pat = re.compile("|".join(terms), re.IGNORECASE)
    return lambda s: pat.sub(lambda m: f"{_HL}{m.group(0)}{_RST}", s)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="legendary_potato",
        description="Local hybrid search (vector + BM25) over legal PDFs.",
    )
    ap.add_argument("query", help="search query")
    ap.add_argument("--docs", default="data", help="folder of PDFs (default: data)")
    ap.add_argument("-k", "--top-k", type=int, default=5, help="number of results (default: 5)")
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                    help="highlight query terms (default: auto — on when printing to a terminal)")
    ap.add_argument("--max-lines", type=int, default=18,
                    help="max lines of context shown per result (default: 18)")
    args = ap.parse_args()

    results, n_nodes = search(args.query, docs_dir=args.docs, top_k=args.top_k)

    colorize = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())
    highlight = _highlighter(args.query, colorize)

    print(f'\nQuery: "{args.query}"   ·   showing {len(results)} of {n_nodes} chunks\n')
    if not results:
        print("  (no matches)\n")
        return
    for rank, hit in enumerate(results, start=1):
        score = hit.score if hit.score is not None else 0.0
        print(f"[{rank}]  {citation(hit.node)}      score {score:.3f}")
        start = hit.node.metadata.get("line", 1)
        lines = hit.node.get_content().splitlines()
        for offset, ln in enumerate(lines[:args.max_lines]):
            print(f"   {start + offset:>5} │ {highlight(ln)}")
        if len(lines) > args.max_lines:
            print(f"         │ … ({len(lines) - args.max_lines} more lines)")
        print()


if __name__ == "__main__":
    main()
