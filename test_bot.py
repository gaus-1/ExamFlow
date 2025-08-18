#!/usr/bin/env python3
"""
Простой тест для проверки работы Telegram бота
"""

import os
import sys
import django
import asyncio
import requests
from datetime import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from django.conf import settings


def test_bot_token():
    """Тестирует токен бота"""
    print("🔍 Проверка токена бота...")
    
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не настроен в settings.py")
        return False
    
    if len(bot_token) < 40:
        print("❌ Токен бота слишком короткий")
        return False
    
    print("✅ Токен бота найден")
    return True


def test_bot_api():
    """Тестирует API бота"""
    print("🔍 Проверка API бота...")
    
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот отвечает: @{bot_info['username']}")
                print(f"   ID: {bot_info['id']}")
                print(f"   Имя: {bot_info['first_name']}")
                return True
            else:
                print(f"❌ API ошибка: {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка сети: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
        return False


def test_database():
    """Тестирует подключение к базе данных"""
    print("🔍 Проверка базы данных...")
    
    try:
        from core.models import Subject, Task
        
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        
        print(f"✅ База данных доступна")
        print(f"   Предметов: {subjects_count}")
        print(f"   Заданий: {tasks_count}")
        
        if subjects_count == 0:
            print("⚠️  Нет данных о предметах. Запустите: python manage.py load_sample_data")
        
        if tasks_count == 0:
            print("⚠️  Нет заданий. Запустите: python manage.py load_fipi_data")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {str(e)}")
        return False


def test_bot_import():
    """Тестирует импорт модуля бота"""
    print("🔍 Проверка импорта бота...")
    
    try:
        import bot.bot as bot_module
        print("✅ Модуль бота импортирован успешно")
        
        # Проверяем наличие основных функций
        required_functions = ['start', 'subjects_menu', 'main']
        for func_name in required_functions:
            if hasattr(bot_module, func_name):
                print(f"   ✅ {func_name}")
            else:
                print(f"   ❌ {func_name} - не найдена")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
        return False


def main():
    """Основная функция тестирования"""
    print("🤖 Тестирование ExamFlow Telegram Bot")
    print("=" * 50)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Токен бота", test_bot_token),
        ("API бота", test_bot_api),
        ("База данных", test_database),
        ("Импорт бота", test_bot_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        try:
            if test_func():
                passed += 1
                print("✅ ПРОЙДЕН\n")
            else:
                print("❌ ПРОВАЛЕН\n")
        except Exception as e:
            print(f"❌ ОШИБКА: {str(e)}\n")
    
    print("=" * 50)
    print(f"📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к работе.")
        print("\n🚀 Для запуска бота выполните:")
        print("   python manage.py runbot start --daemon")
    else:
        print("⚠️  Есть проблемы, которые нужно исправить.")
        print("\n🔧 Возможные решения:")
        print("   1. Проверьте TELEGRAM_BOT_TOKEN в .env")
        print("   2. Запустите: python manage.py migrate")
        print("   3. Загрузите данные: python manage.py load_sample_data")
        print("   4. Проверьте интернет-соединение")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
