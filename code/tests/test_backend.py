"""API: контракт `docs/Tech/04-api-and-access.md`; поиск BM25 без LLM (`D-17`)."""

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings, read_env_file
from backend.main import create_app
from backend.stats import Stats
from search import ModSearch

BENCH_CORPUS = Path(__file__).resolve().parents[1] / "benchmark" / "corpus.jsonl"


@pytest.fixture(scope="module")
def engine():
    # 30 документов benchmark: быстро и с известным составом
    return ModSearch.build(BENCH_CORPUS)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        user_login="player",
        user_password="player-pass",
        admin_login="admin",
        admin_password="admin-pass",
        session_secret="test-secret",
        db_path=tmp_path / "analytics.sqlite3",
    )


@pytest.fixture
def client(settings, engine):
    return TestClient(create_app(settings, engine))


def login(client, who="player", password="player-pass"):
    return client.post("/api/auth/login", json={"login": who, "password": password})


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_sets_cookie_and_me_returns_role(client):
    r = login(client)
    assert r.status_code == 200 and r.json() == {"role": "user"}
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/auth/me").json() == {"role": "user"}


def test_wrong_login_and_wrong_password_give_same_401(client):
    a = login(client, who="nobody")
    b = login(client, password="wrong")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_me_without_session_and_with_forged_cookie(client):
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("session", "admin:x.deadbeef")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(client):
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_search_returns_bm25_mods(client, engine):
    login(client)
    r = client.post("/api/search", json={"query": "  harvest crops with right click "})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] is None  # LLM ещё не подключена (D-17)
    assert 1 <= len(body["mods"]) <= 5  # RULE-SRCH-04
    expected = [doc["slug"] for doc, _ in engine.search("harvest crops with right click", k=5)]
    assert [m["slug"] for m in body["mods"]] == expected  # порядок BM25 (RULE-SRCH-03)
    assert body["mods"][0]["slug"] == "rightclickharvest"
    first = body["mods"][0]
    assert set(first) == {"slug", "title", "description", "categories", "url"}
    assert first["url"].startswith("https://modrinth.com/mod/")


def test_search_without_matches_is_empty_and_counted(client):
    login(client)
    r = client.post("/api/search", json={"query": "ферма без лагов"})  # без перевода (GAP-01)
    assert r.json() == {"mods": [], "answer": None}
    login(client, "admin", "admin-pass")
    s = client.get("/api/admin/stats").json()
    assert s["requests"] == 1 and s["noResults"] == 1


def test_search_failure_is_500_and_counted(settings):
    class Broken:
        def search(self, query, k=5):
            raise RuntimeError("index is broken")

    client = TestClient(create_app(settings, Broken()), raise_server_exceptions=False)
    login(client)
    r = client.post("/api/search", json={"query": "farm"})
    assert r.status_code == 500 and "index" not in r.text  # RULE-ERR-01
    login(client, "admin", "admin-pass")
    s = client.get("/api/admin/stats").json()
    assert s["requests"] == 1 and s["noResults"] == 0


@pytest.mark.parametrize("query", ["", "   ", "x" * 501])
def test_search_rejects_blank_and_long(client, query):
    login(client)
    assert client.post("/api/search", json={"query": query}).status_code == 400


def test_search_bad_body_is_400(client):
    login(client)
    assert client.post("/api/search", json={}).status_code == 400


def test_roles_are_checked_on_server(client):
    assert client.post("/api/search", json={"query": "x"}).status_code == 401
    login(client, "admin", "admin-pass")
    assert client.post("/api/search", json={"query": "x"}).status_code == 403
    login(client)
    assert client.get("/api/admin/stats").status_code == 403


def test_stats_count_logins_and_valid_searches(client):
    login(client)
    client.post("/api/search", json={"query": "magic spells"})
    client.post("/api/search", json={"query": "   "})  # не считается (RULE-ADM-02)
    login(client, "admin", "admin-pass")
    s = client.get("/api/admin/stats").json()
    assert s["requests"] == 1 and s["logins"] == 2 and s["noResults"] == 0
    assert len(s["byDay"]) == 7 and s["byDay"][-1] == {"date": date.today().isoformat(), "count": 1}


def test_stats_survive_restart(settings):
    first = Stats(settings.db_path)
    first.record_search(empty=True, today=date(2026, 11, 18))
    first.close()
    snap = Stats(settings.db_path).snapshot(today=date(2026, 11, 18))
    assert snap["requests"] == 1 and snap["noResults"] == 1
    assert snap["byDay"][0]["date"] == "2026-11-12" and snap["byDay"][-1]["count"] == 1


def test_read_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# комментарий\nUSER_LOGIN=player\nLLM_MODEL=\"m\"\nEMPTY=\n", encoding="utf-8")
    assert read_env_file(env) == {"USER_LOGIN": "player", "LLM_MODEL": "m", "EMPTY": ""}
