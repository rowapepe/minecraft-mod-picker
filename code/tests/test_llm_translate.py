"""Обёртка LLM и перевод запроса (`D-18`) на подставной LLM, без сети и ключа."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.llm import GigaChatLLM, LLMError, make_llm
from backend.main import create_app
from backend.translate import SYSTEM_PROMPT, clean_keywords, needs_translation, translate_query
from test_backend import engine, login, settings  # noqa: F401 — общие фикстуры


class FakeLLM:
    def __init__(self, reply="harvest crops right click", error=None):
        self.reply, self.error, self.calls = reply, error, []

    def complete(self, system, user, *, max_tokens=512, temperature=0.2):
        self.calls.append((system, user))
        if self.error:
            raise self.error
        return self.reply


@pytest.mark.parametrize(
    ("query", "expected"),
    [("ферма без лагов", True), ("моды для Create", True), ("Ёлка", True), ("magic spells", False), ("123", False)],
)
def test_needs_translation(query, expected):
    assert needs_translation(query) is expected


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("Automatic Farm, crops; harvest!", "automatic farm crops harvest"),
        ("\n  magic spells wands\nExplanation: ...", "magic spells wands"),
        ('"хочу магию" -> magic spells', "magic spells"),
        ("Keywords: fps performance", "fps performance"),
        ("x-ray mod's ore -- finder", "x-ray mod's ore finder"),
        ("только по-русски", ""),
    ],
)
def test_clean_keywords(reply, expected):
    assert clean_keywords(reply) == expected


def test_translate_calls_llm_only_for_cyrillic():
    llm = FakeLLM()
    assert translate_query(llm, "magic spells") == "magic spells"
    assert llm.calls == []
    assert translate_query(llm, "сбор урожая правой кнопкой") == "harvest crops right click"
    assert llm.calls == [(SYSTEM_PROMPT, "сбор урожая правой кнопкой")]


def test_translate_without_llm_keeps_query():
    assert translate_query(None, "ферма без лагов") == "ферма без лагов"


def test_translate_empty_reply_is_error():
    with pytest.raises(LLMError):
        translate_query(FakeLLM(reply="..."), "ферма")


def test_russian_query_is_translated_before_search(settings, engine):  # noqa: F811
    llm = FakeLLM()
    client = TestClient(create_app(settings, engine, llm))
    login(client)
    body = client.post("/api/search", json={"query": "сбор урожая правой кнопкой"}).json()
    assert body["mods"][0]["slug"] == "rightclickharvest"
    assert body["answer"] is None
    assert len(llm.calls) == 1


def test_translation_failure_is_500_and_counted(settings, engine):  # noqa: F811
    llm = FakeLLM(error=LLMError("GigaChat: ConnectError"))
    client = TestClient(create_app(settings, engine, llm), raise_server_exceptions=False)
    login(client)
    r = client.post("/api/search", json={"query": "ферма"})
    assert r.status_code == 500 and "GigaChat" not in r.text  # RULE-ERR-01
    login(client, "admin", "admin-pass")
    assert client.get("/api/admin/stats").json()["requests"] == 1


def test_make_llm_without_key_is_none(settings):  # noqa: F811
    assert make_llm(settings) is None


def gigachat_with(settings, chat):  # noqa: F811
    llm = GigaChatLLM(Settings(**{**settings.__dict__, "llm_api_key": "test-key"}))
    llm._client = SimpleNamespace(chat=chat)
    return llm


def test_gigachat_returns_text_and_sends_messages(settings):  # noqa: F811
    sent = {}

    def chat(payload):
        sent.update(payload)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="  fps lag  "))])

    assert gigachat_with(settings, chat).complete("sys", "user", max_tokens=10) == "fps lag"
    assert sent["messages"] == [{"role": "system", "content": "sys"}, {"role": "user", "content": "user"}]
    assert sent["max_tokens"] == 10


def test_gigachat_errors_become_llm_error(settings):  # noqa: F811
    def chat(payload):
        raise ConnectionError("no network")

    with pytest.raises(LLMError):
        gigachat_with(settings, chat).complete("sys", "user")


def test_ca_bundle_path_is_relative_to_repo_root():
    from backend.config import ROOT_DIR, resolve_path

    assert resolve_path("") == ""
    assert resolve_path("certs/ca.pem") == str(ROOT_DIR / "certs" / "ca.pem")
    assert resolve_path("/etc/ssl/ca.pem") == "/etc/ssl/ca.pem"


def test_gigachat_uses_classic_url_and_repo_certificates(settings):  # noqa: F811
    from backend.config import DEFAULT_CA_BUNDLE, DEFAULT_LLM_BASE_URL, default_ca_bundle

    assert default_ca_bundle() == str(DEFAULT_CA_BUNDLE)  # файл есть в репозитории
    assert "BEGIN CERTIFICATE" in DEFAULT_CA_BUNDLE.read_text()
    llm = GigaChatLLM(Settings(**{**settings.__dict__, "llm_api_key": "test-key", "llm_ca_bundle": str(DEFAULT_CA_BUNDLE)}))
    assert llm._client._settings.base_url == DEFAULT_LLM_BASE_URL
    assert llm._client._settings.ca_bundle_file == str(DEFAULT_CA_BUNDLE)
