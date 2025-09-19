"""
Команда для безопасного применения миграций на Render.com
Включает retry логику и обработку SSL соединений
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from core.database_utils import retry_database_operation, ensure_database_connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Безопасное применение миграций на Render.com с retry логикой'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Максимальное количество попыток (по умолчанию: 3)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=10,
            help='Задержка между попытками в секундах (по умолчанию: 10)'
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        delay = options['delay']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Начинаем безопасное применение миграций (max_retries={max_retries}, delay={delay}s)'
            )
        )
        
        # Проверяем подключение к базе данных
        self.stdout.write('🔗 Проверяем подключение к базе данных...')
        if not ensure_database_connection():
            raise CommandError('Не удалось установить подключение к базе данных')
        
        # Применяем миграции с retry логикой
        self._apply_migrations_with_retry(max_retries, delay)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Все миграции применены успешно!')
        )

    def _apply_migrations_with_retry(self, max_retries, delay):
        """Применяет миграции с retry логикой"""
        
        @retry_database_operation(max_retries=max_retries, delay=delay)
        def apply_migrations():
            # Сначала проверяем, есть ли непримененные миграции
            try:
                call_command('makemigrations', '--dry-run', '--check')
                self.stdout.write('✅ Все миграции актуальны')
            except CommandError:
                self.stdout.write('⚠️ Есть неприменённые миграции, создаем...')
                call_command('makemigrations')
            
            # Применяем миграции
            self.stdout.write('🔄 Применяем миграции...')
            call_command('migrate', '--noinput')
            
            return True
        
        try:
            apply_migrations()
        except Exception as e:
            raise CommandError(f'Не удалось применить миграции после {max_retries} попыток: {e}')
