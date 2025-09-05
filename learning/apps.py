from django.apps import AppConfig


class LearningConfig(AppConfig):
    """
    Конфигурация модуля обучения

    Этот модуль отвечает за:
    - Управление предметами и темами
    - Работу с заданиями и их решение
    - Отслеживание прогресса пользователей
    - Систему достижений и рейтингов
    - Загрузку материалов с ФИПИ
    """
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'learning'
    verbose_name = 'Обучение'
