from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    """
    Конфигурация модуля Telegram бота

    Этот модуль отвечает за:
    - Обработку команд Telegram бота
    - Webhook интеграцию с Telegram
    - Отправку уведомлений пользователям
    - Синхронизацию данных между сайтом и ботом
    """
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'telegram_bot'
    verbose_name = 'Telegram Бот'
