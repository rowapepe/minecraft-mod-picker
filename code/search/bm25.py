"""Собственная реализация поискового индекса BM25 (RULE-SRCH-01).

Формула — методические указания, раздел 1.3; код повторяет презентацию
«Занятие 3», слайды 25–28:

    IDF(t)     = ln(1 + (N − df + 0.5) / (df + 0.5))
    BM25(q, d) = Σ_{t ∈ q} IDF(t) · tf·(k1 + 1) / (tf + k1·(1 − b + b·|d| / avgdl))

- индекс — обратный: терм → {id документа: tf} (слайд 25, методичка 1.4);
- повторы слов в запросе считаются один раз: `dict.fromkeys` (слайд 26);
- документы сортируются по убыванию балла, при равенстве — по id (слайды 24, 28,
  RULE-SRCH-03); возвращаются первые `k` (RULE-SRCH-04);
- в баллы попадают только документы хотя бы с одним совпадением, а IDF такого
  вида всегда положителен, поэтому документы с нулевой оценкой в выдачу не
  попадают (RULE-SRCH-05).

Готовые поисковые индексы и движки не используются.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import log
from pathlib import Path
from typing import Any, Iterable

from .preprocess import Preprocessor

K1 = 1.2  # GAP-03: начальное значение, подбирается по benchmark
B = 0.75  # RULE-SRCH-06
TOP_K = 5  # RULE-SRCH-04

INDEX_FORMAT = 1


@dataclass
class Hit:
    """Документ в выдаче: id, балл BM25 и вклад каждого слова запроса (слайд 5)."""

    doc_id: str
    score: float
    contributions: dict[str, float] = field(default_factory=dict)


class BM25Index:
    def __init__(self, preprocess: Preprocessor | None = None, k1: float = K1, b: float = B):
        self.preprocess = preprocess or Preprocessor()
        self.k1 = k1
        self.b = b
        self.index: dict[str, dict[str, int]] = defaultdict(dict)
        self.lengths: dict[str, int] = {}
        self.meta: dict[str, Any] = {}  # сведения об источнике, сохраняются в файл индекса

    # ------------------------------------------------------------ построение

    def add(self, doc_id: str, text: str) -> None:
        """Слайд 25: длина документа и частоты его термов в обратный индекс."""
        if doc_id in self.lengths:
            raise ValueError(f"документ {doc_id} уже есть в индексе")
        words = self.preprocess(text)
        self.lengths[doc_id] = len(words)
        for word, tf in Counter(words).items():
            self.index[word][doc_id] = tf

    @classmethod
    def build(cls, docs: Iterable[tuple[str, str]], **kwargs: Any) -> "BM25Index":
        idx = cls(**kwargs)
        for doc_id, text in docs:
            idx.add(doc_id, text)
        return idx

    # ----------------------------------------------------------- статистика

    @property
    def N(self) -> int:  # noqa: N802 — обозначение из методички
        return len(self.lengths)

    @property
    def avgdl(self) -> float:
        return sum(self.lengths.values()) / self.N if self.N else 0.0

    def idf(self, word: str) -> float:
        """Слайд 13: редкое слово даёт больше информации."""
        df = len(self.index.get(word, {}))
        return log(1 + (self.N - df + 0.5) / (df + 0.5))

    # ------------------------------------------------------------------ поиск

    def score(self, query: str) -> dict[str, Hit]:
        """Слайды 26–27: баллы всех документов хотя бы с одним совпадением."""
        hits: dict[str, Hit] = {}
        if not self.N:
            return hits
        avgdl = self.avgdl
        for word in dict.fromkeys(self.preprocess(query)):
            postings = self.index.get(word)
            if not postings:  # пустой список → баллы не меняются
                continue
            idf = self.idf(word)
            for doc, tf in postings.items():
                norm = self.k1 * (1 - self.b + self.b * self.lengths[doc] / avgdl)
                part = idf * tf * (self.k1 + 1) / (tf + norm)
                hit = hits.setdefault(doc, Hit(doc, 0.0))
                hit.score += part  # оценки накапливаются, а не заменяют друг друга
                hit.contributions[word] = part
        return hits

    def search(self, query: str, k: int = TOP_K) -> list[Hit]:
        """Слайд 28: по убыванию балла, при равенстве по id, первые k."""
        hits = self.score(query)
        ranked = sorted(hits.values(), key=lambda h: (-h.score, h.doc_id))
        return [h for h in ranked[:k] if h.score > 0]

    # ------------------------------------------------------------ файл индекса

    def save(self, path: Path) -> None:
        data = {
            "format": INDEX_FORMAT,
            "preprocess": self.preprocess.name,
            "k1": self.k1,
            "b": self.b,
            "meta": self.meta,
            "lengths": self.lengths,
            "index": self.index,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def load(cls, path: Path, preprocess: Preprocessor | None = None) -> "BM25Index":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != INDEX_FORMAT:
            raise ValueError(f"неизвестный формат индекса: {data.get('format')}")
        idx = cls(preprocess=preprocess, k1=data["k1"], b=data["b"])
        if idx.preprocess.name != data["preprocess"]:
            raise ValueError(
                f"индекс построен с предобработкой {data['preprocess']}, "
                f"а запросы обрабатываются как {idx.preprocess.name}: перестройте индекс"
            )
        idx.meta = data.get("meta", {})
        idx.lengths = data["lengths"]
        idx.index = defaultdict(dict, data["index"])
        return idx
