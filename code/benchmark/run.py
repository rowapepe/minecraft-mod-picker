"""Прогон benchmark (GAP-18, RULE-QA-01…05). Запуск из каталога `code/`:

    python -m benchmark.run

1. Корпус benchmark — 30 документов `corpus.jsonl` (D01…D30), вопросы — `questions.json`.
2. Глубина k фиксирована заранее (k = 5, `questions.json`), MRR считается по тем же k.
3. Настройки поиска сравниваются по одной за раз относительно базовой (слайд 35):
   тот же корпус, те же вопросы, та же глубина.
4. Дополнительно — те же вопросы на полном снимке из 1000 модов: Recall там
   оценка снизу, потому что релевантные документы размечены только среди D01…D30.
5. Accuracy и Correct Rejection Rate считаются, если есть `answers.jsonl`
   с оценками ответов LLM (`{"id", "answer", "verdict": correct|incorrect|refused}`).

Результаты: `results/report.md` (сводка) и `results/search-results.json`
(выдача по каждому из 15 вопросов). Сводку переносят в
`docs/Service/verification.md` (RULE-QA-05).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from search import B, ENGLISH_STOPWORDS, K1, BM25Index, ModSearch, Preprocessor, doc_text, lemmatize_en, no_lemmatize

from .metrics import mean, recall_at_k, reciprocal_rank, share

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus.jsonl"
QUESTIONS = HERE / "questions.json"
ANSWERS = HERE / "answers.jsonl"
RESULTS = HERE / "results"


@dataclass(frozen=True)
class Config:
    name: str
    k1: float = K1
    b: float = B
    lemmatize: bool = True
    stopwords: bool = False

    def build(self, docs: list[dict[str, Any]]) -> BM25Index:
        pre = Preprocessor(
            lemmatize_en if self.lemmatize else no_lemmatize,
            ENGLISH_STOPWORDS if self.stopwords else frozenset(),
        )
        return BM25Index.build(((d["bench_id"], doc_text(d)) for d in docs), preprocess=pre, k1=self.k1, b=self.b)


BASELINE = Config("базовая: лемматизация, k1 = 1.2, b = 0.75")
VARIANTS = [
    BASELINE,
    Config("k1 = 1.5", k1=1.5),
    Config("k1 = 2.0", k1=2.0),
    Config("b = 0.5", b=0.5),
    Config("b = 1.0", b=1.0),
    Config("без лемматизации", lemmatize=False),
    Config("удаление стоп-слов", stopwords=True),
]


def load() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    docs = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    return docs, data


def evaluate(ranked: dict[str, list[str]], questions: list[dict[str, Any]], k: int) -> dict[str, Any]:
    normal = [q for q in questions if q["type"] == "normal"]
    per = {
        q["id"]: {
            "recall": recall_at_k(q["relevant"], ranked[q["id"]], k),
            "rr": reciprocal_rank(q["relevant"], ranked[q["id"]], k),
        }
        for q in normal
    }
    return {
        "recall": mean(p["recall"] for p in per.values()),
        "mrr": mean(p["rr"] for p in per.values()),
        "per_question": per,
    }


def answer_metrics(questions: list[dict[str, Any]]) -> dict[str, Any]:
    if not ANSWERS.is_file():
        return {"accuracy": None, "crr": None, "note": "нет answers.jsonl: ответы LLM ещё не получены"}
    verdicts = {}
    for line in ANSWERS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            a = json.loads(line)
            verdicts[a["id"]] = a["verdict"]
    normal = [q["id"] for q in questions if q["type"] == "normal"]
    traps = [q["id"] for q in questions if q["type"] == "trap"]
    return {
        "accuracy": share(verdicts.get(i) == "correct" for i in normal),
        "crr": share(verdicts.get(i) == "refused" for i in traps),
        "answered": len(verdicts),
    }


def main() -> None:
    docs, data = load()
    k, questions = data["k"], data["questions"]
    titles = {d["bench_id"]: d["title"] for d in docs}

    runs = []
    details: dict[str, Any] = {}
    for cfg in VARIANTS:
        index = cfg.build(docs)
        hits = {q["id"]: index.search(q["query"], k) for q in questions}
        ranked = {qid: [h.doc_id for h in hs] for qid, hs in hits.items()}
        runs.append((cfg, evaluate(ranked, questions, k)))
        if cfg is BASELINE:
            details = {
                q["id"]: {
                    "type": q["type"],
                    "query": q["query"],
                    "relevant": q["relevant"],
                    "results": [
                        {
                            "rank": r,
                            "doc": h.doc_id,
                            "title": titles[h.doc_id],
                            "score": round(h.score, 3),
                            "relevant": h.doc_id in q["relevant"],
                            "contributions": {w: round(v, 3) for w, v in sorted(h.contributions.items(), key=lambda kv: -kv[1])},
                        }
                        for r, h in enumerate(hits[q["id"]], 1)
                    ],
                }
                for q in questions
            }

    # те же вопросы на полном снимке: D-номера переводятся в id Modrinth
    to_bench = {d["id"]: d["bench_id"] for d in docs}
    full = ModSearch.open()
    full_ranked = {
        q["id"]: [to_bench.get(doc["id"], doc["slug"]) for doc, _ in full.search(q["query"], k)]
        for q in questions
    }
    full_eval = evaluate(full_ranked, questions, k)
    answers = answer_metrics(questions)

    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (RESULTS / "search-results.json").write_text(
        json.dumps({"run_at": stamp, "config": BASELINE.name, "k": k, "questions": details}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = render(stamp, k, questions, runs, details, full_eval, full_ranked, answers)
    (RESULTS / "report.md").write_text(report, encoding="utf-8")
    print(report)


def fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def render(stamp, k, questions, runs, details, full_eval, full_ranked, answers) -> str:
    base = runs[0][1]
    n_normal = sum(q["type"] == "normal" for q in questions)
    n_trap = len(questions) - n_normal
    lines = [
        f"# Benchmark поиска — {stamp}",
        "",
        f"Корпус: 30 документов (`corpus.jsonl`); вопросы: {n_normal} обычных и {n_trap} ловушек; k = {k}.",
        "",
        "## Метрики по настройкам (одна настройка за раз)",
        "",
        f"| Настройка | Recall@{k} | MRR@{k} |",
        "| --------- | -------- | ----- |",
    ]
    for cfg, ev in runs:
        lines.append(f"| {cfg.name} | {fmt(ev['recall'])} | {fmt(ev['mrr'])} |")
    lines += [
        f"| полный снимок, 1000 модов (базовая; Recall — оценка снизу) | {fmt(full_eval['recall'])} | {fmt(full_eval['mrr'])} |",
        "",
        "## Ответы",
        "",
        f"| Accuracy (из {n_normal}) | Correct Rejection Rate (из {n_trap}) |",
        "| -------- | ---------------------- |",
        f"| {fmt(answers['accuracy'])} | {fmt(answers['crr'])} |",
        "",
    ]
    if answers.get("note"):
        lines += [f"_{answers['note']}._", ""]
    lines += [
        "## Выдача базовой настройки по вопросам",
        "",
        f"| Вопрос | Релевантные | Первые {k} (★ — релевантный) | Recall@{k} | RR | Полный снимок: первые {k} |",
        "| ------ | ----------- | ---------------------------- | -------- | -- | ------------------------- |",
    ]
    for q in questions:
        d = details[q["id"]]
        got = " ".join(f"{r['doc']}★" if r["relevant"] else r["doc"] for r in d["results"]) or "пусто"
        full = " ".join(x if not x.startswith("D") else f"{x}★" if x in q["relevant"] else x for x in full_ranked[q["id"]])
        if q["type"] == "normal":
            pq = base["per_question"][q["id"]]
            lines.append(f"| {q['id']} | {' '.join(q['relevant'])} | {got} | {fmt(pq['recall'])} | {fmt(pq['rr'])} | {full} |")
        else:
            lines.append(f"| {q['id']} (ловушка) | — | {got} | — | — | {full} |")
    lines += ["", "В столбце полного снимка документы вне D01…D30 показаны slug Modrinth.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
