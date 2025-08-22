#!/usr/bin/env python
"""
Инициализация базовых данных для ИИ модуля ExamFlow
"""
import os
import sys
import django

def init_ai():
    """Инициализируем базовые данные для ИИ"""
    print("🤖 Инициализация ИИ модуля ExamFlow...")
    
    # Устанавливаем переменные окружения
    os.environ['USE_SQLITE'] = 'False'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:Slava2402@localhost:5432/examflow_db'
    os.environ['DEBUG'] = 'True'
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    django.setup()
    
    try:
        from ai.models import AiProvider, AiLimit
        from django.contrib.auth.models import User
        
        print("✅ Django настроен")
        
        # Проверяем существующие данные
        providers_count = AiProvider.objects.count()
        limits_count = AiLimit.objects.count()
        
        print(f"📊 Текущее состояние:")
        print(f"   AI Providers: {providers_count}")
        print(f"   AI Limits: {limits_count}")
        
        if providers_count == 0:
            print("\n🔧 Создаем базовые AI провайдеры...")
            
            # Создаем базовые провайдеры
            providers_data = [
                {
                    'name': 'GigaChat',
                    'provider_type': 'gigachat',
                    'api_key': 'test_key_gigachat',
                    'is_active': True,
                    'daily_limit': 100,
                    'priority': 1
                },
                {
                    'name': 'DeepSeek Chat',
                    'provider_type': 'deepseek',
                    'api_key': 'test_key_deepseek',
                    'is_active': True,
                    'daily_limit': 50,
                    'priority': 2
                },
                {
                    'name': 'Fallback',
                    'provider_type': 'fallback',
                    'api_key': 'test_key_fallback',
                    'is_active': False,  # Отключен по умолчанию
                    'daily_limit': 10,
                    'priority': 3
                }
            ]
            
            for provider_data in providers_data:
                provider = AiProvider.objects.create(**provider_data)
                print(f"   ✅ Создан провайдер: {provider.name}")
            
            print(f"\n🎉 Создано AI провайдеров: {AiProvider.objects.count()}")
        
        if limits_count == 0:
            print("\n🔧 Создаем базовые лимиты...")
            
            from datetime import timedelta
            from django.utils import timezone
            
            # Создаем дневные лимиты для гостей
            guest_daily = AiLimit.objects.create(
                limit_type='daily',
                max_limit=5,
                reset_date=timezone.now() + timedelta(days=1)
            )
            print(f"   ✅ Создан дневной лимит для гостей: {guest_daily.max_limit}/день")
            
            # Создаем месячные лимиты для гостей
            guest_monthly = AiLimit.objects.create(
                limit_type='monthly',
                max_limit=50,
                reset_date=timezone.now() + timedelta(days=30)
            )
            print(f"   ✅ Создан месячный лимит для гостей: {guest_monthly.max_limit}/месяц")
            
            print(f"\n🎉 Создано AI лимитов: {AiLimit.objects.count()}")
        
        # Финальная проверка
        print(f"\n📊 Финальное состояние:")
        print(f"   AI Providers: {AiProvider.objects.count()}")
        print(f"   AI Limits: {AiLimit.objects.count()}")
        
        print("\n🎉 ИИ модуль инициализирован! Теперь помощник должен работать.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_ai()
