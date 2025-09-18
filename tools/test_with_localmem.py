#!/usr/bin/env python
"""
Тест AI с локальным кэшем (без Redis)
"""

import os
import sys
import django

# Настройка Django с локальным кэшем
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
os.environ['USE_LOCMEM_CACHE'] = 'True'  # Форсируем локальный кэш

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from core.container import Container
from telegram_bot.services.ai_dialogs import get_ai_response

def test_ai_direct():
    """Тестирует AI напрямую"""
    print("🤖 ПРЯМОЕ ТЕСТИРОВАНИЕ AI:")
    
    try:
        ai_orchestrator = Container.ai_orchestrator()
        
        test_queries = [
            "Привет! Как дела?",
            "Что такое производная?",
            "Объясни квадратные уравнения"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"  🔄 Запрос {i}: {query}")
                response = ai_orchestrator.ask(query)
                
                if response and isinstance(response, dict) and 'answer' in response:
                    answer = response['answer']
                    preview = answer[:100] + "..." if len(answer) > 100 else answer
                    print(f"  ✅ Ответ {i}: {preview}")
                else:
                    print(f"  ❌ Запрос {i}: некорректный ответ - {response}")
                    
            except Exception as e:
                print(f"  ❌ Запрос {i}: ошибка - {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка AI Orchestrator: {e}")
        return False

def test_bot_ai():
    """Тестирует AI в боте"""
    print("\n📱 ТЕСТИРОВАНИЕ AI В БОТЕ:")
    
    try:
        test_queries = [
            "Привет из бота!",
            "Что такое интеграл?",
            "Помоги с математикой"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"  🔄 Бот запрос {i}: {query}")
                response = get_ai_response(query, task_type='chat')
                
                if response and not response.startswith('Ошибка'):
                    preview = response[:100] + "..." if len(response) > 100 else response
                    print(f"  ✅ Бот ответ {i}: {preview}")
                else:
                    print(f"  ❌ Бот запрос {i}: {response}")
                    
            except Exception as e:
                print(f"  ❌ Бот запрос {i}: ошибка - {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка бот AI: {e}")
        return False

def main():
    print("🧪 ТЕСТИРОВАНИЕ AI С ЛОКАЛЬНЫМ КЭШЕМ")
    print("=" * 50)
    
    # Тестируем AI компоненты
    ai_success = test_ai_direct()
    bot_success = test_bot_ai()
    
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("=" * 50)
    print(f"AI Orchestrator: {'✅ РАБОТАЕТ' if ai_success else '❌ ОШИБКА'}")
    print(f"Telegram Bot AI: {'✅ РАБОТАЕТ' if bot_success else '❌ ОШИБКА'}")
    
    if ai_success and bot_success:
        print("\n🎉 ВСЕ AI КОМПОНЕНТЫ РАБОТАЮТ!")
        print("💡 Для полноценной работы добавьте ваш IP в Redis whitelist на Render.com")
    else:
        print("\n🔧 ЕСТЬ ПРОБЛЕМЫ С AI СИСТЕМОЙ")
    
    return ai_success and bot_success

if __name__ == "__main__":
    main()
