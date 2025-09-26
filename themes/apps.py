from django.apps import AppConfig


class ThemesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "themes"
    verbose_name = "Управление дизайнами"

    def ready(self):
        """Инициализация приложения при запуске Django"""
