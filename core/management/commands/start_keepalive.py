"""
Главная команда для запуска всех keep-alive процессов
Предотвращает "засыпание" базы данных и сайта на Render
"""

import subprocess
import time
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает все keep-alive процессы для предотвращения "засыпания"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-interval',
            type=int,
            default=300,  # 5 минут для базы
            help='Интервал проверки базы в секундах (по умолчанию 300 = 5 минут)'
        )
        parser.add_argument(
            '--site-interval',
            type=int,
            default=600,  # 10 минут для сайта
            help='Интервал проверки сайта в секундах (по умолчанию 600 = 10 минут)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить в фоновом режиме (daemon)'
        )

    def handle(self, *args, **options):
        db_interval = options['db_interval']
        site_interval = options['site_interval']
        daemon = options['daemon']

        self.stdout.write('🚀 Запуск системы keep-alive для ExamFlow')
        self.stdout.write('=' * 50)
        self.stdout.write(
            f'🗄️ База данных: каждые {db_interval} секунд ({db_interval//60} минут)')
        self.stdout.write(
            f'🌐 Сайт: каждые {site_interval} секунд ({site_interval//60} минут)')
        self.stdout.write('=' * 50)

        if daemon:
            self.stdout.write('🔄 Запуск в фоновом режиме...')

            # Запускаем keep-alive базы в фоне
            db_process = subprocess.Popen([
                'python', 'manage.py', 'keep_db_alive',
                '--continuous', '--interval', str(db_interval)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Запускаем keep-alive сайта в фоне
            site_process = subprocess.Popen([
                'python', 'manage.py', 'keep_site_alive',
                '--continuous', '--interval', str(site_interval)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.stdout.write('✅ Keep-alive запущены в фоне:')
            self.stdout.write(f'   База данных: PID {db_process.pid}')
            self.stdout.write(f'   Сайт: PID {site_process.pid}')
            self.stdout.write('')
            self.stdout.write('💡 Для остановки используйте:')
            self.stdout.write(f'   kill {db_process.pid}  # Остановить keep-alive базы')
            self.stdout.write(
                f'   kill {site_process.pid}  # Остановить keep-alive сайта')

        else:
            self.stdout.write('🔄 Запуск в интерактивном режиме...')
            self.stdout.write('Нажмите Ctrl+C для остановки')

            try:
                while True:
                    # Проверяем базу данных
                    self.stdout.write('🗄️ Проверяем базу данных...')
                    call_command('keep_db_alive', '--interval', '1')

                    # Проверяем сайт
                    self.stdout.write('🌐 Проверяем сайт...')
                    call_command('keep_site_alive', '--interval', '1')

                    # Ждем до следующей проверки
                    wait_time = min(db_interval, site_interval)
                    self.stdout.write(
                        f'⏰ Следующая проверка через {wait_time} секунд...')
                    time.sleep(wait_time)

            except KeyboardInterrupt:
                self.stdout.write('')
                self.stdout.write('🛑 Keep-alive остановлен пользователем')

        self.stdout.write('🏁 Система keep-alive завершена')
