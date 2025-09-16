from __future__ import annotations

import logging
from typing import Optional
from django.conf import settings

from .base import Notifier, NotifyMessage

logger = logging.getLogger(__name__)


class TelegramNotifier(Notifier):
    def __init__(self, bot_token: Optional[str] = None) -> None:
        self._token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not self._token:
            logger.warning('TelegramNotifier: отсутствует TELEGRAM_BOT_TOKEN')

    def send(self, user_id: str | int, message: NotifyMessage) -> None:
        # Здесь может быть интеграция через requests к sendMessage или reuse PTB
        logger.info(f"Notify TG -> {user_id}: {message.get('text', '')[:120]}")
