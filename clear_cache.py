#!/usr/bin/env python
"""
Принудительная очистка кэша для Render
"""

import os

import django
from django.core.management import execute_from_command_line

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
django.setup()


def clear_all_cache():
    """Очищает весь кэш Django"""
    try:
        from django.core.cache import cache

        cache.clear()
        print("✅ Django кэш очищен")
    except Exception as e:
        print(f"❌ Ошибка очистки кэша: {e}")


def collect_static():
    """Собирает статические файлы заново"""
    try:
        execute_from_command_line(
            ["manage.py", "collectstatic", "--noinput", "--clear"]
        )
        print("✅ Статические файлы пересобраны")
    except Exception as e:
        print(f"❌ Ошибка сборки статики: {e}")


if __name__ == "__main__":
    print("🔧 ПРИНУДИТЕЛЬНАЯ ОЧИСТКА КЭША EXAMFLOW")
    print("=" * 50)

    clear_all_cache()
    collect_static()

    print("=" * 50)
    print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")
    print("🚀 Теперь перезапустите сервер на Render")
