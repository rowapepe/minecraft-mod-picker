"""Вход и сессия: две учётные записи из `.env` (RULE-AUTH-01, RULE-AUTH-02), подписанная cookie."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Literal

from .config import Settings

Role = Literal["user", "admin"]
COOKIE_NAME = "session"


def check_credentials(settings: Settings, login: str, password: str) -> Role | None:
    """Роль при верных данных, иначе None. Неверный логин и пароль неразличимы (RULE-AUTH-03)."""
    accounts: list[tuple[str, str, Role]] = [
        (settings.user_login, settings.user_password, "user"),
        (settings.admin_login, settings.admin_password, "admin"),
    ]
    found: Role | None = None
    for acc_login, acc_password, role in accounts:
        if not acc_login or not acc_password:
            continue  # учётная запись не настроена в .env
        login_ok = hmac.compare_digest(login.encode(), acc_login.encode())
        password_ok = hmac.compare_digest(password.encode(), acc_password.encode())
        if login_ok and password_ok:
            found = role
    return found


def _sign(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(settings: Settings, role: Role) -> str:
    payload = f"{role}:{secrets.token_hex(8)}"
    return f"{payload}.{_sign(settings.session_secret, payload)}"


def read_session(settings: Settings, value: str | None) -> Role | None:
    if not value or "." not in value:
        return None
    payload, signature = value.rsplit(".", 1)
    if not hmac.compare_digest(signature, _sign(settings.session_secret, payload)):
        return None
    role = payload.split(":", 1)[0]
    return role if role in ("user", "admin") else None  # type: ignore[return-value]
