from __future__ import annotations

from typing import Optional
from django.conf import settings
from django.core.cache import caches

from ai.clients.gemini_client import GeminiClient
from ai.clients.deepseek_client import DeepSeekClient
from ai.orchestrator import AIOrchestrator
from ai.dual_orchestrator import DualAIOrchestrator
from core.notifications.telegram_notifier import TelegramNotifier


class Container:
    """Контейнер зависимостей с поддержкой множественных AI провайдеров."""

    _ai_orchestrator: Optional[AIOrchestrator] = None
    _dual_ai_orchestrator: Optional[DualAIOrchestrator] = None
    _notifier: Optional[TelegramNotifier] = None

    @classmethod
    def ai_orchestrator(cls) -> AIOrchestrator:
        """Возвращает стандартный AI оркестратор (обратная совместимость)"""
        if cls._ai_orchestrator is None:
            # Используем DualAIOrchestrator как основной
            cls._ai_orchestrator = cls.dual_ai_orchestrator()  # type: ignore
        return cls._ai_orchestrator  # type: ignore
    
    @classmethod
    def dual_ai_orchestrator(cls) -> DualAIOrchestrator:
        """Возвращает dual AI оркестратор с поддержкой Gemini + DeepSeek"""
        if cls._dual_ai_orchestrator is None:
            cls._dual_ai_orchestrator = DualAIOrchestrator()
        return cls._dual_ai_orchestrator
    
    @classmethod
    def gemini_client(cls) -> GeminiClient:
        """Возвращает только Gemini клиент"""
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY не найден")
        return GeminiClient(api_key=gemini_key)
    
    @classmethod
    def deepseek_client(cls) -> DeepSeekClient:
        """Возвращает только DeepSeek клиент"""
        deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not deepseek_key:
            raise ValueError("DEEPSEEK_API_KEY не найден")
        return DeepSeekClient(api_key=deepseek_key)

    @classmethod
    def notifier(cls) -> TelegramNotifier:
        if cls._notifier is None:
            cls._notifier = TelegramNotifier(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))
        return cls._notifier

    @staticmethod
    def cache(alias: str = 'default'):
        return caches[alias]
