"""
Django management команда для тестирования AI системы
"""

import requests
import json
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from core.container import Container


class Command(BaseCommand):
    help = 'Тестирует AI систему ExamFlow'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='http://localhost:8000',
            help='URL для тестирования (по умолчанию: http://localhost:8000)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🧪 ТЕСТИРОВАНИЕ AI СИСТЕМЫ EXAMFLOW")
        self.stdout.write("=" * 50)
        
        base_url = options['url']
        
        # 1. Тестируем конфигурацию
        self.test_configuration()
        
        # 2. Тестируем прямое обращение к AI
        self.test_direct_ai()
        
        # 3. Тестируем веб интерфейс
        self.test_web_interface(base_url)
        
        # 4. Тестируем Telegram бот
        self.test_telegram_bot()
        
        self.stdout.write("\n✅ Тестирование завершено")
    
    def test_configuration(self):
        """Проверяет конфигурацию AI"""
        self.stdout.write("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
        
        # Проверяем API ключи
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        if gemini_key and gemini_key != '<set-in-env>':
            self.stdout.write("  ✅ GEMINI_API_KEY настроен")
        else:
            self.stdout.write("  ❌ GEMINI_API_KEY не настроен")
        
        # Проверяем Container
        try:
            ai_orchestrator = Container.ai_orchestrator()
            if ai_orchestrator:
                self.stdout.write("  ✅ AI Orchestrator доступен")
            else:
                self.stdout.write("  ❌ AI Orchestrator недоступен")
        except Exception as e:
            self.stdout.write(f"  ❌ Ошибка Container: {e}")
    
    def test_direct_ai(self):
        """Тестирует прямое обращение к AI"""
        self.stdout.write("\n🤖 ТЕСТИРОВАНИЕ ПРЯМОГО AI:")
        
        try:
            ai_orchestrator = Container.ai_orchestrator()
            
            # Тестовые запросы
            test_queries = [
                "Привет! Как дела?",
                "Что такое производная?",
                "Объясни квадратные уравнения"
            ]
            
            for i, query in enumerate(test_queries, 1):
                try:
                    response = ai_orchestrator.process_query(query)  # type: ignore
                    if response and isinstance(response, dict) and 'answer' in response:
                        answer_length = len(response['answer'])
                        self.stdout.write(f"  ✅ Запрос {i}: получен ответ ({answer_length} символов)")
                    else:
                        self.stdout.write(f"  ❌ Запрос {i}: некорректный ответ")
                except Exception as e:
                    self.stdout.write(f"  ❌ Запрос {i}: ошибка {e}")
                    
        except Exception as e:
            self.stdout.write(f"  ❌ Ошибка прямого AI: {e}")
    
    def test_web_interface(self, base_url):
        """Тестирует веб интерфейс"""
        self.stdout.write("\n🌐 ТЕСТИРОВАНИЕ ВЕБ ИНТЕРФЕЙСА:")
        
        try:
            session = requests.Session()
            
            # Загружаем главную страницу
            response = session.get(base_url, timeout=10)
            
            if response.status_code == 200:
                self.stdout.write(f"  ✅ Сайт доступен (HTTP {response.status_code})")
                
                # Проверяем AI элементы
                html = response.text
                ai_elements = [
                    ("AI интерфейс", "ai-interface"),
                    ("AI инпут", "ai-input"),
                    ("AI кнопка", "ai-send-btn"),
                    ("JavaScript", "examflow-main.js"),
                ]
                
                for name, selector in ai_elements:
                    if selector in html:
                        self.stdout.write(f"  ✅ {name} найден")
                    else:
                        self.stdout.write(f"  ❌ {name} отсутствует")
                
                # Тестируем API через веб
                csrf_match = re.search(r'csrfmiddlewaretoken[^>]*value=["\']([^"\']*)["\']', html)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    self.stdout.write("  ✅ CSRF токен получен")
                    
                    # Тестируем AI API
                    try:
                        ai_response = session.post(
                            f"{base_url}/ai/api/",
                            json={'prompt': 'Тест веб API'},
                            headers={
                                'X-CSRFToken': csrf_token,
                                'Content-Type': 'application/json'
                            },
                            timeout=30
                        )
                        
                        if ai_response.status_code == 200:
                            data = ai_response.json()
                            if 'answer' in data and data['answer']:
                                self.stdout.write("  ✅ AI API работает")
                            else:
                                self.stdout.write("  ❌ AI API: пустой ответ")
                        else:
                            self.stdout.write(f"  ❌ AI API: HTTP {ai_response.status_code}")
                            
                    except Exception as e:
                        self.stdout.write(f"  ❌ AI API ошибка: {e}")
                else:
                    self.stdout.write("  ❌ CSRF токен не найден")
            else:
                self.stdout.write(f"  ❌ Сайт недоступен (HTTP {response.status_code})")
                
        except Exception as e:
            self.stdout.write(f"  ❌ Ошибка веб интерфейса: {e}")
    
    def test_telegram_bot(self):
        """Тестирует Telegram бот"""
        self.stdout.write("\n📱 ТЕСТИРОВАНИЕ TELEGRAM БОТА:")
        
        try:
            from telegram_bot.services.ai_dialogs import get_ai_response
            
            # Тестируем AI сервис бота
            test_queries = [
                "Привет из бота!",
                "Что такое интеграл?",
                "Помоги с задачей"
            ]
            
            for i, query in enumerate(test_queries, 1):
                try:
                    response = get_ai_response(query, task_type='chat')
                    if response and not response.startswith('Ошибка'):
                        self.stdout.write(f"  ✅ Бот запрос {i}: получен ответ")
                    else:
                        self.stdout.write(f"  ❌ Бот запрос {i}: {response or 'пустой ответ'}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Бот запрос {i}: ошибка {e}")
                    
        except ImportError as e:
            self.stdout.write(f"  ❌ Импорт бот модулей: {e}")
        except Exception as e:
            self.stdout.write(f"  ❌ Ошибка Telegram бота: {e}")
