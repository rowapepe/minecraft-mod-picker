"""Перевод запроса в английские ключевые слова до поиска (`GAP-01`, `RULE-SRCH-02`, `D-18`).

Корпус описаний модов на английском, поэтому русский запрос сначала
превращается в короткий набор английских слов, которые есть в описаниях.
"""

from __future__ import annotations

import re

from .llm import LLM, LLMError

CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)
NOT_KEYWORD = re.compile(r"[^a-z0-9' -]+")
LABEL = re.compile(r"^\s*(english\s+)?(search\s+)?keywords?\s*:\s*")
MAX_KEYWORDS = 16

SYSTEM_PROMPT = """You convert a Minecraft player's request into English search keywords.
The keywords are used for BM25 keyword search over English descriptions of Minecraft mods from Modrinth.

Rules:
- Reply with keywords only: 3 to 12 lowercase English words separated by spaces, on one line.
- Translate the meaning of the request; use words that mod descriptions are likely to contain.
- Keep mod names, game terms and proper nouns as they are, in English spelling.
- Do not add explanations, quotes, punctuation, numbering or mod names the request does not mention.

Example: "хочу автоматизировать ферму и не получить лагов" -> automatic farm automation crops harvest performance lag"""


def needs_translation(query: str) -> bool:
    """Переводятся только запросы с кириллицей; английский запрос идёт в поиск как есть."""
    return bool(CYRILLIC.search(query))


def clean_keywords(text: str) -> str:
    """Первая строка ответа → строчные английские слова через пробел."""
    line = next((s for s in text.strip().splitlines() if s.strip()), "")
    line = line.split("->")[-1].lower()  # если модель повторила формат примера
    line = LABEL.sub("", line)  # «Keywords: …»
    words = (w.strip("-'") for w in NOT_KEYWORD.sub(" ", line).split())
    words = [w for w in words if any(c.isalnum() for c in w)]
    return " ".join(words[:MAX_KEYWORDS])


def translate_query(llm: LLM | None, query: str) -> str:
    """Запрос для поиска. Ошибку LLM передаёт дальше: это ошибка поиска (RULE-ERR-01)."""
    if llm is None or not needs_translation(query):
        return query
    keywords = clean_keywords(llm.complete(SYSTEM_PROMPT, query, max_tokens=64, temperature=0.0))
    if not keywords:
        raise LLMError("перевод запроса пустой")
    return keywords
