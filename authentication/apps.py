from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Конфигурация модуля аутентификации
    
    Этот модуль отвечает за:
    - Регистрацию новых пользователей
    - Вход и выход из системы
    - Управление профилями пользователей
    - Восстановление паролей
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Аутентификация'
