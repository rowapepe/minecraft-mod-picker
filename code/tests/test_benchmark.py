"""Метрики по примерам презентации «Занятие 3» (слайды 33–34) и проверка набора benchmark (GAP-18)."""

import json
from pathlib import Path

import pytest

from benchmark.metrics import mean, recall_at_k, reciprocal_rank, share
from search import ENGLISH_STOPWORDS, Preprocessor

BENCH = Path(__file__).resolve().parents[1] / "benchmark"


# ------------------------------------------------------------------- метрики


def test_recall_at_3_lecture_example():
    # слайд 33: правильные A, D, F; поиск вернул B, A, D → 2 / 3
    assert recall_at_k(["A", "D", "F"], ["B", "A", "D"], 3) == pytest.approx(2 / 3)
    assert round(recall_at_k(["A", "D", "F"], ["B", "A", "D"], 3), 3) == 0.667


def test_mrr_lecture_example():
    # слайд 34: первый полезный на № 2 и на № 1 → (0,5 + 1) / 2 = 0,75
    rr1 = reciprocal_rank(["A", "D"], ["B", "A", "D"], 3)
    rr2 = reciprocal_rank(["C"], ["C", "B"], 3)
    assert (rr1, rr2) == (0.5, 1.0)
    assert mean([rr1, rr2]) == 0.75


def test_rr_is_zero_without_relevant_in_top_k():
    # слайд 34: нет полезного в top-k → RR@k = 0
    assert reciprocal_rank(["Z"], ["A", "B", "C", "Z"], 3) == 0.0


def test_recall_requires_relevant_documents():
    with pytest.raises(ValueError):
        recall_at_k([], ["A"], 5)


def test_share():
    assert share([True, False, True, True]) == 0.75
    assert share([]) is None


def test_stopwords_option():
    pre = Preprocessor(stopwords=ENGLISH_STOPWORDS)
    assert pre("I keep getting lost in the world, it is my house") == [
        "keep", "get", "lose", "world", "house"
    ]
    assert Preprocessor()("I is")[0] == "i"  # по умолчанию стоп-слова остаются


# ------------------------------------------------------------- набор данных


@pytest.fixture(scope="module")
def corpus():
    return [json.loads(line) for line in (BENCH / "corpus.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.fixture(scope="module")
def questions():
    return json.loads((BENCH / "questions.json").read_text(encoding="utf-8"))


def test_corpus_has_30_numbered_documents(corpus):
    # слайд 39: 30 документов D01 … D30
    assert [d["bench_id"] for d in corpus] == [f"D{i:02d}" for i in range(1, 31)]
    assert len({d["id"] for d in corpus}) == 30  # RULE-QA-04: связь с id Modrinth
    assert all(d["title"] and d["body"] for d in corpus)


def test_questions_composition(questions, corpus):
    qs = questions["questions"]
    ids = {d["bench_id"] for d in corpus}
    normal = [q for q in qs if q["type"] == "normal"]
    traps = [q for q in qs if q["type"] == "trap"]
    # слайд 39: 10 обычных и 5 ловушек; k согласовано заранее (слайд 42)
    assert (len(normal), len(traps)) == (10, 5)
    assert questions["k"] == 5
    assert len({q["id"] for q in qs}) == 15
    for q in normal:
        # RULE-QA-02 и слайд 40: не менее трёх релевантных документов и эталон
        assert len(q["relevant"]) >= 3, q["id"]
        assert set(q["relevant"]) <= ids, q["id"]
        assert q["reference"] and q["question"] and q["query"]
    for q in traps:
        assert q["relevant"] == [] and q["reference"]


def test_questions_cover_all_topics(questions, corpus):
    # RULE-QA-03: набор равномерно покрывает корпус — каждый документ релевантен хотя бы одному вопросу
    covered = {d for q in questions["questions"] for d in q["relevant"]}
    assert covered == {d["bench_id"] for d in corpus}
