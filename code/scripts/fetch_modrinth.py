"""Выгрузка корпуса описаний модов с Modrinth API v2.

Берёт N самых скачиваемых проектов типа `mod` (GAP-17), догружает полные
описания пакетными запросами `/v2/projects`, очищает `body` (RULE-DATA-05)
и сохраняет снимок в JSONL: одна строка — один документ с полями из
`docs/Product/05-rules-and-data-meaning.md`, раздел 2.6.

Запуск из корня репозитория:

    python3 code/scripts/fetch_modrinth.py            # 1000 модов
    python3 code/scripts/fetch_modrinth.py --limit 50 # пробная выгрузка

`User-Agent` берётся из `MODRINTH_USER_AGENT` (окружение или `.env` в корне).
Запросы идут не чаще одного в 0.25 с (240 в минуту при лимите 300);
на ответ 429 скрипт ждёт столько, сколько сказал сервер.

Используется только стандартная библиотека Python 3.12.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

API = "https://api.modrinth.com/v2"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "code" / "data" / "mods.jsonl"
SEARCH_PAGE = 100  # максимум limit у /v2/search
PROJECTS_BATCH = 100  # id в одном запросе /v2/projects
MIN_INTERVAL = 0.25  # секунд между запросами: 240 в минуту < 300
MAX_RETRIES = 5

GetJson = Callable[[str, dict[str, str]], Any]


# ---------------------------------------------------------------- очистка body

_RE_COMMENT = re.compile(r"<!--.*?-->", re.S)
_RE_FENCE = re.compile(r"^\s*(```|~~~).*$", re.M)
_RE_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]")
_RE_MD_LINK = re.compile(r"\[([^\[\]]*)\]\([^)]*\)|\[([^\[\]]*)\]\[[^\]]*\]")
_RE_REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*\S+.*$", re.M)
_RE_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_RE_URL = re.compile(r"(?:https?://|www\.)\S+")
_RE_RULE = re.compile(r"^\s*([-=*_])\1{2,}\s*$", re.M)
_RE_LIST = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+", re.M)
_RE_SYMBOLS = re.compile(r"[#*_~`>|\\]+")
_RE_TABLE_SEP = re.compile(r":?-{3,}:?")
_RE_SPACE = re.compile(r"\s+")


def clean_body(text: str | None) -> str:
    """Убирает из markdown/HTML картинки, ссылки, теги и символы разметки.

    Текст ссылок остаётся, адреса и картинки (вместе с подписью) удаляются.
    Результат — одна строка, пробелы схлопнуты.
    """
    if not text:
        return ""
    s = _RE_COMMENT.sub(" ", text)
    s = _RE_FENCE.sub(" ", s)
    s = _RE_MD_IMAGE.sub(" ", s)
    # ссылки могут быть вложены в другие ссылки ([![img](a)](b) после
    # удаления картинки становится [ ](b)), поэтому повторяем до упора
    while True:
        new = _RE_MD_LINK.sub(lambda m: m.group(1) or m.group(2) or " ", s)
        if new == s:
            break
        s = new
    s = _RE_REF_DEF.sub(" ", s)
    s = _RE_HTML_TAG.sub(" ", s)
    s = html.unescape(s)
    s = _RE_URL.sub(" ", s)
    s = _RE_RULE.sub(" ", s)
    s = _RE_LIST.sub(" ", s)
    s = _RE_TABLE_SEP.sub(" ", s)
    s = _RE_SYMBOLS.sub(" ", s)
    return _RE_SPACE.sub(" ", s).strip()


# ------------------------------------------------------------------- документ


def to_record(project: dict[str, Any]) -> dict[str, Any]:
    """Проект Modrinth → документ корпуса (поля из `05`, раздел 2.6)."""
    slug = project["slug"]
    return {
        "id": project["id"],
        "slug": slug,
        "title": (project.get("title") or "").strip(),
        "description": _RE_SPACE.sub(" ", project.get("description") or "").strip(),
        "body": clean_body(project.get("body")),
        "categories": list(project.get("categories") or []),
        "loaders": list(project.get("loaders") or []),
        "game_versions": list(project.get("game_versions") or []),
        "url": f"https://modrinth.com/mod/{slug}",
        "downloads": int(project.get("downloads") or 0),
    }


# ---------------------------------------------------------------------- сеть


class HttpClient:
    """GET с паузой между запросами, повторами и учётом 429."""

    def __init__(self, user_agent: str, min_interval: float = MIN_INTERVAL):
        self.user_agent = user_agent
        self.min_interval = min_interval
        self._last = 0.0
        self.requests = 0

    def _wait_turn(self) -> None:
        delay = self._last + self.min_interval - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()

    def get_json(self, path: str, params: dict[str, str]) -> Any:
        url = f"{API}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url, headers={"User-Agent": self.user_agent, "Accept": "application/json"}
        )
        for attempt in range(1, MAX_RETRIES + 1):
            self._wait_turn()
            self.requests += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = _retry_after(e.headers)
                    print(f"429 от Modrinth, жду {wait:.0f} с", file=sys.stderr)
                    time.sleep(wait)
                    continue
                if 500 <= e.code < 600 and attempt < MAX_RETRIES:
                    time.sleep(2**attempt)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                if attempt < MAX_RETRIES:
                    time.sleep(2**attempt)
                    continue
                raise
        raise RuntimeError(f"не удалось получить {url} за {MAX_RETRIES} попыток")


def _retry_after(headers: Any) -> float:
    for name in ("Retry-After", "X-Ratelimit-Reset"):
        value = headers.get(name) if headers else None
        if value:
            try:
                return max(1.0, float(value))
            except ValueError:
                pass
    return 60.0


# ------------------------------------------------------------------ выгрузка


def collect_ids(get_json: GetJson, limit: int) -> list[str]:
    """id первых `limit` модов по числу скачиваний, без повторов."""
    ids: list[str] = []
    seen: set[str] = set()
    offset = 0
    while len(ids) < limit:
        page = get_json(
            "/search",
            {
                "facets": json.dumps([["project_type:mod"]]),
                "index": "downloads",
                "limit": str(min(SEARCH_PAGE, limit - len(ids))),
                "offset": str(offset),
            },
        )
        hits = page.get("hits") or []
        if not hits:
            break
        for hit in hits:
            pid = hit["project_id"]
            if pid not in seen:
                seen.add(pid)
                ids.append(pid)
        offset += len(hits)
    return ids[:limit]


def fetch_projects(get_json: GetJson, ids: list[str]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for start in range(0, len(ids), PROJECTS_BATCH):
        batch = ids[start : start + PROJECTS_BATCH]
        projects.extend(get_json("/projects", {"ids": json.dumps(batch)}))
        print(f"проекты: {min(start + PROJECTS_BATCH, len(ids))}/{len(ids)}", file=sys.stderr)
    return projects


def build_corpus(projects: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Только `project_type == mod`, по убыванию скачиваний, при равенстве по id."""
    records = {p["id"]: to_record(p) for p in projects if p.get("project_type") == "mod"}
    return sorted(records.values(), key=lambda r: (-r["downloads"], r["id"]))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------- настройки


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def user_agent() -> str:
    ua = os.environ.get("MODRINTH_USER_AGENT") or read_env_file(REPO_ROOT / ".env").get(
        "MODRINTH_USER_AGENT", ""
    )
    if not ua:
        sys.exit(
            "Не задан MODRINTH_USER_AGENT (в окружении или в .env в корне репозитория).\n"
            "Modrinth просит указывать проект и контакт, например:\n"
            "  MODRINTH_USER_AGENT=github_user/minecraft-mod-picker/0.1"
        )
    return ua


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=1000, help="сколько модов выгрузить")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="файл JSONL")
    args = parser.parse_args(argv)

    client = HttpClient(user_agent())
    started = datetime.now(timezone.utc)
    ids = collect_ids(client.get_json, args.limit)
    print(f"найдено id: {len(ids)}", file=sys.stderr)
    corpus = build_corpus(fetch_projects(client.get_json, ids))
    write_jsonl(args.out, corpus)

    meta = {
        "source": f"{API}/search + {API}/projects",
        "query": {"facets": [["project_type:mod"]], "index": "downloads", "limit": args.limit},
        "fetched_at": started.isoformat(timespec="seconds"),
        "documents": len(corpus),
        "empty_body": sum(1 for r in corpus if not r["body"]),
        "requests": client.requests,
    }
    meta_path = args.out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"сохранено {len(corpus)} документов в {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
