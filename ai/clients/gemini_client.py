from __future__ import annotations

import os
import logging
import google.generativeai as genai  # type: ignore

from .base import AIClientProtocol

logger = logging.getLogger(__name__)


class GeminiClient(AIClientProtocol):
    def __init__(self, model_name: str = 'gemini-1.5-flash', api_key: str | None = None) -> None:
        api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY is not set')
        genai.configure(api_key=api_key)  # type: ignore
        self._model = genai.GenerativeModel(model_name)  # type: ignore

    def generate(self, prompt: str) -> str:
        try:
            resp = self._model.generate_content(prompt)  # type: ignore
            return getattr(resp, 'text', '') or ''
        except Exception as e:
            logger.error(f'Gemini generate error: {e}')
            raise
