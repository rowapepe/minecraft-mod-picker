"""Поиск модов по корпусу Modrinth собственной реализацией BM25.

Интерфейс для бэкенда (GAP-07, модуль вызывается как библиотека):

    from search import ModSearch
    engine = ModSearch.open()              # корпус code/data/mods.jsonl
    for doc, hit in engine.search("automatic farm without lag", k=5):
        doc["title"], doc["url"], hit.score

Запрос должен быть уже на английском: перевод русского запроса (GAP-01)
выполняется до вызова поиска (RULE-SRCH-02).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from .bm25 import B, K1, TOP_K, BM25Index, Hit
from .preprocess import ENGLISH_STOPWORDS, Preprocessor, lemmatize_en, no_lemmatize, tokenize

__all__ = [
    "B", "K1", "TOP_K", "BM25Index", "Hit", "ModSearch",
    "ENGLISH_STOPWORDS", "Preprocessor", "lemmatize_en", "no_lemmatize", "tokenize",
    "load_corpus", "doc_text",
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CORPUS_PATH = DATA_DIR / "mods.jsonl"
INDEX_PATH = DATA_DIR / "index.json"


def load_corpus(path: Path = CORPUS_PATH) -> Iterator[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def doc_text(doc: dict[str, Any]) -> str:
    """Индексируемый текст документа: название, короткое и полное описание (RULE-DATA-03)."""
    return "\n".join(doc.get(f) or "" for f in ("title", "description", "body"))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ModSearch:
    """Корпус + индекс BM25: возвращает документы корпуса с баллами."""

    def __init__(self, docs: dict[str, dict[str, Any]], index: BM25Index):
        self.docs = docs
        self.index = index

    @classmethod
    def build(
        cls,
        corpus_path: Path = CORPUS_PATH,
        preprocess: Preprocessor | None = None,
        k1: float = K1,
        b: float = B,
    ) -> "ModSearch":
        docs = {d["id"]: d for d in load_corpus(corpus_path)}
        index = BM25Index.build(
            ((i, doc_text(d)) for i, d in docs.items()), preprocess=preprocess, k1=k1, b=b
        )
        index.meta = {"corpus": Path(corpus_path).name, "corpus_sha256": file_sha256(corpus_path)}
        return cls(docs, index)

    @classmethod
    def open(cls, corpus_path: Path = CORPUS_PATH, index_path: Path | None = INDEX_PATH) -> "ModSearch":
        """Загружает индекс из файла, если он построен по этому же корпусу; иначе строит заново."""
        if index_path and Path(index_path).is_file():
            try:
                index = BM25Index.load(index_path)
            except ValueError:
                index = None
            if index and index.meta.get("corpus_sha256") == file_sha256(corpus_path):
                return cls({d["id"]: d for d in load_corpus(corpus_path)}, index)
        engine = cls.build(corpus_path)
        if index_path:
            engine.index.save(Path(index_path))
        return engine

    def search(self, query: str, k: int = TOP_K) -> list[tuple[dict[str, Any], Hit]]:
        return [(self.docs[h.doc_id], h) for h in self.index.search(query, k)]
