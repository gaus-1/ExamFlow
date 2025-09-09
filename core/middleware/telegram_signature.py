from __future__ import annotations

import hmac
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class TelegramWebhookSignatureMiddleware(MiddlewareMixin):
    """Проверка подписи Telegram webhook по секрету (если задан TELEGRAM_WEBHOOK_SECRET).
    Обратимо: при пустом секрете пропускает запросы без валидации.
    """

    header_name = 'HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'

    def process_request(self, request: HttpRequest):  # type: ignore
        secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')
        if not secret:
            return None

        token = request.META.get(self.header_name)
        if not token:
            return HttpResponse('Forbidden', status=403)  # type: ignore

        # Сравниваем безопасно
        try:
            ok = hmac.compare_digest(token, secret)
        except Exception:
            ok = False
        if not ok:
            return HttpResponse('Forbidden', status=403)  # type: ignore
        return None


