"""
Приложение Telegram аутентификации для ExamFlow
"""

from django.apps import AppConfig


class TelegramAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'telegram_auth'
    verbose_name = 'Telegram Authentication'
