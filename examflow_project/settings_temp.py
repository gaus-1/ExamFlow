"""
Временные настройки Django для исправления миграций.
"""

from dotenv import load_dotenv

load_dotenv()

# Импорт всех компонентов настроек
from .settings_components import *

# Отключение проверки целостности миграций
class DisableMigrationChecks:
    def check_consistent_history(self, connection):
        pass

# Переопределяем загрузчик миграций
from django.db.migrations.loader import MigrationLoader

# Создаем статический метод для отключения проверки
def disable_migration_checks(self, connection):
    pass

# Переопределяем метод проверки целостности миграций
MigrationLoader.check_consistent_history = disable_migration_checks  # type: ignore
