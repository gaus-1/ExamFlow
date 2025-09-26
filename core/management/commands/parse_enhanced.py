"""
Django management command для запуска улучшенного парсера
"""

from django.core.management.base import BaseCommand
from core.fipi_parser_fixed import run_full_parsing
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает улучшенный парсер для обновления базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Запустить в тестовом режиме',
        )
        parser.add_argument(
            '--max-tasks',
            type=int,
            default=50,
            help='Максимальное количество заданий на предмет (по умолчанию: 50)',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write("🚀 Запуск улучшенного парсера...")

            if options['test']:
                self.stdout.write("🧪 Тестовый режим")
                success = run_full_parsing(
                    max_tasks_per_subject=10)  # Ограничиваем для тестирования
            else:
                # Здесь будет вызов полного парсера
                self.stdout.write("📚 Полный режим парсинга")
                success = run_full_parsing(options['max_tasks'])

            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Парсинг успешно завершен!")  # type: ignore
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Ошибка при парсинге")  # type: ignore
                )

        except Exception:
            logger.error("Критическая ошибка: {e}")
            self.stdout.write(
                self.style.ERROR("❌ Критическая ошибка: {e}")  # type: ignore
            )
