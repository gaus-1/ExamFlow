#!/usr/bin/env python3
"""
Django Management команда для полного тестирования AI системы
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import django
import requests
import json
import time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from core.container import Container
from learning.models import Subject, Task
from telegram_auth.models import TelegramUser


class Command(BaseCommand):
    help = 'Полное тестирование AI системы'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ AI СИСТЕМЫ'))  # type: ignore
        self.stdout.write('=' * 60)
        
        # 1. Тест AI Orchestrator напрямую
        self.test_ai_orchestrator()
        
        # 2. Тест базы данных
        self.test_database()
        
        # 3. Тест Container
        self.test_container()
        
        # 4. Итоговый отчет
        self.final_report()

    def test_ai_orchestrator(self):
        """Тестирует AI Orchestrator напрямую"""
        self.stdout.write('\n🤖 ТЕСТ AI ORCHESTRATOR:')
        
        try:
            ai_orchestrator = Container.ai_orchestrator()
            
            test_prompts = [
                "Привет, как дела?",
                "Объясни теорему Пифагора",
                "Помоги решить уравнение x² + 5x + 6 = 0"
            ]
            
            for i, prompt in enumerate(test_prompts, 1):
                self.stdout.write(f'\n  📝 Тест {i}: {prompt}')
                
                start_time = time.time()
                try:
                    response = ai_orchestrator.ask(prompt)
                    end_time = time.time()
                    
                    if isinstance(response, dict) and 'answer' in response:
                        answer = response['answer'][:100] + '...' if len(response['answer']) > 100 else response['answer']
                        self.stdout.write(f'  ✅ Ответ получен за {end_time - start_time:.2f}с: {answer}')
                    else:
                        self.stdout.write(f'  ⚠️ Неожиданный формат ответа: {type(response)}')
                        
                except Exception as e:
                    self.stdout.write(f'  ❌ Ошибка AI: {str(e)}')
                    
        except Exception as e:
            self.stdout.write(f'❌ Ошибка создания AI Orchestrator: {str(e)}')

    def test_database(self):
        """Тестирует базу данных"""
        self.stdout.write('\n🗄️ ТЕСТ БАЗЫ ДАННЫХ:')
        
        try:
            # Тест предметов
            subjects = Subject.objects.all()  # type: ignore
            self.stdout.write(f'  ✅ Предметов в БД: {subjects.count()}')
            
            # Тест задач
            tasks = Task.objects.all()  # type: ignore
            self.stdout.write(f'  ✅ Задач в БД: {tasks.count()}')
            
            # Тест пользователей
            users = TelegramUser.objects.all()  # type: ignore
            self.stdout.write(f'  ✅ Пользователей в БД: {users.count()}')
            
            if subjects.count() == 0:
                self.stdout.write('  ⚠️ Нет предметов - запустите load_sample_data')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка БД: {str(e)}')

    def test_container(self):
        """Тестирует Container"""
        self.stdout.write('\n📦 ТЕСТ CONTAINER:')
        
        try:
            # Тест AI Orchestrator
            ai = Container.ai_orchestrator()  # type: ignore
            self.stdout.write('  ✅ AI Orchestrator создан')
            
            # Тест Notifier
            notifier = Container.notifier()  # type: ignore
            self.stdout.write('  ✅ Notifier создан')
            
            # Тест Cache
            cache = Container.cache()
            self.stdout.write('  ✅ Cache создан')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка Container: {str(e)}')

    def final_report(self):
        """Итоговый отчет"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!'))  # type: ignore
        self.stdout.write('\n💡 Рекомендации:')
        self.stdout.write('  • Если AI работает - запустите сервер: python manage.py runserver')
        self.stdout.write('  • Если нет данных - загрузите: python manage.py load_sample_data')
        self.stdout.write('  • Для бота запустите: python -m telegram_bot.bot_main')
