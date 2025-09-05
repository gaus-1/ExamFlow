"""
URL-маршруты для модуля Telegram бота

Определяет пути для:
- Webhook от Telegram (/bot/webhook/)
- Панели управления (/bot/control/)
- API статуса (/bot/api/status/)
"""

from django.urls import path
from . import views

app_name = 'telegram_bot'

urlpatterns = [
    # Webhook для Telegram
    path('webhook/', views.telegram_webhook, name='webhook'),

    # Тестовая функция для проверки webhook
    path('test/', views.test_webhook, name='test_webhook'),  # type: ignore

    # Тест API бота
    path('test-api/', views.test_bot_api, name='test_bot_api'),  # type: ignore
    # Панель управления
    path('control/', views.bot_control_panel, name='control_panel'),

    # API
    path('api/status/', views.bot_api_status, name='api_status'),
]
