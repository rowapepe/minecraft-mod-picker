"""Тесты выгрузки корпуса без обращения к сети (RULE-DATA-05, раздел 2.6 `05`)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fetch_modrinth as fm  # noqa: E402


def test_clean_body_removes_images_links_tags_and_markup():
    md = (
        "# Sodium\n"
        "[![badge](https://img.shields.io/x.svg)](https://discord.gg/x)\n"
        "![screenshot](https://cdn.modrinth.com/a.png)\n"
        "<p align=\"center\"><img src=\"logo.png\" alt=\"logo\"></p>\n"
        "A **rendering** engine that _greatly_ improves `FPS`.\n"
        "See the [wiki](https://github.com/x/wiki) or https://example.com.\n"
        "- fewer lag spikes\n"
        "---\n"
        "| a | b |\n|---|:---:|\n"
        "<!-- hidden -->Tom &amp; Jerry"
    )
    out = fm.clean_body(md)
    assert out == (
        "Sodium A rendering engine that greatly improves FPS . "
        "See the wiki or fewer lag spikes a b Tom & Jerry"
    )
    for junk in ("http", "png", "badge", "screenshot", "<", "#", "*", "hidden"):
        assert junk not in out


def test_clean_body_empty():
    assert fm.clean_body(None) == ""
    assert fm.clean_body("") == ""


def test_to_record_fields_and_url():
    project = {
        "id": "AANobbMI",
        "slug": "sodium",
        "title": " Sodium ",
        "description": "Fast\n rendering",
        "body": "**Hello** [docs](https://x)",
        "categories": ["optimization"],
        "loaders": ["fabric"],
        "game_versions": ["1.21"],
        "downloads": 10,
        "project_type": "mod",
        "extra": "ignored",
    }
    assert fm.to_record(project) == {
        "id": "AANobbMI",
        "slug": "sodium",
        "title": "Sodium",
        "description": "Fast rendering",
        "body": "Hello docs",
        "categories": ["optimization"],
        "loaders": ["fabric"],
        "game_versions": ["1.21"],
        "url": "https://modrinth.com/mod/sodium",
        "downloads": 10,
    }


def test_collect_ids_pages_dedups_and_stops_at_limit():
    pages = {0: ["a", "b", "c"], 3: ["c", "d", "e"], 6: []}
    calls = []

    def fake(path, params):
        assert path == "/search"
        assert json.loads(params["facets"]) == [["project_type:mod"]]
        assert params["index"] == "downloads"
        calls.append(int(params["offset"]))
        return {"hits": [{"project_id": p} for p in pages[int(params["offset"])]]}

    assert fm.collect_ids(fake, 4) == ["a", "b", "c", "d"]
    assert fm.collect_ids(fake, 100) == ["a", "b", "c", "d", "e"]
    assert calls[-1] == 6  # остановились на пустой странице


def test_build_corpus_filters_type_and_sorts():
    def proj(pid, downloads, ptype="mod"):
        return {"id": pid, "slug": pid, "downloads": downloads, "project_type": ptype}

    corpus = fm.build_corpus([proj("b", 5), proj("a", 5), proj("c", 9), proj("x", 99, "modpack")])
    assert [r["id"] for r in corpus] == ["c", "a", "b"]


def test_write_jsonl_roundtrip(tmp_path):
    path = tmp_path / "data" / "mods.jsonl"
    fm.write_jsonl(path, [{"id": "a", "title": "Ферма"}, {"id": "b", "title": "x"}])
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["a", "b"]
    assert "Ферма" in lines[0]
    assert not path.with_suffix(".jsonl.tmp").exists()


def test_read_env_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# c\nMODRINTH_USER_AGENT='me/proj/0.1'\nEMPTY=\n", encoding="utf-8")
    assert fm.read_env_file(env) == {"MODRINTH_USER_AGENT": "me/proj/0.1", "EMPTY": ""}
