"""
Django команда для загрузки данных ФИПИ и РешуЕГЭ

Использование:
python manage.py load_fipi_data
"""

from core.fipi_parser import run_data_update
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import sys
import os

# Добавляем путь к core для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загружает все данные ФИПИ и РешуЕГЭ в базу ExamFlow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно обновить все данные',
        )
        parser.add_argument(
            '--subjects-only',
            action='store_true',
            help='Обновить только предметы и темы',
        )
        parser.add_argument(
            '--tasks-only',
            action='store_true',
            help='Обновить только задания',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 ЗАГРУЗКА ДАННЫХ ФИПИ И РЕШУЕГЭ')
        self.stdout.write('=' * 60)

        start_time = timezone.now()

        try:
            if options['subjects_only']:
                self.stdout.write('📚 Обновляем только предметы и темы...')
                # Здесь будет логика для обновления только предметов
                success = self._update_subjects_only()
            elif options['tasks_only']:
                self.stdout.write('📝 Обновляем только задания...')
                # Здесь будет логика для обновления только заданий
                success = self._update_tasks_only()
            else:
                self.stdout.write('🔄 Полное обновление данных...')
                success = run_data_update()

            if success:
                end_time = timezone.now()
                duration = end_time - start_time

                self.stdout.write('=' * 60)
                self.stdout.write(
                    self.style.SUCCESS(  # type: ignore
                        f'✅ ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!'
                    )
                )
                self.stdout.write(f'⏱️ Время выполнения: {duration}')
                self.stdout.write(
                    f'📅 Завершено: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')

                # Показываем статистику
                self._show_statistics()

            else:
                # Полная загрузка с ФИПИ
                self.stdout.write('🌐 Загрузка данных с сайта ФИПИ...')
                self.stdout.write(
                    self.style.ERROR(  # type: ignore
                        '❌ ОШИБКА ПРИ ЗАГРУЗКЕ ДАННЫХ!'
                    )
                )
                return 1

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(  # type: ignore
                    f'❌ КРИТИЧЕСКАЯ ОШИБКА: {e}'
                )
            )
            logger.error(f"Ошибка в команде load_fipi_data: {e}")
            return 1

    def _update_subjects_only(self):
        """Обновляет только предметы и темы"""
        try:
            from core.fipi_parser import DataIntegrator

            integrator = DataIntegrator()

            # Создаем только предметы и темы
            subjects = integrator._create_subjects()
            topics = integrator._create_topics(subjects)

            self.stdout.write(f'✅ Создано предметов: {len(subjects)}')
            self.stdout.write(f'✅ Создано тем: {len(topics)}')

            return True

        except Exception as e:
            self.stdout.write(f'❌ Ошибка обновления предметов: {e}')
            return False

    def _update_tasks_only(self):
        """Обновляет только задания"""
        try:
            from core.fipi_parser import DataIntegrator
            from learning.models import Subject, Topic

            integrator = DataIntegrator()

            # Получаем существующие предметы и темы
            subjects = list(Subject.objects.all())  # type: ignore
            topics = list(Topic.objects.all())  # type: ignore

            if not subjects:
                self.stdout.write(
                    '❌ Нет предметов в базе. Сначала запустите --subjects-only')
                return False

            # Создаем только задания
            tasks = integrator._create_tasks(subjects, topics)

            self.stdout.write(f'✅ Создано заданий: {len(tasks)}')

            return True

        except Exception as e:
            self.stdout.write(f'❌ Ошибка обновления заданий: {e}')
            return False

    def _show_statistics(self):
        """Показывает статистику загруженных данных"""
        try:
            from learning.models import Subject, Topic, Task

            subjects_count = Subject.objects.count()  # type: ignore
            topics_count = Topic.objects.count()  # type: ignore
            tasks_count = Task.objects.count()  # type: ignore

            self.stdout.write('📊 СТАТИСТИКА:')
            self.stdout.write(f'   📚 Предметов: {subjects_count}')
            self.stdout.write(f'   🏷️ Тем: {topics_count}')
            self.stdout.write(f'   📝 Заданий: {tasks_count}')

            # Показываем детали по предметам
            self.stdout.write('\n📚 ДЕТАЛИ ПО ПРЕМЕТАМ:')
            for subject in Subject.objects.all():  # type: ignore
                subject_tasks = Task.objects.filter(
                    subject=subject).count()  # type: ignore
                subject_topics = Topic.objects.filter(
                    subject=subject).count()  # type: ignore
                self.stdout.write(  # type: ignore
                    f'   {subject.name} ({subject.exam_type}): '
                    f'{subject_tasks} заданий, {subject_topics} тем'
                )

        except Exception as e:
            self.stdout.write(f'⚠️ Не удалось показать статистику: {e}')
