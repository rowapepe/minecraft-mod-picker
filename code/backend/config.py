"""Настройки бэкенда из единого `.env` в корне репозитория (`docs/Tech/02-running.md`).

Переменные окружения процесса важнее значений из файла.
"""

from __future__ import annotations

import os
import secrets
import warnings
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / ".data" / "analytics.sqlite3"


def read_env_file(path: Path) -> dict[str, str]:
    """Простой разбор `.env`: строки `ИМЯ=значение`, комментарии `#`, кавычки вокруг значения."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name.strip()] = value
    return values


@dataclass(frozen=True)
class Settings:
    user_login: str
    user_password: str
    admin_login: str
    admin_password: str
    session_secret: str
    db_path: Path

    @classmethod
    def load(cls, env_path: Path = ENV_PATH) -> "Settings":
        env = {**read_env_file(env_path), **os.environ}
        secret = env.get("SESSION_SECRET", "")
        if not secret:
            # Без ключа сессии каркас работает, но сессии не переживут перезапуск.
            warnings.warn("SESSION_SECRET не задан: используется случайный ключ до перезапуска", stacklevel=2)
            secret = secrets.token_hex(32)
        return cls(
            user_login=env.get("USER_LOGIN", ""),
            user_password=env.get("USER_PASSWORD", ""),
            admin_login=env.get("ADMIN_LOGIN", ""),
            admin_password=env.get("ADMIN_PASSWORD", ""),
            session_secret=secret,
            db_path=Path(env.get("BACKEND_DB_PATH") or DEFAULT_DB_PATH),
        )
