#!/usr/bin/env python3
"""
Тест Gemini API для ExamFlow 2.0
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_gemini_api():
    """Тестирует подключение к Gemini API"""
    
    # Получаем API ключ
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCvi8Mm5paqqV-bakd2N897MgUEvJyWw44')
    
    if not api_key:
        print("❌ GEMINI_API_KEY не найден!")
        return False
    
    try:
        # Настраиваем API
        genai.configure(api_key=api_key)  # type: ignore
        
        # Создаем модель
        model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
        # Тестовый запрос
        prompt = """
        Ты - эксперт по подготовке к ЕГЭ в России. 
        Ответь кратко на вопрос: "Как решать квадратные уравнения?"
        
        Ответ должен быть структурированным и понятным для ученика.
        """
        
        print("🤖 Отправляю запрос к Gemini API...")
        
        # Получаем ответ
        response = model.generate_content(prompt)
        
        print("✅ Ответ получен успешно!")
        print("\n📝 Ответ Gemini:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с Gemini API: {e}")
        return False

def test_django_integration():
    """Тестирует интеграцию с Django"""
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        
        from ai.api import AIAssistantAPI
        
        print("✅ Django интеграция работает!")
        
        # Создаем экземпляр API
        api = AIAssistantAPI()
        
        # Тестируем генерацию ответа
        test_prompt = "Как решать логарифмы?"
        response = api.generate_ai_response(test_prompt)
        
        print("✅ AI API работает!")
        print(f"📝 Ответ: {response['answer'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Django интеграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование Gemini API для ExamFlow 2.0")
    print("=" * 60)
    
    # Тест 1: Прямое подключение к Gemini
    print("\n1️⃣ Тест прямого подключения к Gemini API")
    gemini_ok = test_gemini_api()
    
    # Тест 2: Интеграция с Django
    print("\n2️⃣ Тест интеграции с Django")
    django_ok = test_django_integration()
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   Gemini API: {'✅ РАБОТАЕТ' if gemini_ok else '❌ НЕ РАБОТАЕТ'}")
    print(f"   Django интеграция: {'✅ РАБОТАЕТ' if django_ok else '❌ НЕ РАБОТАЕТ'}")
    
    if gemini_ok and django_ok:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ExamFlow 2.0 готов к работе!")
    else:
        print("\n⚠️  Есть проблемы, требующие исправления.")
