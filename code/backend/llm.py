"""Тонкая обёртка над LLM (`D-08`, `D-18`): остальной код знает только `LLM.complete`.

Провайдер — GigaChat. Чтобы заменить его (например, на локальную модель),
достаточно другого класса с методом `complete` и правки `make_llm`.
"""

from __future__ import annotations

from typing import Protocol

from .config import Settings


class LLMError(Exception):
    """LLM недоступна или вернула неподходящий ответ."""


class LLM(Protocol):
    def complete(self, system: str, user: str, *, max_tokens: int = 512, temperature: float = 0.2) -> str:
        """Ответ модели на одно сообщение пользователя с системной инструкцией."""
        ...


class GigaChatLLM:
    def __init__(self, settings: Settings):
        from gigachat import GigaChat  # импорт здесь: тестам на подставной LLM библиотека не нужна

        self._client = GigaChat(
            base_url=settings.llm_base_url,
            credentials=settings.llm_api_key,
            scope=settings.llm_scope,
            model=settings.llm_model,
            ca_bundle_file=settings.llm_ca_bundle or None,
            timeout=settings.llm_timeout,
        )

    def complete(self, system: str, user: str, *, max_tokens: int = 512, temperature: float = 0.2) -> str:
        payload = {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            response = self._client.chat(payload)
            text = response.choices[0].message.content
        except Exception as error:  # сеть, авторизация, лимит, сертификат
            raise LLMError(f"GigaChat: {type(error).__name__}") from error
        if not text or not text.strip():
            raise LLMError("GigaChat: пустой ответ")
        return text.strip()


def make_llm(settings: Settings) -> LLM | None:
    """LLM по настройкам или None, если ключ не задан."""
    if not settings.llm_api_key:
        return None
    return GigaChatLLM(settings)
