from django.utils.deprecation import MiddlewareMixin  # type: ignore
from django.http import HttpResponse  # type: ignore
from .tasks import start_bot

class AutoStartBotMiddleware(MiddlewareMixin):
    """Middleware для автоматического запуска Telegram-бота"""
    
    def process_request(self, request):
        # Запускаем бота при первом запросе к сайту
        start_bot()
        return None

    def process_response(self, request, response):
        return response
