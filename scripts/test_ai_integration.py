#!/usr/bin/env python
"""
Комплексное тестирование ИИ интеграции ExamFlow
Проверяет работу ИИ на сайте, в API и в Telegram боте
"""

import os
import sys
import requests
import json
import re
import time
import asyncio
from typing import Optional

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')

try:
    import django
    django.setup()
    
    from ai.orchestrator import AIOrchestrator
    from ai.clients.gemini_client import GeminiClient
    from core.container import Container
    from django.conf import settings
except ImportError as e:
    print(f"⚠️  Django не настроен: {e}")
    AIOrchestrator = None
    GeminiClient = None
    Container = None
    settings = None

class AITester:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Записывает результат теста"""
        self.results.append((test_name, success, details))
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}: {details}")
    
    def test_website_ai_interface(self):
        """Тестирует AI интерфейс на сайте"""
        print("\n🌐 ТЕСТИРОВАНИЕ AI ИНТЕРФЕЙСА НА САЙТЕ:")
        
        try:
            # Загружаем главную страницу
            response = self.session.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                self.log_result("Загрузка сайта", False, f"HTTP {response.status_code}")
                return
            
            self.log_result("Загрузка сайта", True, f"HTTP {response.status_code}")
            
            # Проверяем AI элементы
            html = response.text
            ai_elements = [
                ("AI интерфейс", "ai-interface"),
                ("AI инпут", "ai-input"),
                ("AI кнопка", "ai-send-btn"),
                ("AI предложения", "ai-suggestion"),
                ("AI чат", "ai-chat"),
                ("AI виджет", "ai-widget"),
            ]
            
            for name, selector in ai_elements:
                found = selector in html
                self.log_result(name, found, "найден" if found else "отсутствует")
            
            # Проверяем JavaScript
            js_found = "examflow-main.js" in html
            self.log_result("JavaScript", js_found, "загружен" if js_found else "отсутствует")
            
        except Exception as e:
            self.log_result("Сайт AI интерфейс", False, str(e))
    
    def test_ai_api_endpoint(self):
        """Тестирует AI API endpoint"""
        print("\n🔌 ТЕСТИРОВАНИЕ AI API:")
        
        try:
            # Получаем CSRF токен
            response = self.session.get(self.base_url)
            csrf_match = re.search(r'csrfmiddlewaretoken[^>]*value=["\']([^"\']*)["\']', response.text)
            
            if not csrf_match:
                self.log_result("CSRF токен", False, "не найден")
                return
            
            csrf_token = csrf_match.group(1)
            self.log_result("CSRF токен", True, "получен")
            
            # Тестируем простой запрос
            test_prompts = [
                "Привет! Как дела?",
                "Что такое производная?",
                "Как решать квадратные уравнения?"
            ]
            
            for i, prompt in enumerate(test_prompts, 1):
                try:
                    ai_response = self.session.post(
                        f"{self.base_url}/ai/api/",
                        json={'prompt': prompt},
                        headers={
                            'X-CSRFToken': csrf_token,
                            'Content-Type': 'application/json'
                        },
                        timeout=30
                    )
                    
                    if ai_response.status_code == 200:
                        try:
                            data = ai_response.json()
                            if 'answer' in data and data['answer']:
                                answer_preview = data['answer'][:50] + "..."
                                self.log_result(f"AI запрос {i}", True, f"ответ: {answer_preview}")
                            else:
                                self.log_result(f"AI запрос {i}", False, "пустой ответ")
                        except json.JSONDecodeError:
                            self.log_result(f"AI запрос {i}", False, "некорректный JSON")
                    else:
                        self.log_result(f"AI запрос {i}", False, f"HTTP {ai_response.status_code}")
                        
                except Exception as e:
                    self.log_result(f"AI запрос {i}", False, str(e))
                
                # Небольшая пауза между запросами
                time.sleep(1)
                
        except Exception as e:
            self.log_result("AI API", False, str(e))
    
    def test_direct_ai_components(self):
        """Тестирует AI компоненты напрямую"""
        print("\n⚙️  ТЕСТИРОВАНИЕ AI КОМПОНЕНТОВ:")
        
        if not Container:
            self.log_result("Django setup", False, "не настроен")
            return
        
        try:
            # Тестируем Container
            ai_orchestrator = Container.ai_orchestrator()
            if ai_orchestrator:
                self.log_result("AI Orchestrator", True, "создан через Container")
                
                # Тестируем прямой вызов
                try:
                    response = ai_orchestrator.process_query("Тест прямого вызова")  # type: ignore
                    if response and isinstance(response, dict) and 'answer' in response:
                        answer_preview = response['answer'][:50] + "..."
                        self.log_result("Прямой AI вызов", True, f"ответ: {answer_preview}")
                    else:
                        self.log_result("Прямой AI вызов", False, "некорректный ответ")
                except Exception as e:
                    self.log_result("Прямой AI вызов", False, str(e))
            else:
                self.log_result("AI Orchestrator", False, "не создан")
                
        except Exception as e:
            self.log_result("AI компоненты", False, str(e))
    
    def test_telegram_bot_ai(self):
        """Тестирует AI в Telegram боте"""
        print("\n🤖 ТЕСТИРОВАНИЕ AI В TELEGRAM БОТЕ:")
        
        try:
            # Импортируем модули бота
            from telegram_bot.services.ai_dialogs import get_ai_response
            
            # Тестируем AI сервис бота
            test_queries = [
                "Привет!",
                "Что такое интеграл?",
                "Помоги с математикой"
            ]
            
            for i, query in enumerate(test_queries, 1):
                try:
                    response = get_ai_response(query, task_type='chat')
                    if response and not response.startswith('Ошибка'):
                        preview = response[:50] + "..."
                        self.log_result(f"Бот AI запрос {i}", True, f"ответ: {preview}")
                    else:
                        self.log_result(f"Бот AI запрос {i}", False, response or "пустой ответ")
                except Exception as e:
                    self.log_result(f"Бот AI запрос {i}", False, str(e))
                
                time.sleep(0.5)
                
        except ImportError as e:
            self.log_result("Импорт бот модулей", False, str(e))
        except Exception as e:
            self.log_result("Telegram AI", False, str(e))
    
    def test_ai_configuration(self):
        """Проверяет конфигурацию AI"""
        print("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ AI:")
        
        try:
            if settings:
                # Проверяем наличие API ключей
                gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
                if gemini_key and gemini_key != '<set-in-env>':
                    self.log_result("GEMINI_API_KEY", True, "настроен")
                else:
                    self.log_result("GEMINI_API_KEY", False, "не настроен")
                
                # Проверяем другие настройки
                debug = getattr(settings, 'DEBUG', False)
                self.log_result("DEBUG режим", debug, "включен" if debug else "выключен")
                
            else:
                self.log_result("Django settings", False, "не доступны")
                
        except Exception as e:
            self.log_result("Конфигурация", False, str(e))
    
    def run_comprehensive_test(self):
        """Запускает полное тестирование"""
        print("🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ AI EXAMFLOW")
        print("=" * 60)
        
        # Запускаем все тесты
        self.test_ai_configuration()
        self.test_website_ai_interface()
        self.test_ai_api_endpoint()
        self.test_direct_ai_components()
        self.test_telegram_bot_ai()
        
        # Подводим итоги
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, details in self.results:
            status = "✅ ПРОШЁЛ" if success else "❌ ОШИБКА"
            print(f"{test_name:<25} | {status:<12} | {details}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📈 ИТОГО: {passed} прошли, {failed} ошибок")
        
        if failed == 0:
            print("🎉 ВСЕ AI КОМПОНЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
        elif failed <= 2:
            print("⚠️  Есть незначительные проблемы, но основная функциональность работает.")
        else:
            print("🔧 Требуются серьезные исправления AI системы.")
        
        return failed <= 2

def main():
    """Главная функция"""
    tester = AITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🚀 AI система готова к использованию!")
    else:
        print("\n🔧 Необходимо исправить проблемы с AI.")
    
    return success

if __name__ == "__main__":
    main()
