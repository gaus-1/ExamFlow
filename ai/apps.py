from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore
    name = 'ai'
    verbose_name = 'ИИ-ассистент'
    
    def ready(self):
        """Инициализация модуля при запуске Django"""
        try:
            # Импортируем сигналы
            import ai.signals  # type: ignore
        except ImportError:
            pass
