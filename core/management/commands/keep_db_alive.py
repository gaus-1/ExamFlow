"""
Команда для поддержания соединения с базой данных активным
Предотвращает "засыпание" PostgreSQL на Render
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Поддерживает соединение с базой данных активным'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Интервал проверки в секундах (по умолчанию 60)'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Запустить в непрерывном режиме'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        continuous = options['continuous']

        self.stdout.write(
            f'🔄 Запуск keep-alive для базы данных (интервал: {interval}с)'
        )

        while True:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

                timestamp = timezone.now().strftime('%H:%M:%S')
                self.stdout.write(f"✅ {timestamp} - База активна")
                logger.info(f"База данных активна: {timestamp}")

            except Exception as e:
                timestamp = timezone.now().strftime('%H:%M:%S')
                error_msg = f"❌ {timestamp} - Ошибка базы: {e}"
                self.stdout.write(f"❌ {error_msg}")
                logger.error(f"Ошибка соединения с базой: {e}")

                # Пытаемся переподключиться
                try:
                    connection.close()
                    connection.ensure_connection()
                    self.stdout.write("🔄 Переподключение к базе...")
                except Exception as reconnect_error:
                    self.stdout.write(
                        f"❌ Не удалось переподключиться: {reconnect_error}"
                    )

            if not continuous:
                break

            time.sleep(interval)

        self.stdout.write(
            '🏁 Keep-alive завершен'
        )
