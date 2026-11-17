"""Собирает зафиксированный корпус benchmark из 30 документов (GAP-18, RULE-QA-04).

Моды выбраны вручную по категориям Modrinth и описаниям — по три на каждую
из десяти тем вопросов, — а не по выдаче BM25, чтобы набор не подстраивался
под поиск. Каждому документу присваивается ID `D01…D30`; поле `id` хранит id
проекта Modrinth. Тексты копируются из снимка `code/data/mods.jsonl`, поэтому
повторная выгрузка с Modrinth benchmark не меняет.

    python3 code/benchmark/make_corpus.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE.parent / "data" / "mods.jsonl"
OUT = HERE / "corpus.jsonl"

# тема → slug модов; порядок задаёт номера D01…D30
SELECTION = {
    "фермерство и урожай": ["rightclickharvest", "smarter-farmers-farmers-replant", "lets-do-farm-charm"],
    "готовка и напитки": ["farmers-delight", "kaleidoscope-cookery", "lets-do-herbalbrews"],
    "хранение предметов": ["toms-storage", "sophisticated-storage", "ae2"],
    "производительность": ["sodium", "lithium", "ferrite-core"],
    "графика и эффекты": ["iris", "lambdynamiclights", "visuality"],
    "магия": ["irons-spells-n-spellbooks", "wizards", "goety"],
    "генерация мира": ["terralith", "biomes-o-plenty", "tectonic"],
    "постройки и подземелья": ["yungs-better-dungeons", "dungeons-and-taverns", "towns-and-towers"],
    "боссы и оружие": ["l_enders-cataclysm", "mowzies-mobs", "simply-swords"],
    "карты и перемещение": ["xaeros-minimap", "xaeros-world-map", "waystones"],
}


def main() -> None:
    snapshot = {}
    with SNAPSHOT.open(encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            snapshot[doc["slug"]] = doc
    records = []
    for topic, slugs in SELECTION.items():
        for slug in slugs:
            doc = snapshot[slug]
            records.append({"bench_id": f"D{len(records) + 1:02d}", "topic": topic, **doc})
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(records)} документов → {OUT}")


if __name__ == "__main__":
    main()
