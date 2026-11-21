"""Режим обменного датасета (`EXCHANGE_DATASET`, ветка test_memes).

Корпус и промпт другой команды (русские мемы): индекс BM25 с ru-лемматизацией
из `benchmark.exchange.run_exchange`, запрос без перевода, объяснение с
промптом под домен мемов. Штатный режим (корпус модов) не затрагивается.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.exchange.run_exchange import REFUSAL, SYSTEM, build, lemmatize_ru, parse_doc

from .explain import build_user_message, is_refusal
from .llm import LLM


def open_engine(path: str):
    docs = [parse_doc(d) for d in json.loads(Path(path).read_text(encoding="utf-8"))["documents"]]
    for d in docs:
        d["slug"] = d["id"]
        d["url"] = ""  # у мемов нет страницы Modrinth
    index = build(docs, lemmatize_ru)
    by_id = {d["id"]: d for d in docs}

    class Engine:
        def search(self, query: str, k: int = 5) -> list[tuple[dict[str, Any], float]]:
            return [(by_id[h.doc_id], h.score) for h in index.search(query, k)]

    return Engine()


def explain_exchange(llm: LLM | None, query: str, docs: list[dict[str, Any]]) -> str | None:
    if llm is None or not docs:
        return None
    text = llm.complete(SYSTEM, build_user_message(query, docs), max_tokens=450, temperature=0.2)
    return REFUSAL if is_refusal(text) else text