#!/usr/bin/env python
"""
Инициализация ИИ модуля для продакшена ExamFlow
"""
import os
import sys
import django

def init_production_ai():
    """Инициализируем ИИ для продакшена"""
    print("🚀 Инициализация ИИ модуля для продакшена...")
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    django.setup()
    
    try:
        from ai.models import AiProvider, AiLimit
        from django.utils import timezone
        from datetime import timedelta
        
        print("✅ Django настроен")
        
        # Проверяем существующие данные
        providers_count = AiProvider.objects.count()
        limits_count = AiLimit.objects.count()
        
        print(f"📊 Текущее состояние:")
        print(f"   AI Providers: {providers_count}")
        print(f"   AI Limits: {limits_count}")
        
        if providers_count == 0:
            print("\n🔧 Создаем AI провайдеры для продакшена...")
            
            # Создаем базовые провайдеры
            providers_data = [
                {
                    'name': 'GigaChat',
                    'provider_type': 'gigachat',
                    'api_key': 'production_key_gigachat',
                    'is_active': True,
                    'daily_limit': 1000,
                    'priority': 1
                },
                {
                    'name': 'DeepSeek Chat',
                    'provider_type': 'deepseek',
                    'api_key': 'production_key_deepseek',
                    'is_active': True,
                    'daily_limit': 500,
                    'priority': 2
                },
                {
                    'name': 'Fallback',
                    'provider_type': 'fallback',
                    'api_key': 'production_key_fallback',
                    'is_active': False,
                    'daily_limit': 100,
                    'priority': 3
                }
            ]
            
            for provider_data in providers_data:
                provider = AiProvider.objects.create(**provider_data)
                print(f"   ✅ Создан провайдер: {provider.name}")
            
            print(f"\n🎉 Создано AI провайдеров: {AiProvider.objects.count()}")
        
        if limits_count == 0:
            print("\n🔧 Создаем лимиты для продакшена...")
            
            # Создаем лимиты для гостей
            guest_daily = AiLimit.objects.create(
                limit_type='daily',
                max_limit=10,
                reset_date=timezone.now() + timedelta(days=1)
            )
            print(f"   ✅ Создан дневной лимит: {guest_daily.max_limit}/день")
            
            guest_monthly = AiLimit.objects.create(
                limit_type='monthly',
                max_limit=100,
                reset_date=timezone.now() + timedelta(days=30)
            )
            print(f"   ✅ Создан месячный лимит: {guest_monthly.max_limit}/месяц")
            
            print(f"\n🎉 Создано AI лимитов: {AiLimit.objects.count()}")
        
        print(f"\n🎉 ИИ модуль для продакшена готов!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_production_ai()
