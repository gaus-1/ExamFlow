"""
Команда для тестирования RAG-системы
"""

from django.core.management.base import BaseCommand
from core.rag_system.orchestrator import get_ai_orchestrator
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует RAG-систему с различными запросами'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            help='Конкретный запрос для тестирования',
            default=None
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя для тестирования персонализации',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Тестирование RAG-системы ExamFlow 2.0') # type: ignore      
        )
        
        # Получаем оркестратор
        try:
            orchestrator = get_ai_orchestrator()
            self.stdout.write(
                self.style.SUCCESS('RAG-система инициализирована') # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка инициализации RAG-системы: {e}') # type: ignore
            )
            return

        # Тестовые запросы
        test_queries = [
            "Как решать квадратные уравнения?",
            "Объясни теорию вероятности",
            "Как писать сочинение по русскому языку?",
            "Правила английской грамматики",
            "Основы органической химии"
        ]

        if options['query']:
            test_queries = [options['query']]

        user_id = options.get('user_id')

        for i, query in enumerate(test_queries, 1):
            self.stdout.write(f'\n📝 Тест {i}: {query}')
            self.stdout.write('-' * 50)
            
            try:
                # Обрабатываем запрос
                response = orchestrator.process_query(query, user_id)
                
                # Выводим результат
                self.stdout.write(f'Ответ получен') # type: ignore
                self.stdout.write(f'Ответ: {response["answer"][:200]}...')
                self.stdout.write(f'Источники: {len(response["sources"])}')
                self.stdout.write(f'Практика: {response["practice"]["topic"]}')
                
                if response.get('error'):
                    self.stdout.write(f'Ошибка: {response["error"]}') # type: ignore
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при обработке запроса: {e}') # type: ignore
                )

        self.stdout.write(
            self.style.SUCCESS('\nТестирование RAG-системы завершено!') # type: ignore
        )