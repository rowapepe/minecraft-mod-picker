"""Обменный прогон КТ2: dataset.json другой команды (русский корпус мемов).

Запуск из каталога `code/`:

    backend/.venv/bin/python benchmark/exchange/run_exchange.py search
    env -u NO_PROXY -u no_proxy -u AG_LS_PROXY backend/.venv/bin/python benchmark/exchange/run_exchange.py answers

Отличия от штатного `benchmark.run` (корпус и запросы русские):
- лемматизация simplemma ru для документов и запросов (наш Preprocessor,
  язык — параметр); перевод не нужен, запросы уже русские;
- параметры поиска те же: k1 = 1.2, b = 0.75, k = 5; варианты en/none — для сравнения;
- объяснение: backend.llm и функции explain (format_documents, build_user_message,
  is_refusal), системный промпт и текст отказа адаптированы под домен мемов;
- оценки verdict: correct / partial / refused (partial — «~ частично» бланка,
  в штатной схеме benchmark его нет); Accuracy считается по correct.

Результаты: results/search-results.json, results/answers-raw.json (ответы LLM),
results/answers.jsonl (ответы с ручными оценками по expected_answer).
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
sys.path.insert(0, str(CODE))

from search import BM25Index, Preprocessor, lemmatize_en, no_lemmatize
from benchmark.metrics import mean, recall_at_k, reciprocal_rank, share

DATASET = HERE / "dataset.json"
OUT = HERE / "results"
K = 5


@lru_cache(maxsize=None)
def lemmatize_ru(word: str) -> str:
    import simplemma
    return simplemma.lemmatize(word, lang="ru").lower()


def parse_doc(d: dict) -> dict:
    fields = {}
    for line in d["text"].splitlines():
        for key in ("Название:", "Описание:", "История:", "Теги:"):
            if line.startswith(key):
                fields[key[:-1]] = line[len(key):].strip()
    return {
        "id": d["id"],
        "title": fields.get("Название", d["id"]),
        "description": fields.get("Описание", ""),
        "body": d["text"],
        "categories": [t.strip() for t in fields.get("Теги", "").split(",") if t.strip()],
        "text": d["text"],
    }


def load():
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    docs = [parse_doc(d) for d in data["documents"]]
    questions = [
        {
            "id": q["id"],
            "type": "trap" if q["trap"] else "normal",
            "query": q["text"],
            "relevant": q["relevant_ids"] or [],
            "reference": q["expected_answer"],
        }
        for q in data["questions"]
    ]
    return docs, questions


def build(docs, lemmatizer):
    pre = Preprocessor(lemmatizer, frozenset())
    return BM25Index.build(((d["id"], d["text"]) for d in docs), preprocess=pre, k1=1.2, b=0.75)


def stage_search():
    OUT.mkdir(exist_ok=True)
    docs, questions = load()
    titles = {d["id"]: d["title"] for d in docs}
    variants = [("ru-лемматизация (базовая)", lemmatize_ru), ("en-лемматизация (как есть)", lemmatize_en), ("без лемматизации", no_lemmatize)]
    report = {}
    for name, lem in variants:
        index = build(docs, lem)
        hits = {q["id"]: index.search(q["query"], K) for q in questions}
        ranked = {qid: [h.doc_id for h in hs] for qid, hs in hits.items()}
        per = {
            q["id"]: {"recall": recall_at_k(q["relevant"], ranked[q["id"]], K), "rr": reciprocal_rank(q["relevant"], ranked[q["id"]], K)}
            for q in questions if q["type"] == "normal"
        }
        report[name] = {"recall": mean(p["recall"] for p in per.values()), "mrr": mean(p["rr"] for p in per.values()), "per": per}
        if name.startswith("ru"):
            details = {
                q["id"]: {
                    "type": q["type"], "query": q["query"], "relevant": q["relevant"],
                    "results": [
                        {"rank": r, "doc": h.doc_id, "title": titles[h.doc_id], "score": round(h.score, 3), "relevant": h.doc_id in q["relevant"]}
                        for r, h in enumerate(hits[q["id"]], 1)
                    ],
                }
                for q in questions
            }
    (OUT / "search-results.json").write_text(json.dumps({"k": K, "variants": {n: {"recall": v["recall"], "mrr": v["mrr"]} for n, v in report.items()}, "per_question": report["ru-лемматизация (базовая)"]["per"], "questions": details}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, v in report.items():
        print(f"{name}: Recall@{K}={v['recall']:.3f} MRR@{K}={v['mrr']:.3f}")
    for qid, p in report["ru-лемматизация (базовая)"]["per"].items():
        print(qid, f"recall={p['recall']:.3f} rr={p['rr']:.3f}", [f"{r['rank']}:{r['doc']}{'*' if r['relevant'] else ''}" for r in details[qid]["results"]])
    for q in questions:
        if q["type"] == "trap":
            print(q["id"], [f"{r['rank']}:{r['doc']}" for r in details[q["id"]]["results"]])


SYSTEM = """Ты помогаешь пользователю подобрать мемы по их описаниям.
Тебе дают запрос пользователя и список найденных документов с описаниями мемов.

Правила:
- Отвечай только по описаниям из списка. Не используй другие знания о мемах и ничего не придумывай.
- Называй только мемы из списка, точно как в поле «Название». Другие мемы не упоминай и не советуй.
- Объясни, какие мемы из списка подходят под запрос и чем именно; неподходящие пропусти.
- Не приписывай мему смысла или свойств, которых нет в его описании. Если мем подходит лишь частично, так и скажи.
- Пиши по-русски, кратко: не больше 120 слов, обычным текстом, без заголовков, ссылок, таблиц, эмодзи и номеров из списка.
- Если ни в одном описании нет того, что просит пользователь, ответь ровно одним словом: NO_ANSWER"""

REFUSAL = "В описаниях найденных документов нет ответа на этот вопрос."


def stage_answers():
    from backend.config import Settings
    from backend.llm import make_llm
    from backend.explain import build_user_message, is_refusal

    docs, questions = load()
    by_id = {d["id"]: d for d in docs}
    details = json.loads((OUT / "search-results.json").read_text(encoding="utf-8"))["questions"]
    llm = make_llm(Settings.load())
    if llm is None:
        raise SystemExit("нет LLM_API_KEY")
    raw = []
    for q in questions:
        found = [by_id[r["doc"]] for r in details[q["id"]]["results"]]
        if not found:
            answer = None
        else:
            text = llm.complete(SYSTEM, build_user_message(q["query"], found), max_tokens=450, temperature=0.2)
            answer = REFUSAL if is_refusal(text) else text
        raw.append({"id": q["id"], "type": q["type"], "query": q["query"], "found": [d["id"] for d in found], "answer": answer, "reference": q["reference"]})
        print(q["id"], "->", (answer or "пусто").replace("\n", " ")[:200])
    (OUT / "answers-raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    {"search": stage_search, "answers": stage_answers}[sys.argv[1]]()