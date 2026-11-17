"""Метрики benchmark (методичка, раздел 1.5; презентация «Занятие 3», слайды 33–34, 42).

Поиск (только обычные вопросы):
    Recall@k = |R ∩ Top_k| / |R|            — доля нужных документов среди первых k
    RR@k     = 1 / rank первого релевантного — 0, если в первых k его нет
    MRR@k    = среднее RR@k по вопросам

Ответы:
    Accuracy               — доля полностью правильных ответов на обычные вопросы
    Correct Rejection Rate — доля корректных отказов на вопросах-ловушках
"""

from __future__ import annotations

from typing import Iterable, Sequence


def recall_at_k(relevant: Iterable[str], ranked: Sequence[str], k: int) -> float:
    rel = set(relevant)
    if not rel:
        raise ValueError("у вопроса нет релевантных документов: Recall не определён")
    return len(rel & set(ranked[:k])) / len(rel)


def reciprocal_rank(relevant: Iterable[str], ranked: Sequence[str], k: int) -> float:
    rel = set(relevant)
    for rank, doc in enumerate(ranked[:k], 1):
        if doc in rel:
            return 1 / rank
    return 0.0


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def share(flags: Iterable[bool]) -> float | None:
    flags = list(flags)
    return sum(flags) / len(flags) if flags else None
