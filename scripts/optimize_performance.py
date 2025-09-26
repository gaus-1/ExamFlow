#!/usr/bin/env python3
"""
Скрипт для оптимизации производительности
"""

import subprocess
import sys
from pathlib import Path


def install_performance_tools():
    """Устанавливает инструменты для оптимизации"""
    print("⚡ Устанавливаем инструменты производительности...")

    tools = [
        "django-compressor",
        "Pillow",
        "django-debug-toolbar",
        "memory-profiler",
        "django-extensions",
    ]

    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True)
            print("✅ {tool} установлен")
        except subprocess.CalledProcessError:
            print("❌ Ошибка установки {tool}")


def optimize_static_files():
    """Оптимизирует статические файлы"""
    print("📁 Оптимизируем статические файлы...")

    settings_file = Path("examflow_project/settings.py")
    if not settings_file.exists():
        print("❌ Файл settings.py не найден")
        return

    # Читаем настройки
    with open(settings_file, encoding="utf-8") as f:
        content = f.read()

    # Добавляем настройки сжатия
    compression_config = """
# Сжатие статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Настройки сжатия
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
    ]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
    ]

# Кэширование статики
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ]

# Настройки WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
"""

    if "STATICFILES_STORAGE" not in content:
        content = content.replace(
            "STATICFILES_DIRS = [", compression_config + "\nSTATICFILES_DIRS = ["
        )

        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Настройки сжатия добавлены")
    else:
        print("✅ Настройки сжатия уже существуют")


def add_lazy_loading():
    """Добавляет lazy loading для изображений"""
    print("🖼️ Добавляем lazy loading...")

    # Обновляем base.html
    base_template = Path("templates/base.html")
    if base_template.exists():
        with open(base_template, encoding="utf-8") as f:
            content = f.read()

        # Добавляем lazy loading к изображениям
        content = content.replace("<img src=", '<img loading="lazy" src=')

        with open(base_template, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Lazy loading добавлен")
    else:
        print("⚠️ Шаблон base.html не найден")


def optimize_images():
    """Оптимизирует изображения"""
    print("🖼️ Оптимизируем изображения...")

    # Создаем скрипт оптимизации изображений
    image_optimizer = Path("core/utils/image_optimizer.py")
    image_optimizer.parent.mkdir(parents=True, exist_ok=True)

    optimizer_content = '''"""
Утилиты для оптимизации изображений
"""

import os
from PIL import Image
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def optimize_image(image_path: str, max_width: int = 800, quality: int = 85) -> str:
    """
    Оптимизирует изображение для веб

    Args:
        image_path: Путь к изображению
        max_width: Максимальная ширина
        quality: Качество сжатия (1-100)

    Returns:
        Путь к оптимизированному изображению
    """
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Изменяем размер если нужно
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Создаем WebP версию
            output_path = str(Path(image_path).with_suffix('.webp'))
            img.save(output_path, 'WebP', quality=quality, optimize=True)

            logger.info("Изображение оптимизировано: {output_path}")
            return output_path

    except Exception as e:
        logger.error("Ошибка оптимизации изображения {image_path}: {e}")
        return image_path

def optimize_all_images(static_dir: str = 'static/images'):
    """
    Оптимизирует все изображения в директории

    Args:
        static_dir: Директория со статическими файлами
    """
    static_path = Path(static_dir)
    if not static_path.exists():
        logger.warning("Директория {static_dir} не найдена")
        return

    image_extensions = {'.png', '.jpg', '.jpeg', '.gi', '.bmp'}

    for file_path in static_path.rglob('*'):
        if file_path.suffix.lower() in image_extensions:
            optimize_image(str(file_path))

if __name__ == "__main__":
    optimize_all_images()
'''

    with open(image_optimizer, "w", encoding="utf-8") as f:
        f.write(optimizer_content)

    print("✅ Скрипт оптимизации изображений создан")


def add_caching():
    """Добавляет кэширование"""
    print("💾 Настраиваем кэширование...")

    settings_file = Path("examflow_project/settings.py")
    if not settings_file.exists():
        print("❌ Файл settings.py не найден")
        return

    with open(settings_file, encoding="utf-8") as f:
        content = f.read()

    # Добавляем настройки кэширования
    cache_config = """
# Настройки кэширования
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'examflow',
        'TIMEOUT': 300,  # 5 минут по умолчанию
    }
}

# Кэширование сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Кэширование статики
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
"""

    if "CACHES = {" not in content:
        content = content.replace(
            "INSTALLED_APPS = [", cache_config + "\nINSTALLED_APPS = ["
        )

        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Настройки кэширования добавлены")
    else:
        print("✅ Настройки кэширования уже существуют")


def add_database_optimization():
    """Добавляет оптимизацию базы данных"""
    print("🗄️ Оптимизируем базу данных...")

    # Создаем management команду для оптимизации БД
    management_dir = Path("core/management/commands")
    management_dir.mkdir(parents=True, exist_ok=True)

    optimize_db_file = management_dir / "optimize_database.py"

    optimize_content = '''"""
Команда для оптимизации базы данных
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Оптимизирует базу данных'

    def handle(self, *args, **options):
        self.stdout.write('🗄️ Начинаем оптимизацию базы данных...')

        with connection.cursor() as cursor:
            # Анализируем таблицы
            cursor.execute("ANALYZE;")
            self.stdout.write('✅ Анализ таблиц завершен')

            # Создаем индексы для часто используемых полей
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_fipi_data_subject ON core_fipidata(subject);",
                "CREATE INDEX IF NOT EXISTS idx_fipi_data_processed ON core_fipidata(is_processed);",
                "CREATE INDEX IF NOT EXISTS idx_data_chunk_subject ON core_datachunk(subject);",
                "CREATE INDEX IF NOT EXISTS idx_data_chunk_fipi_data ON core_datachunk(fipi_data_id);",
                "CREATE INDEX IF NOT EXISTS idx_unified_profile_user ON core_unifiedprofile(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_user ON core_userprogress(user_id);",
            ]

            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    self.stdout.write('✅ Индекс создан: {index_sql.split()[5]}')
                except Exception as e:
                    self.stdout.write('⚠️ Ошибка создания индекса: {e}')

        # Собираем статистику
        call_command('collectstatic', '--noinput')
        self.stdout.write('✅ Статические файлы собраны')

        self.stdout.write('🎉 Оптимизация базы данных завершена!')
'''

    with open(optimize_db_file, "w", encoding="utf-8") as f:
        f.write(optimize_content)

    print("✅ Команда оптимизации БД создана")


def create_performance_monitor():
    """Создает мониторинг производительности"""
    print("📊 Создаем мониторинг производительности...")

    monitor_file = Path("core/utils/performance_monitor.py")
    monitor_file.parent.mkdir(parents=True, exist_ok=True)

    monitor_content = '''"""
Мониторинг производительности
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger(__name__)

def monitor_performance(func_name: str = None):
    """
    Декоратор для мониторинга производительности функций

    Args:
        func_name: Имя функции для логирования
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_queries = len(connection.queries)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                end_queries = len(connection.queries)

                execution_time = end_time - start_time
                query_count = end_queries - start_queries

                name = func_name or func.__name__

                logger.info("Performance: {name} - {execution_time:.3f}s, {query_count} queries")

                # Кэшируем медленные операции
                if execution_time > 1.0:
                    logger.warning("Slow operation: {name} took {execution_time:.3f}s")

        return wrapper
    return decorator

def get_performance_stats():
    """
    Возвращает статистику производительности

    Returns:
        Словарь со статистикой
    """
    stats = {
        'cache_hits': cache.get('cache_hits', 0),
        'cache_misses': cache.get('cache_misses', 0),
        'total_queries': len(connection.queries),
        'slow_queries': len([q for q in connection.queries if float(q['time']) > 0.1]),
    }

    return stats

def log_slow_queries():
    """Логирует медленные запросы"""
    slow_queries = [q for q in connection.queries if float(q['time']) > 0.1]

    if slow_queries:
        logger.warning("Found {len(slow_queries)} slow queries:")
        for query in slow_queries:
            logger.warning("  {query['time']}s: {query['sql']}")
'''

    with open(monitor_file, "w", encoding="utf-8") as f:
        f.write(monitor_content)

    print("✅ Мониторинг производительности создан")


def run_performance_tests():
    """Запускает тесты производительности"""
    print("🧪 Запускаем тесты производительности...")

    # Создаем простой тест производительности
    test_file = Path("tests/test_performance.py")
    test_file.parent.mkdir(parents=True, exist_ok=True)

    test_content = '''"""
Тесты производительности
"""

import time
from django.test import TestCase, Client
from django.urls import reverse

class PerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_load_time(self):
        """Тест времени загрузки главной страницы"""
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # Менее 2 секунд

    def test_ai_api_response_time(self):
        """Тест времени ответа AI API"""
        start_time = time.time()
        response = self.client.post('/ai/chat/', {
            'prompt': 'Test question'
        }, content_type='application/json')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 5.0)  # Менее 5 секунд
'''

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    print("✅ Тесты производительности созданы")


def main():
    """Основная функция"""
    print("🚀 Начинаем оптимизацию производительности...")

    # Устанавливаем инструменты
    install_performance_tools()

    # Оптимизируем статические файлы
    optimize_static_files()

    # Добавляем lazy loading
    add_lazy_loading()

    # Оптимизируем изображения
    optimize_images()

    # Настраиваем кэширование
    add_caching()

    # Оптимизируем БД
    add_database_optimization()

    # Создаем мониторинг
    create_performance_monitor()

    # Создаем тесты
    run_performance_tests()

    print("🎉 Оптимизация производительности завершена!")
    print("📋 Следующие шаги:")
    print("1. Запустите: python manage.py optimize_database")
    print("2. Запустите: python manage.py collectstatic")
    print("3. Протестируйте производительность")
    print("4. Проверьте логи на медленные операции")


if __name__ == "__main__":
    main()
