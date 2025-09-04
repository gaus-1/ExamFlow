"""
Команда для тестирования карты структуры fipi.ru
"""

from django.core.management.base import BaseCommand
import logging

from core.data_ingestion.fipi_structure_map import get_fipi_structure_map
from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper
from core.models import FIPISourceMap

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирует карту структуры fipi.ru и собирает данные'

    def add_arguments(self, parser):
        parser.add_argument(
            '--init-map',
            action='store_true',
            help='Инициализировать карту источников в БД',
        )
        parser.add_argument(
            '--test-scraping',
            action='store_true',
            help='Протестировать сбор данных',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Показать статистику',
        )
        parser.add_argument(
            '--priority',
            type=int,
            choices=[1, 2, 3, 4],
            help='Тестировать только источники с указанным приоритетом',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Тестирование карты структуры fipi.ru')
        )
        self.stdout.write('=' * 60)

        if options['init_map']:
            self.init_source_map()

        if options['test_scraping']:
            self.test_scraping(options.get('priority'))

        if options['show_stats']:
            self.show_statistics()

        if not any([options['init_map'],
                    options['test_scraping'],
                    options['show_stats']]):
            self.show_help()

    def init_source_map(self):
        """Инициализирует карту источников"""
        self.stdout.write(
            self.style.SUCCESS('🗺️ Инициализация карты источников...')
        )

        # Получаем карту источников
        structure_map = get_fipi_structure_map()
        sources = structure_map.get_all_sources()

        created_count = 0
        updated_count = 0

        for source in sources:
            try:
                source_obj, created = FIPISourceMap.objects.get_or_create(
                    source_id=source.id,
                    defaults={
                        'name': source.name,
                        'url': source.url,
                        'data_type': source.data_type.value,
                        'exam_type': source.exam_type.value,
                        'subject': source.subject,
                        'priority': source.priority.value,
                        'update_frequency': source.update_frequency.value,
                        'file_format': source.file_format,
                        'description': source.description,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'✅ Создан: {source.name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'🔄 Обновлен: {source.name}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при создании {source.name}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Создано: {created_count}, Обновлено: {updated_count}')
        )

    def test_scraping(self, priority=None):
        """Тестирует сбор данных"""
        self.stdout.write(
            self.style.SUCCESS('🕷️ Тестирование сбора данных...')
        )

        scraper = AdvancedFIPIScraper()

        # Получаем источники для тестирования
        if priority:
            sources = FIPISourceMap.objects.filter(
                is_active=True,
                priority=priority
            )[:5]  # Ограничиваем для теста
            self.stdout.write(f'Тестируем источники с приоритетом {priority}')
        else:
            sources = FIPISourceMap.objects.filter(
                is_active=True,
                priority__lte=2  # Только критически важные и высокоприоритетные
            )[:10]
            self.stdout.write(
                'Тестируем критически важные и высокоприоритетные источники')

        if not sources.exists():
            self.stdout.write(
                self.style.ERROR('Нет активных источников для тестирования')
            )
            return

        success_count = 0
        error_count = 0

        for source in sources:
            try:
                self.stdout.write(f'Тестируем: {source.name}')

                # Получаем содержимое
                content = scraper.get_page_content(source.url)

                if content:
                    # Создаем хеш
                    content_hash = scraper.get_content_hash(str(content))

                    # Обновляем источник
                    source.mark_as_checked(content_hash)

                    self.stdout.write(f'  ✅ Успешно: {len(str(content))} символов')
                    success_count += 1
                else:
                    self.stdout.write(f'  ❌ Ошибка: не удалось получить содержимое')
                    error_count += 1

                # Небольшая задержка
                import time
                time.sleep(1)

            except Exception as e:
                self.stdout.write(f'  ❌ Ошибка: {e}')
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Тестирование завершено: {success_count} успешно, {error_count} ошибок'))

    def show_statistics(self):
        """Показывает статистику"""
        self.stdout.write(
            self.style.SUCCESS('📊 Статистика системы')
        )
        self.stdout.write('=' * 60)

        # Статистика источников
        total_sources = FIPISourceMap.objects.count()
        active_sources = FIPISourceMap.objects.filter(is_active=True).count()

        self.stdout.write(f'📋 Всего источников: {total_sources}')
        self.stdout.write(f'✅ Активных источников: {active_sources}')

        # Статистика по приоритетам
        self.stdout.write('\n📈 По приоритетам:')
        for priority in [1, 2, 3, 4]:
            count = FIPISourceMap.objects.filter(priority=priority).count()
            priority_name = {
                1: 'Критически важные',
                2: 'Высокий приоритет',
                3: 'Средний приоритет',
                4: 'Низкий приоритет',
            }[priority]
            self.stdout.write(f'  • {priority_name}: {count}')

        # Статистика по типам данных
        self.stdout.write('\n📈 По типам данных:')
        for data_type, _ in FIPISourceMap.DATA_TYPES:
            count = FIPISourceMap.objects.filter(data_type=data_type).count()
            if count > 0:
                self.stdout.write(f'  • {data_type}: {count}')

        # Статистика по типам экзаменов
        self.stdout.write('\n📈 По типам экзаменов:')
        for exam_type, _ in FIPISourceMap.EXAM_TYPES:
            count = FIPISourceMap.objects.filter(exam_type=exam_type).count()
            if count > 0:
                self.stdout.write(f'  • {exam_type}: {count}')

        # Статистика по форматам
        self.stdout.write('\n📈 По форматам файлов:')
        for file_format, _ in FIPISourceMap.FILE_FORMATS:
            count = FIPISourceMap.objects.filter(file_format=file_format).count()
            if count > 0:
                self.stdout.write(f'  • {file_format}: {count}')

    def show_help(self):
        """Показывает справку по использованию"""
        self.stdout.write(
            self.style.WARNING('Использование команды:')
        )
        self.stdout.write('  --init-map     - Инициализировать карту источников в БД')
        self.stdout.write('  --test-scraping - Протестировать сбор данных')
        self.stdout.write('  --show-stats   - Показать статистику')
        self.stdout.write(
            '  --priority N   - Тестировать только источники с приоритетом N')
        self.stdout.write('')
        self.stdout.write('Примеры:')
        self.stdout.write('  python manage.py test_fipi_structure --init-map')
        self.stdout.write(
            '  python manage.py test_fipi_structure --test-scraping --priority 1')
        self.stdout.write('  python manage.py test_fipi_structure --show-stats')
