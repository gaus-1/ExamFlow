from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):  # type: ignore
    help = "Инициализирует карту источников FIPI для математики и русского"

    def handle(self, *args, **options):
        try:
            from core.models import FIPISourceMap  # type: ignore
        except Exception:
            self.stdout.write(self.style.ERROR("Модель FIPISourceMap недоступна"))  # type: ignore
            return

        seeds = [
            {
                "name": "ЕГЭ Математика — Демоверсия",
                "url": "https://fipi.ru/ege/demoversii/po-matematike",
                "type": "PDF",
                "category": "demo",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
            {
                "name": "ЕГЭ Математика — Спецификация",
                "url": "https://fipi.ru/ege/specifikacii/po-matematike",
                "type": "PDF",
                "category": "spec",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
            {
                "name": "ЕГЭ Математика — Кодификатор",
                "url": "https://fipi.ru/ege/kodifikatory/po-matematike",
                "type": "PDF",
                "category": "codifier",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 90,
            },
            {
                "name": "ЕГЭ Русский — Демоверсия",
                "url": "https://fipi.ru/ege/demoversii/po-russkomu-yazyku",
                "type": "PDF",
                "category": "demo",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
            {
                "name": "ЕГЭ Русский — Спецификация",
                "url": "https://fipi.ru/ege/specifikacii/po-russkomu-yazyku",
                "type": "PDF",
                "category": "spec",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
            {
                "name": "ЕГЭ Русский — Кодификатор",
                "url": "https://fipi.ru/ege/kodifikatory/po-russkomu-yazyku",
                "type": "PDF",
                "category": "codifier",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 90,
            },
        ]

        created = 0
        with transaction.atomic():  # type: ignore
            for s in seeds:
                obj, was_created = FIPISourceMap.objects.get_or_create(  # type: ignore
                    url=s["url"], defaults=s
                )
                if was_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Готово: добавлено {created} источников (или уже были).")  # type: ignore
        )

"""
Команда для инициализации карты источников данных fipi.ru
"""

from django.core.management.base import BaseCommand
import logging

from core.data_ingestion.fipi_structure_map import get_fipi_structure_map
from core.models import FIPISourceMap

logger = logging.getLogger(__name__)


class Command(BaseCommand):  # type: ignore 
    help = 'Инициализирует карту источников данных fipi.ru в базе данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно пересоздать все источники',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет создано без сохранения в БД',
        )
        parser.add_argument(
            '--priority',
            type=int,
            choices=[1, 2, 3, 4],
            help='Создать только источники с указанным приоритетом',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                '🗺️ Инициализация карты источников данных fipi.ru')  # type: ignore
        )
        self.stdout.write('=' * 60)

        # Получаем карту источников
        structure_map = get_fipi_structure_map()
        sources = structure_map.get_all_sources()

        # Фильтруем по приоритету если указан
        if options['priority']:
            sources = [s for s in sources if s.priority.value == options['priority']]
            self.stdout.write(
                self.style.WARNING(  # type: ignore
                    f'Создаем только источники с приоритетом {options["priority"]}')  # type: ignore
            )

        if options['dry_run']:
            self.dry_run(sources)
            return

        if options['force']:
            self.stdout.write(
                self.style.WARNING('Удаляем существующие источники...')  # type: ignore
            )
            FIPISourceMap.objects.all().delete()  # type: ignore            

        # Создаем источники
        created_count = 0
        updated_count = 0

        for source in sources:
            try:
                source_obj, created = FIPISourceMap.objects.get_or_create(  # type: ignore
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
                    self.stdout.write(
                        f'✅ Создан: {source.name}'  # type: ignore
                    )
                else:
                    # Обновляем существующий источник
                    source_obj.name = source.name
                    source_obj.url = source.url
                    source_obj.data_type = source.data_type.value
                    source_obj.exam_type = source.exam_type.value
                    source_obj.subject = source.subject
                    source_obj.priority = source.priority.value
                    source_obj.update_frequency = source.update_frequency.value
                    source_obj.file_format = source.file_format
                    source_obj.description = source.description
                    source_obj.save()

                    updated_count += 1
                    self.stdout.write(
                        f'🔄 Обновлен: {source.name}'  # type: ignore
                    )

            except Exception as e:
                self.stdout.write(
                    # type: ignore
                    self.style.ERROR(f'❌ Ошибка при создании {source.name}: {e}')  # type: ignore
                )
                logger.error(f'Ошибка при создании источника {source.id}: {e}')

        # Показываем статистику
        self.show_statistics(created_count, updated_count)

    def dry_run(self, sources):
        """Показать что будет создано без сохранения"""
        self.stdout.write(
            self.style.WARNING(  # type: ignore
                '🔍 DRY RUN - источники НЕ будут сохранены в БД')  # type: ignore
        )
        self.stdout.write('=' * 60)

        # Группируем по приоритетам
        by_priority = {}
        for source in sources:
            priority = source.priority.value
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(source)

        # Показываем по приоритетам
        for priority in sorted(by_priority.keys()):
            priority_name = {
                1: 'КРИТИЧЕСКИ ВАЖНЫЕ',
                2: 'ВЫСОКИЙ ПРИОРИТЕТ',
                3: 'СРЕДНИЙ ПРИОРИТЕТ',
                4: 'НИЗКИЙ ПРИОРИТЕТ',
            }[priority]

            self.stdout.write(
                self.style.SUCCESS(  # type: ignore
                    f'\n📋 {priority_name} ({len(by_priority[priority])} источников):')  # type: ignore
            )

            for source in by_priority[priority]:
                self.stdout.write(f'  • {source.name}')  # type: ignore
                self.stdout.write(f'    URL: {source.url}')
                self.stdout.write(
                    f'    Тип: {source.data_type.value} | Формат: {source.file_format}')
                if source.subject:
                    self.stdout.write(f'    Предмет: {source.subject}')  # type: ignore
                self.stdout.write('')

        # Общая статистика
        self.stdout.write('=' * 60)
        self.stdout.write(f'📊 Всего источников: {len(sources)}')  # type: ignore

        # Статистика по типам
        by_type = {}
        for source in sources:
            data_type = source.data_type.value
            by_type[data_type] = by_type.get(data_type, 0) + 1

        self.stdout.write('\n📈 По типам данных:')
        for data_type, count in sorted(by_type.items()):
            self.stdout.write(f'  • {data_type}: {count}')

    def show_statistics(self, created_count, updated_count):
        """Показать статистику создания"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('📊 Статистика инициализации:')  # type: ignore
        )
        self.stdout.write(f'✅ Создано новых источников: {created_count}')
        self.stdout.write(f'🔄 Обновлено существующих: {updated_count}')
        self.stdout.write(
            f'📋 Всего источников в БД: {FIPISourceMap.objects.count()}')  # type: ignore

        # Статистика по приоритетам
        self.stdout.write('\n📈 По приоритетам:')
        for priority in [1, 2, 3, 4]:
            count = FIPISourceMap.objects.filter(  # type: ignore
                priority=priority).count()  # type: ignore
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
            count = FIPISourceMap.objects.filter(  # type: ignore
                data_type=data_type).count()  # type: ignore
            if count > 0:
                self.stdout.write(f'  • {data_type}: {count}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                '🎉 Инициализация карты источников завершена!')  # type: ignore
        )
