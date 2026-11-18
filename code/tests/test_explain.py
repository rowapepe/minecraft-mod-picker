"""Объяснение по найденным модам и отказ (`D-19`, `GAP-19`) на подставной LLM."""

import pytest
from fastapi.testclient import TestClient

from backend.explain import (
    BODY_CHARS,
    NO_ANSWER_MARK,
    REFUSAL,
    SYSTEM_PROMPT as EXPLAIN_PROMPT,
    build_user_message,
    explain,
    format_documents,
    is_refusal,
)
from backend.llm import LLMError
from backend.main import create_app
from backend.translate import SYSTEM_PROMPT as TRANSLATE_PROMPT
from test_backend import engine, login, settings  # noqa: F401 — общие фикстуры


class ScriptedLLM:
    """Перевод и объяснение отвечают по-разному; можно уронить любой из шагов."""

    def __init__(self, translation="harvest crops right click", explanation="RightClickHarvest подходит.",
                 explain_error=None):
        self.translation, self.explanation, self.explain_error = translation, explanation, explain_error
        self.calls = []

    def complete(self, system, user, *, max_tokens=512, temperature=0.2):
        self.calls.append((system, user))
        if system == TRANSLATE_PROMPT:
            return self.translation
        if self.explain_error:
            raise self.explain_error
        return self.explanation


DOC = {
    "title": "RightClickHarvest",
    "description": "Allows you to harvest crops with right click",
    "body": "word " * 400,
    "categories": ["utility", "farming"],
}


def test_format_documents_keeps_only_given_mods_and_cuts_body():
    text = format_documents([DOC, {**DOC, "title": "Second", "body": "", "categories": []}])
    assert "1. Название: RightClickHarvest" in text and "2. Название: Second" in text
    assert "Категории: utility, farming" in text and "Категории: —" in text
    first_body = text.split("Подробно: ")[1].split("\n")[0]
    assert len(first_body) <= BODY_CHARS + 2 and first_body.endswith("…")


def test_user_message_has_original_query():
    assert build_user_message("хочу собирать урожай", [DOC]).startswith("Запрос игрока: хочу собирать урожай")


@pytest.mark.parametrize("text", [NO_ANSWER_MARK, " no_answer ", "NO ANSWER", "Ответ: NO_ANSWER."])
def test_refusal_mark_is_recognized(text):
    assert is_refusal(text)


def test_normal_text_is_not_refusal():
    assert not is_refusal("RightClickHarvest собирает урожай правой кнопкой мыши.")


def test_explain_returns_text_or_fixed_refusal():
    assert explain(ScriptedLLM(), "урожай", [DOC]) == "RightClickHarvest подходит."
    assert explain(ScriptedLLM(explanation=NO_ANSWER_MARK), "самолёты", [DOC]) == REFUSAL


def test_explain_skips_llm_without_docs_or_key():
    llm = ScriptedLLM()
    assert explain(llm, "урожай", []) is None
    assert explain(None, "урожай", [DOC]) is None
    assert llm.calls == []


def test_search_returns_explanation_for_found_mods(settings, engine):  # noqa: F811
    llm = ScriptedLLM()
    client = TestClient(create_app(settings, engine, llm))
    login(client)
    body = client.post("/api/search", json={"query": "сбор урожая правой кнопкой"}).json()
    assert body["answer"] == "RightClickHarvest подходит."
    system, user = llm.calls[1]
    assert system == EXPLAIN_PROMPT
    assert user.startswith("Запрос игрока: сбор урожая правой кнопкой")  # исходный запрос, не перевод
    for mod in body["mods"]:  # LLM получает ровно найденные моды (RULE-ANS-01)
        assert f"Название: {mod['title']}" in user
    assert user.count("Название: ") == len(body["mods"])


def test_search_returns_refusal_with_mods(settings, engine):  # noqa: F811
    client = TestClient(create_app(settings, engine, ScriptedLLM(explanation=NO_ANSWER_MARK)))
    login(client)
    body = client.post("/api/search", json={"query": "сбор урожая правой кнопкой"}).json()
    assert body["mods"] and body["answer"] == REFUSAL


def test_explain_error_keeps_mods_without_answer(settings, engine):  # noqa: F811
    llm = ScriptedLLM(explain_error=LLMError("GigaChat: ReadTimeout"))
    client = TestClient(create_app(settings, engine, llm))
    login(client)
    r = client.post("/api/search", json={"query": "сбор урожая правой кнопкой"})
    assert r.status_code == 200  # RULE-ANS-04, GWT-09
    assert r.json()["mods"] and r.json()["answer"] is None
    login(client, "admin", "admin-pass")
    stats = client.get("/api/admin/stats").json()
    assert stats["requests"] == 1 and stats["noResults"] == 0


def test_empty_result_does_not_call_explanation(settings, engine):  # noqa: F811
    llm = ScriptedLLM(translation="airplane jet propeller")
    client = TestClient(create_app(settings, engine, llm))
    login(client)
    body = client.post("/api/search", json={"query": "самолёты"}).json()
    assert body == {"mods": [], "answer": None}
    assert [system for system, _ in llm.calls] == [TRANSLATE_PROMPT]
