#!/usr/bin/env python3
"""
Тест RAG системы ExamFlow с Gemini API
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

print("🧪 Тестируем RAG систему ExamFlow...")

try:
    # Импортируем Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    
    import django
    django.setup()
    
    print("✅ Django настроен")
    
    # Тестируем AI сервис
    from ai.services import AiService
    
    print("✅ AI сервис импортирован")
    
    # Создаем экземпляр сервиса
    ai_service = AiService()
    
    print("✅ AI сервис создан")
    
    # Тестируем провайдеры
    providers = ai_service.providers
    print(f"✅ Загружено провайдеров: {len(providers)}")
    
    for provider in providers:
        print(f"   - {provider.name}: {'✅ Доступен' if provider.is_available() else '❌ Недоступен'}")
    
    # Тестируем простой запрос
    print("\n🤖 Тестируем простой запрос...")
    
    result = ai_service.ask("Объясни, что такое квадратное уравнение", task_type='task_explanation')
    
    if 'error' in result:
        print(f"❌ Ошибка: {result['error']}")
    else:
        print("✅ Запрос выполнен успешно!")
        print(f"🤖 Ответ: {result['response'][:200]}...")
        print(f"📊 Провайдер: {result['provider']}")
        print(f"🔢 Токены: {result['tokens_used']}")
    
    print("\n🎯 RAG система готова к работе!")
    
except Exception as e:
    print(f"❌ Ошибка при тестировании RAG системы: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("🎯 РЕЗУЛЬТАТ ТЕСТА RAG СИСТЕМЫ:")
print("="*50)
