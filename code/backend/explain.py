"""Объяснение LLM по найденным модам или отказ (`RULE-ANS-01…05`, `GAP-19`, `D-19`).

LLM получает исходный запрос игрока и только документы из выдачи. Если в их
описаниях нет ответа, модель возвращает служебную метку, и бэкенд отдаёт
фиксированный текст отказа — так отказ легко распознать и в интерфейсе,
и при подсчёте Correct Rejection Rate.
"""

from __future__ import annotations

from typing import Any

from .llm import LLM

REFUSAL = "В описаниях найденных модов нет ответа на этот вопрос."
NO_ANSWER_MARK = "NO_ANSWER"
BODY_CHARS = 700  # начало полного описания: хватает для смысла, промпт остаётся коротким
MAX_TOKENS = 450  # ~150 слов по-русски (RULE-ANS-05) с запасом

SYSTEM_PROMPT = f"""Ты помогаешь игроку Minecraft подобрать моды.
Тебе дают запрос игрока и список найденных модов с описаниями с Modrinth.

Правила:
- Отвечай только по описаниям из списка. Не используй другие знания о модах и ничего не придумывай.
- Называй только моды из списка, точно как в поле «Название». Другие моды не упоминай и не советуй.
- Объясни, какие моды из списка подходят под запрос и чем именно; неподходящие пропусти.
- Не приписывай моду возможностей, которых нет в его описании. Если мод подходит лишь частично, так и скажи.
- Пиши по-русски, кратко: не больше 120 слов, обычным текстом, без заголовков, ссылок, таблиц, эмодзи и номеров из списка.
- Если ни в одном описании нет того, что просит игрок, ответь ровно одним словом: {NO_ANSWER_MARK}"""


def format_documents(docs: list[dict[str, Any]]) -> str:
    """Найденные моды для промпта: название, категории, описания (RULE-ANS-01)."""
    parts = []
    for n, doc in enumerate(docs, 1):
        body = " ".join((doc.get("body") or "").split())
        if len(body) > BODY_CHARS:
            body = body[:BODY_CHARS].rsplit(" ", 1)[0] + " …"
        categories = ", ".join(doc.get("categories") or []) or "—"
        parts.append(
            f"{n}. Название: {doc['title']}\n"
            f"Категории: {categories}\n"
            f"Кратко: {doc.get('description') or '—'}\n"
            f"Подробно: {body or '—'}"
        )
    return "\n\n".join(parts)


def build_user_message(query: str, docs: list[dict[str, Any]]) -> str:
    return f"Запрос игрока: {query}\n\nНайденные моды:\n\n{format_documents(docs)}"


def is_refusal(text: str) -> bool:
    return NO_ANSWER_MARK in text.upper().replace(" ", "_")


def explain(llm: LLM | None, query: str, docs: list[dict[str, Any]]) -> str | None:
    """Объяснение или отказ; None — если объяснять нечего или LLM не настроена.

    Ошибку LLM передаёт вызывающему: тот решает, что показать (RULE-ANS-04).
    """
    if llm is None or not docs:
        return None
    text = llm.complete(SYSTEM_PROMPT, build_user_message(query, docs), max_tokens=MAX_TOKENS, temperature=0.2)
    return REFUSAL if is_refusal(text) else text
