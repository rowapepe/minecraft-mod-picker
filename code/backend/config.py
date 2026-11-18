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
DEFAULT_CA_BUNDLE = ROOT_DIR / "certs" / "russian_trusted_ca.pem"  # сертификаты Минцифры для GigaChat (D-18)
# Классический адрес GigaChat API; новый api.giga.chat (по умолчанию в gigachat 0.2) доступен не из всех сетей
DEFAULT_LLM_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
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


def resolve_path(value: str) -> str:
    """Относительный путь из .env считается от корня репозитория."""
    if not value:
        return ""
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else ROOT_DIR / path)


def default_ca_bundle() -> str:
    return str(DEFAULT_CA_BUNDLE) if DEFAULT_CA_BUNDLE.is_file() else ""


@dataclass(frozen=True)
class Settings:
    user_login: str
    user_password: str
    admin_login: str
    admin_password: str
    session_secret: str
    db_path: Path
    # LLM: GigaChat (D-18); пустой ключ — LLM не подключена
    llm_api_key: str = ""
    llm_model: str = "GigaChat"
    llm_scope: str = "GIGACHAT_API_PERS"
    llm_ca_bundle: str = ""
    llm_timeout: float = 30.0
    llm_base_url: str = DEFAULT_LLM_BASE_URL

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
            llm_api_key=env.get("LLM_API_KEY", ""),
            llm_model=env.get("LLM_MODEL") or "GigaChat",
            llm_scope=env.get("LLM_SCOPE") or "GIGACHAT_API_PERS",
            llm_ca_bundle=resolve_path(env.get("LLM_CA_BUNDLE", "")) or default_ca_bundle(),
            llm_timeout=float(env.get("LLM_TIMEOUT") or 30),
            llm_base_url=env.get("LLM_BASE_URL") or DEFAULT_LLM_BASE_URL,
        )
