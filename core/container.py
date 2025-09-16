from __future__ import annotations

from typing import Optional
from django.conf import settings
from django.core.cache import caches

from ai.clients.gemini_client import GeminiClient
from ai.orchestrator import AIOrchestrator
from core.notifications.telegram_notifier import TelegramNotifier


class Container:
    """Простой контейнер зависимостей для провайдеров приложения."""

    _ai_orchestrator: Optional[AIOrchestrator] = None
    _notifier: Optional[TelegramNotifier] = None

    @classmethod
    def ai_orchestrator(cls) -> AIOrchestrator:
        if cls._ai_orchestrator is None:
            client = GeminiClient(model_name='gemini-1.5-flash')
            cls._ai_orchestrator = AIOrchestrator(client)
        return cls._ai_orchestrator

    @classmethod
    def notifier(cls) -> TelegramNotifier:
        if cls._notifier is None:
            cls._notifier = TelegramNotifier(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))
        return cls._notifier

    @staticmethod
    def cache(alias: str = 'default'):
        return caches[alias]
