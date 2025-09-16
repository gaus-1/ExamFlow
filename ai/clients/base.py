from __future__ import annotations

from typing import Protocol, TypedDict


class AIResponse(TypedDict):
    answer: str
    sources: list[dict]
    practice: dict


class AIClientProtocol(Protocol):
    """Абстракция клиента ИИ-провайдера."""

    def generate(self, prompt: str) -> str:
        """Синхронно возвращает текстовый ответ на промпт."""
        ...
