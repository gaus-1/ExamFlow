#!/usr/bin/env python
"""
Тестовый скрипт для проверки ИИ модуля
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from ai.services import AiService
from ai.models import AiProvider, AiLimit

def test_ai_service():
    """Тестируем ИИ сервис"""
    print("🔍 Тестирование ИИ модуля...")
    
    try:
        # Проверяем модели
        print("1. Проверка моделей...")
        providers_count = AiProvider.objects.count() # type: ignore
        print(f"   Провайдеров в БД: {providers_count}")
        
        limits_count = AiLimit.objects.count() # type: ignore
        print(f"   Лимитов в БД: {limits_count}")
        
        # Создаём тестовый провайдер если нет
        if providers_count == 0:
            print("   Создаём тестовый провайдер...")
            provider = AiProvider.objects.create( # type: ignore
                name="Local Test",
                provider_type="fallback",
                is_active=True,
                priority=100
            )
            print(f"   Создан провайдер: {provider}")
        
        # Тестируем сервис
        print("2. Тестирование ИИ сервиса...")
        ai_service = AiService()
        print(f"   Сервис создан: {ai_service}")
        
        # Тестируем простой запрос
        print("3. Тестирование запроса...")
        result = ai_service.ask("Привет! Как дела?")
        print(f"   Результат: {result}")
        
        if 'error' in result:
            print(f"   ❌ Ошибка: {result['error']}")
        else:
            print(f"   ✅ Успех: {result.get('response', '')[:100]}...")
            print(f"   Провайдер: {result.get('provider', 'unknown')}")
            print(f"   Токены: {result.get('tokens_used', 0)}")
        
        print("🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_service()
