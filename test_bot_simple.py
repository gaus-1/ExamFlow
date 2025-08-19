#!/usr/bin/env python3
"""
Простой тест для проверки работы Telegram бота ExamFlow
"""

import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def test_bot_config():
    """Проверяем конфигурацию бота"""
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ БОТА")
    print("=" * 50)
    
    # Проверяем токен
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if bot_token:
        print(f"✅ TELEGRAM_BOT_TOKEN: {bot_token[:10]}...")
    else:
        print("❌ TELEGRAM_BOT_TOKEN не настроен!")
        print("   Это основная причина, почему бот не работает")
    
    # Проверяем SITE_URL
    site_url = getattr(settings, 'SITE_URL', None)
    if site_url:
        print(f"✅ SITE_URL: {site_url}")
    else:
        print("❌ SITE_URL не настроен!")
    
    # Проверяем webhook URL
    if bot_token and site_url:
        webhook_url = f"{site_url}/bot/webhook/"
        print(f"✅ Webhook URL: {webhook_url}")
    else:
        print("❌ Webhook URL не может быть сформирован")
    
    print("\n🔧 ЧТО НУЖНО СДЕЛАТЬ:")
    print("1. Создать бота через @BotFather в Telegram")
    print("2. Получить токен бота")
    print("3. Добавить токен в переменные окружения Render")
    print("4. Настроить webhook командой: python manage.py setup_webhook")
    
    return bot_token is not None

def test_database():
    """Проверяем базу данных"""
    print("\n🗄️ ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        from core.models import Subject, Task
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        
        print(f"✅ Предметов в базе: {subjects_count}")
        print(f"✅ Заданий в базе: {tasks_count}")
        
        if subjects_count == 0:
            print("⚠️  База пуста! Запустите: python manage.py load_sample_data")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка базы данных: {str(e)}")
        return False

if __name__ == "__main__":
    print("🤖 ТЕСТ БОТА EXAMFLOW")
    print("=" * 50)
    
    bot_ok = test_bot_config()
    db_ok = test_database()
    
    print("\n📊 РЕЗУЛЬТАТ:")
    if bot_ok and db_ok:
        print("✅ Бот готов к работе!")
        print("🚀 Запустите: python manage.py setup_webhook")
    else:
        print("❌ Есть проблемы, которые нужно исправить")
        if not bot_ok:
            print("   - Настройте TELEGRAM_BOT_TOKEN")
        if not db_ok:
            print("   - Проверьте базу данных")
