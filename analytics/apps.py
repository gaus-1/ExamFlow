from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """
    Конфигурация модуля аналитики
    
    Этот модуль отвечает за:
    - Сбор и анализ статистики пользователей
    - Генерацию отчетов об активности
    - Мониторинг производительности системы
    - Анализ эффективности обучения
    """
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'analytics'
    verbose_name = 'Аналитика'
