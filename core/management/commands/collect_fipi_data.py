"""
Команда для сбора данных с ФИПИ
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from core.data_ingestion.fipi_scraper import FIPIScraper
from core.data_ingestion.monitor import DataMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Собирает данные с сайта ФИПИ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно собрать данные, даже если они уже есть',
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Запустить мониторинг обновлений',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['demo_variants', 'open_bank_tasks', 'specifications', 'all'],
            default='all',
            help='Тип данных для сбора',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Начинаем сбор данных с ФИПИ...')
        )

        start_time = timezone.now()

        try:
            if options['monitor']:
                # Запускаем мониторинг
                self.run_monitoring()
            else:
                # Запускаем сбор данных
                self.run_data_collection(options)

            end_time = timezone.now()
            duration = end_time - start_time

            self.stdout.write(
                self.style.SUCCESS(
                    f'Сбор данных завершен за {duration.total_seconds():.2f} секунд'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при сборе данных: {e}')
            )
            logger.error(f'Ошибка при сборе данных: {e}')

    def run_data_collection(self, options):
        """Запускает сбор данных"""
        scraper = FIPIScraper()

        if options['type'] == 'all':
            # Собираем все данные
            data = scraper.collect_all_data()
        else:
            # Собираем конкретный тип данных
            if options['type'] == 'demo_variants':
                data = {'demo_variants': scraper.extract_demo_variants()}
            elif options['type'] == 'open_bank_tasks':
                data = {'open_bank_tasks': scraper.extract_open_bank_tasks()}
            elif options['type'] == 'specifications':
                data = {'specifications': scraper.extract_specifications()}

        # Сохраняем данные
        success = scraper.save_to_database(data)

        if success:
            total_items = sum(len(items) for items in data.values())
            self.stdout.write(
                self.style.SUCCESS(f'Сохранено {total_items} записей')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Ошибка при сохранении данных')
            )

    def run_monitoring(self):
        """Запускает мониторинг"""
        monitor = DataMonitor()
        results = monitor.run_monitoring_cycle()

        self.stdout.write(
            self.style.SUCCESS(
                f'Мониторинг завершен. Найдено обновлений: {results["updates_found"]}'
            )
        )

        if results['errors']:
            for error in results['errors']:
                self.stdout.write(
                    self.style.WARNING(f'Предупреждение: {error}')
                )
