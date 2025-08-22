#!/usr/bin/env python
"""
Диагностика AI провайдеров
"""
import os
import sys
import django

def debug_ai_providers():
    """Диагностируем AI провайдеры"""
    print("🔍 Диагностика AI провайдеров ExamFlow")
    print("=" * 50)
    
    try:
        # Настройка Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        print("✅ Django настроен")
        
        # Проверяем переменные окружения
        print("\n📋 Переменные окружения:")
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        huggingface_key = os.getenv('HUGGINGFACE_API_KEY')
        print(f"   DEEPSEEK_API_KEY: {'✅ Есть' if deepseek_key else '❌ Нет'}")
        print(f"   HUGGINGFACE_API_KEY: {'✅ Есть' if huggingface_key else '❌ Нет'}")
        
        # Проверяем модуль requests
        try:
            import requests
            print(f"   requests: ✅ Установлен (версия {requests.__version__})")
        except ImportError:
            print("   requests: ❌ НЕ установлен")
            return
        
        # Тестируем провайдеры
        print("\n🤖 Тестирование провайдеров:")
        
        from ai.services import DeepSeekProvider, SmartLocalProvider
        
        # DeepSeek
        print("\n📡 DeepSeek Provider:")
        deepseek = DeepSeekProvider()
        print(f"   Доступен: {'✅ Да' if deepseek.is_available() else '❌ Нет'}")
        if deepseek.is_available():
            print("   API ключ: ✅ Настроен")
            print("   URL: ✅ Настроен")
        else:
            print("   API ключ: ❌ Отсутствует или неверный")
        
        # SmartLocal
        print("\n📡 SmartLocal Provider:")
        smartlocal = SmartLocalProvider()
        print(f"   Доступен: {'✅ Да' if smartlocal.is_available() else '❌ Нет'}")
        if smartlocal.is_available():
            print("   Работает: ✅ Без API ключей")
            print("   Стоимость: 🆓 Бесплатно")
        else:
            print("   Работает: ❌ Ошибка")
        
        # Тестируем AiService
        print("\n🔧 Тестирование AiService:")
        from ai.services import AiService
        
        service = AiService()
        print("   ✅ AiService создан")
        
        # Проверяем порядок провайдеров
        print("\n📋 Порядок провайдеров в AiService:")
        for i, provider in enumerate(service.providers, 1):
            print(f"   {i}. {provider.name} - {'✅ Доступен' if provider.is_available() else '❌ Недоступен'}")
        
        # Тестируем запрос
        print("\n🧪 Тестирование запроса:")
        result = service.ask("привет")
        print(f"   Ответ: {result.get('response', 'Ошибка')[:100]}...")
        print(f"   Провайдер: {result.get('provider', 'Неизвестно')}")
        print(f"   Кэш: {result.get('cached', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_ai_providers()
    if success:
        print("\n🎉 Диагностика завершена успешно!")
    else:
        print("\n💥 Диагностика не удалась!")
