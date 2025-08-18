import logging
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def get_bot_status():
    """Минимальный статус бота для панели (вебхук-режим)."""
    return {'status': 'running'}


def bot_status_view(request):
    status = get_bot_status()
    return HttpResponse(f"Bot status: {status['status']}")


def start_bot_view(request):
    return HttpResponse("Webhook mode: bot runs under web service")


def restart_bot_view(request):
    return HttpResponse("Webhook mode: restart not applicable")


def stop_bot_view(request):
    return HttpResponse("Webhook mode: stop not applicable")