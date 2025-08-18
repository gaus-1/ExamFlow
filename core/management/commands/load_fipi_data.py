"""
Команда Django для загрузки данных ФИПИ
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.fipi_loader import FipiLoader
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загружает материалы и задания с сайта ФИПИ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--samples-only',
            action='store_true',
            help='Создать только примеры заданий без загрузки с ФИПИ',
        )
        parser.add_argument(
            '--subjects',
            nargs='+',
            help='Загрузить только указанные предметы (например: математика физика)',
        )
        parser.add_argument(
            '--exam-type',
            choices=['ЕГЭ', 'ОГЭ'],
            help='Загрузить только для указанного типа экзамена',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно перезаписать существующие данные',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Начинаем загрузку материалов ФИПИ...')
        )
        
        loader = FipiLoader()
        
        try:
            if options['samples_only']:
                # Создаем только примеры заданий
                self.stdout.write('📝 Создание примеров заданий...')
                tasks_count = loader.create_sample_tasks()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Создано примеров заданий: {tasks_count}'
                    )
                )
            
            else:
                # Полная загрузка с ФИПИ
                self.stdout.write('🌐 Загрузка данных с сайта ФИПИ...')
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  Это может занять несколько минут. Пожалуйста, ждите...'
                    )
                )
                
                subjects_count, tasks_count = loader.load_subjects()
                
                # Добавляем примеры заданий
                self.stdout.write('📝 Добавление примеров заданий...')
                sample_tasks_count = loader.create_sample_tasks()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Загрузка завершена успешно!'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'📊 Предметов создано: {subjects_count}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'📋 Заданий загружено: {tasks_count}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'📝 Примеров добавлено: {sample_tasks_count}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'🎯 Всего заданий: {tasks_count + sample_tasks_count}'
                    )
                )
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке: {str(e)}")
            raise CommandError(f'❌ Ошибка загрузки: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '🎉 Загрузка материалов ФИПИ завершена! Сайт готов к использованию.'
            )
        )
