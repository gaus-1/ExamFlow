#!/usr/bin/env python3
"""
Django Management команда для тестирования Dual AI системы
Тестирует Gemini и DeepSeek одновременно
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import time

from core.container import Container


class Command(BaseCommand):
    help = 'Тестирование Dual AI системы (Gemini + DeepSeek)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            choices=['gemini', 'deepseek', 'auto'],
            default='auto',
            help='Выбор AI провайдера для тестирования'
        )
        parser.add_argument(
            '--question',
            type=str,
            default='Объясни теорему Пифагора',
            help='Вопрос для тестирования AI'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 ТЕСТИРОВАНИЕ DUAL AI СИСТЕМЫ'))  # type: ignore
        self.stdout.write('=' * 70)
        
        provider = options['provider']
        question = options['question']
        
        # 1. Проверяем настройки
        self.test_api_keys()
        
        # 2. Тестируем подключения
        self.test_connections()
        
        # 3. Тестируем конкретный запрос
        self.test_question(question, provider)
        
        # 4. Сравнительное тестирование
        if provider == 'auto':
            self.comparative_test()
        
        # 5. Статистика
        self.show_stats()

    def test_api_keys(self):
        """Проверяет наличие API ключей"""
        self.stdout.write('\n🔑 ПРОВЕРКА API КЛЮЧЕЙ:')
        
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        
        if gemini_key:
            self.stdout.write(f'  ✅ GEMINI_API_KEY: {gemini_key[:10]}...')
        else:
            self.stdout.write('  ❌ GEMINI_API_KEY: НЕ НАЙДЕН')
        
        if deepseek_key:
            self.stdout.write(f'  ✅ DEEPSEEK_API_KEY: {deepseek_key[:10]}...')
        else:
            self.stdout.write('  ❌ DEEPSEEK_API_KEY: НЕ НАЙДЕН')

    def test_connections(self):
        """Тестирует подключения к AI провайдерам"""
        self.stdout.write('\n🔌 ТЕСТ ПОДКЛЮЧЕНИЙ:')
        
        try:
            dual_orchestrator = Container.dual_ai_orchestrator()
            test_results = dual_orchestrator.test_all_providers()
            
            for provider, is_working in test_results.items():
                status = '✅ РАБОТАЕТ' if is_working else '❌ НЕ РАБОТАЕТ'
                self.stdout.write(f'  {provider.upper()}: {status}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка тестирования: {e}')

    def test_question(self, question: str, provider: str):
        """Тестирует конкретный вопрос"""
        self.stdout.write(f'\n🤖 ТЕСТ ВОПРОСА: "{question}"')
        self.stdout.write(f'   Провайдер: {provider}')
        
        try:
            dual_orchestrator = Container.dual_ai_orchestrator()
            
            start_time = time.time()
            
            if provider == 'auto':
                response = dual_orchestrator.ask(question)
            else:
                response = dual_orchestrator.ask(question, provider=provider, use_fallback=False)
            
            end_time = time.time()
            
            answer = response.get('answer', 'Нет ответа')
            provider_used = response.get('provider_used', 'неизвестно')
            processing_time = response.get('processing_time', end_time - start_time)
            
            self.stdout.write(f'\n  📝 ОТВЕТ ({provider_used}):\n{answer[:200]}...')
            self.stdout.write(f'  ⏱️ Время: {processing_time:.2f}с')
            
            if 'error' in response:
                self.stdout.write(f'  ❌ Ошибка: {response["error"]}')
            else:
                self.stdout.write('  ✅ Успешно')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка тестирования: {e}')

    def comparative_test(self):
        """Сравнительное тестирование провайдеров"""
        self.stdout.write('\n⚖️ СРАВНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ:')
        
        test_questions = [
            "Решить уравнение x² + 5x + 6 = 0",
            "Что такое причастие в русском языке?",
            "Объясни закон Ома"
        ]
        
        dual_orchestrator = Container.dual_ai_orchestrator()
        
        for i, question in enumerate(test_questions, 1):
            self.stdout.write(f'\n  📝 Тест {i}: {question}')
            
            # Тестируем каждого провайдера
            for provider in ['gemini', 'deepseek']:
                try:
                    start_time = time.time()
                    response = dual_orchestrator.ask(question, provider=provider, use_fallback=False)
                    end_time = time.time()
                    
                    if 'error' not in response:
                        answer = response.get('answer', '')[:50] + '...'
                        self.stdout.write(f'    {provider.upper()}: ✅ {end_time - start_time:.2f}с - {answer}')
                    else:
                        self.stdout.write(f'    {provider.upper()}: ❌ {response.get("error", "Ошибка")}')
                        
                except Exception as e:
                    self.stdout.write(f'    {provider.upper()}: ❌ Исключение: {e}')

    def show_stats(self):
        """Показывает статистику использования"""
        self.stdout.write('\n📊 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ:')
        
        try:
            dual_orchestrator = Container.dual_ai_orchestrator()
            stats = dual_orchestrator.get_stats()
            
            for provider, provider_stats in stats['providers'].items():
                requests = provider_stats['requests']
                errors = provider_stats['errors']
                avg_time = provider_stats['avg_time']
                success_rate = ((requests - errors) / requests * 100) if requests > 0 else 0
                
                self.stdout.write(f'\n  {provider.upper()}:')
                self.stdout.write(f'    Запросов: {requests}')
                self.stdout.write(f'    Ошибок: {errors}')
                self.stdout.write(f'    Успешность: {success_rate:.1f}%')
                self.stdout.write(f'    Среднее время: {avg_time:.2f}с')
            
            available = ', '.join(stats['available_providers'])
            self.stdout.write(f'\n  Доступные провайдеры: {available}')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка получения статистики: {e}')
        
        # Итоговый отчет
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!'))  # type: ignore
        self.stdout.write('\n💡 Рекомендации:')
        self.stdout.write('  • Если оба провайдера работают - система готова')
        self.stdout.write('  • При ошибках проверьте API ключи')
        self.stdout.write('  • Для выбора провайдера используйте --provider')
        self.stdout.write('  • Для своего вопроса используйте --question "ваш вопрос"')
