from __future__ import annotations

import hashlib
import logging
from typing import Optional
from django.core.cache import cache

from .clients.base import AIClientProtocol, AIResponse

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Высокоуровневый фасад для работы с ИИ: кэш, fallback, постобработка."""

    def __init__(self, client: AIClientProtocol, cache_ttl_sec: int = 3600) -> None:
        self._client = client
        self._cache_ttl_sec = cache_ttl_sec

    def ask(self, prompt: str) -> AIResponse:
        key = self._make_cache_key(prompt)
        cached: Optional[AIResponse] = cache.get(key)  # type: ignore
        if cached:
            logger.info('AIOrchestrator: cache hit')
            return cached

        answer = self._client.generate(self._build_prompt(prompt))
        response: AIResponse = {
            'answer': answer,
            'sources': self._detect_sources(prompt),
            'practice': {
                'topic': self._detect_subject(prompt),
                'description': f'Практика по теме "{self._detect_subject(prompt)}"'
            }
        }
        cache.set(key, response, self._cache_ttl_sec)
        return response

    def _make_cache_key(self, prompt: str) -> str:
        h = hashlib.sha256(prompt.lower().strip().encode()).hexdigest()
        return f'ai:resp:{h}'

    def _build_prompt(self, user_prompt: str) -> str:
        return (
            "Эксперт ЕГЭ. Отвечай кратко и по делу, используй Markdown.\n\n"
            f"Вопрос: {user_prompt}\n"
        )

    def _detect_subject(self, prompt: str) -> str:
        p = prompt.lower()
        if any(x in p for x in ['математ', 'алгебр', 'геометр', 'логарифм', 'производн']):
            return 'mathematics'
        if any(x in p for x in ['русск', 'сочинен', 'грамматик', 'пунктуац']):
            return 'russian'
        return 'general'

    def _detect_sources(self, prompt: str) -> list[dict]:
        subject = self._detect_subject(prompt)
        if subject == 'mathematics':
            return []
        if subject == 'russian':
            return []
        return []
