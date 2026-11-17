"""Командная строка поиска. Запуск из каталога `code/`:

    python -m search build                       # построить code/data/index.json
    python -m search "automatic farm without lag" # первые 5 модов с баллами
    python -m search -k 10 --explain "storage for many items"
"""

from __future__ import annotations

import argparse
import sys
import time

from . import INDEX_PATH, TOP_K, ModSearch


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m search", description="BM25-поиск по корпусу модов")
    parser.add_argument("query", nargs="+", help="текст запроса на английском или слово build")
    parser.add_argument("-k", type=int, default=TOP_K, help="сколько документов вернуть")
    parser.add_argument("--explain", action="store_true", help="показать вклад каждого слова")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    if args.query == ["build"]:
        engine = ModSearch.build()
        engine.index.save(INDEX_PATH)
        idx = engine.index
        print(
            f"индекс: {idx.N} документов, {len(idx.index)} термов, avgdl = {idx.avgdl:.1f}, "
            f"{time.perf_counter() - started:.1f} с → {INDEX_PATH}"
        )
        return

    engine = ModSearch.open()
    query = " ".join(args.query)
    results = engine.search(query, args.k)
    if not results:
        print("ничего не найдено")
    for rank, (doc, hit) in enumerate(results, 1):
        print(f"{rank}. {hit.score:6.3f}  {doc['title']}  {doc['url']}")
        if args.explain:
            parts = sorted(hit.contributions.items(), key=lambda kv: -kv[1])
            print("          " + ", ".join(f"{w} {v:.3f}" for w, v in parts))


if __name__ == "__main__":
    sys.exit(main())
