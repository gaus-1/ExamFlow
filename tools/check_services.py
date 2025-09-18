#!/usr/bin/env python3
"""
🔍 Скрипт проверки статуса всех сервисов ExamFlow
Проверяет: Django сервер, бота, базу данных, статические файлы
"""

import os
import sys
import django
import requests
import subprocess
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402

def check_django_server():
    """Проверка Django сервера"""
    print("🌐 Проверка Django сервера...")
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code == 200:
            print("✅ Django сервер работает (код: 200)")
            return True
        else:
            print("⚠️ Django сервер отвечает с кодом: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print("❌ Django сервер недоступен: {e}")
        return False

def check_database():
    """Проверка базы данных"""
    print("🗄️ Проверка базы данных...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        print("✅ База данных доступна")
        return True
    except Exception as e:
        print("❌ Ошибка базы данных: {e}")
        return False

def check_static_files():
    """Проверка статических файлов"""
    print("📁 Проверка статических файлов...")
    static_dir = Path(settings.STATIC_ROOT or 'staticfiles')
    if static_dir.exists():
        css_files = list(static_dir.rglob('*.css'))
        js_files = list(static_dir.rglob('*.js'))
        print("✅ Статические файлы найдены: {len(css_files)} CSS, {len(js_files)} JS")
        return True
    else:
        print("❌ Папка со статическими файлами не найдена")
        return False

def check_models():
    """Проверка моделей Django"""
    print("📊 Проверка моделей...")
    try:
        from learning.models import Subject, Task, Topic

        subjects_count = Subject.objects.count()  # type: ignore
        topics_count = Topic.objects.count()  # type: ignore
        tasks_count = Task.objects.count()  # type: ignore

        print("✅ Модели работают:")
        print("   📚 Предметов: {subjects_count}")
        print("   🎯 Тем: {topics_count}")
        print("   📝 Заданий: {tasks_count}")
        return True
    except Exception as e:
        print("❌ Ошибка моделей: {e}")
        return False

def check_telegram_bot():
    """Проверка Telegram бота"""
    print("🤖 Проверка Telegram бота...")
    try:
        # Проверяем, что процесс бота запущен
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                              capture_output=True, text=True, shell=True)
        if 'python.exe' in result.stdout:
            print("✅ Python процессы запущены (возможно, бот работает)")
            return True
        else:
            print("⚠️ Python процессы не найдены")
            return False
    except Exception as e:
        print("❌ Ошибка проверки процессов: {e}")
        return False

def check_github_actions():
    """Проверка GitHub Actions"""
    print("🔄 Проверка GitHub Actions...")
    workflows_dir = Path('.github/workflows')
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob('*.yml'))
        print("✅ Найдено {len(workflow_files)} workflow файлов:")
        for workflow in workflow_files:
            print("   📄 {workflow.name}")
        return True
    else:
        print("❌ Папка .github/workflows не найдена")
        return False

def main():
    """Основная функция проверки"""
    print("🚀 Проверка статуса сервисов ExamFlow")
    print("=" * 50)

    checks = [
        check_django_server,
        check_database,
        check_static_files,
        check_models,
        check_telegram_bot,
        check_github_actions
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print("❌ Ошибка в проверке {check.__name__}: {e}")
            results.append(False)
        print()

    # Итоговый отчет
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    passed = sum(results)
    total = len(results)

    print("✅ Успешно: {passed}/{total}")
    print("❌ Ошибок: {total - passed}")

    if passed == total:
        print("🎉 Все сервисы работают корректно!")
    elif passed >= total * 0.8:
        print("⚠️ Большинство сервисов работают, есть незначительные проблемы")
    else:
        print("🚨 Критические проблемы с сервисами!")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
