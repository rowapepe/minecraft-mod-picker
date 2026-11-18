"""Счётчики аналитики в SQLite (RULE-ADM-02…06): сохраняются между перезапусками (RULE-ADM-03)."""

from __future__ import annotations

import sqlite3
import threading
from datetime import date, timedelta
from pathlib import Path


class Stats:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        with self._db:
            self._db.execute("CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER NOT NULL)")
            self._db.execute("CREATE TABLE IF NOT EXISTS by_day (day TEXT PRIMARY KEY, count INTEGER NOT NULL)")

    def _add(self, table: str, key_col: str, key: str) -> None:
        val_col = "value" if table == "counters" else "count"
        self._db.execute(
            f"INSERT INTO {table} ({key_col}, {val_col}) VALUES (?, 1) "
            f"ON CONFLICT({key_col}) DO UPDATE SET {val_col} = {val_col} + 1",
            (key,),
        )

    def record_login(self) -> None:
        with self._lock, self._db:
            self._add("counters", "name", "logins")

    def record_search(self, empty: bool, today: date | None = None) -> None:
        """Каждый запрос, прошедший проверки, независимо от исхода (RULE-ADM-02)."""
        day = (today or date.today()).isoformat()
        with self._lock, self._db:
            self._add("counters", "name", "requests")
            self._add("by_day", "day", day)
            if empty:
                self._add("counters", "name", "noResults")

    def snapshot(self, today: date | None = None) -> dict:
        today = today or date.today()
        with self._lock:
            counters = dict(self._db.execute("SELECT name, value FROM counters"))
            days = dict(self._db.execute("SELECT day, count FROM by_day"))
        week = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        return {
            "requests": counters.get("requests", 0),
            "logins": counters.get("logins", 0),
            "byDay": [{"date": d, "count": days.get(d, 0)} for d in week],
            "noResults": counters.get("noResults", 0),
        }

    def close(self) -> None:
        self._db.close()
