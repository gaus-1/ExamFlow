"""
Команда для обработки данных ФИПИ и создания векторных представлений
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from core.rag_system.text_processor import TextProcessor
from core.rag_system.vector_store import VectorStore

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Обрабатывает данные ФИПИ и создает векторные представления'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Обработать все необработанные данные',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='ID конкретной записи для обработки',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=1000,
            help='Размер чанка в символах',
        )
        parser.add_argument(
            '--overlap',
            type=int,
            default=200,
            help='Размер перекрытия между чанками',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показать статистику векторного хранилища',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_statistics()
            return

        self.stdout.write(
            self.style.SUCCESS('Начинаем обработку данных ФИПИ...')  # type: ignore
        )

        start_time = timezone.now()

        try:
            # Создаем процессор
            processor = TextProcessor(
                chunk_size=options['chunk_size'],
                overlap=options['overlap']
            )

            if options['all']:
                # Обрабатываем все данные
                self.process_all_data(processor)
            elif options['id']:
                # Обрабатываем конкретную запись
                self.process_single_data(processor, options['id'])
            else:
                self.stdout.write(
                    # type: ignore
                    self.style.ERROR('Укажите --all или --id для обработки')
                )
                return

            end_time = timezone.now()
            duration = end_time - start_time

            self.stdout.write(
                self.style.SUCCESS(  # type: ignore
                    # type: ignore
                    'Обработка завершена за {duration.total_seconds():.2f} секунд'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Ошибка при обработке: {e}')  # type: ignore
            )
            logger.error('Ошибка при обработке: {e}')

    def process_all_data(self, processor):
        """Обрабатывает все необработанные данные"""
        results = processor.process_all_unprocessed_data()

        if 'error' in results:
            self.stdout.write(
                self.style.ERROR('Ошибка: {results["error"]}')  # type: ignore
            )
            return

        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                'Обработано: {results["processed"]}/{results["total"]} записей'
            )
        )

        if results['errors'] > 0:
            self.stdout.write(
                self.style.WARNING('Ошибок: {results["errors"]}')  # type: ignore
            )

    def process_single_data(self, processor, data_id):
        """Обрабатывает одну запись"""
        success = processor.process_fipi_data(data_id)

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    'Запись {data_id} обработана успешно')  # type: ignore
            )
        else:
            self.stdout.write(
                # type: ignore
                self.style.ERROR('Ошибка при обработке записи {data_id}')
            )

    def show_statistics(self):
        """Показывает статистику векторного хранилища"""
        vector_store = VectorStore()
        stats = vector_store.get_statistics()

        self.stdout.write(
            self.style.SUCCESS('Статистика векторного хранилища:')  # type: ignore
        )
        self.stdout.write('Всего чанков: {stats.get("total_chunks", 0)}')
        self.stdout.write('Всего источников: {stats.get("total_sources", 0)}')
        self.stdout.write('Обработано источников: {stats.get("processed_sources", 0)}')
        self.stdout.write(
            'Процент обработки: {stats.get("processing_percentage", 0):.1f}%')
