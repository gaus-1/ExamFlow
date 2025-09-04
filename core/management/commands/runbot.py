"""
Команда Django для запуска Telegram бота
"""

from django.core.management.base import BaseCommand
import os
import signal
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Управление Telegram ботом ExamFlow'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'restart', 'status'],
            help='Действие: start, stop, restart или status',
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить в фоновом режиме',
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'start':
            self.start_bot(options.get('daemon', False))
        elif action == 'stop':
            self.stop_bot()
        elif action == 'restart':
            self.restart_bot()
        elif action == 'status':
            self.show_status()

    def start_bot(self, daemon=False):
        """Запускает Telegram бота"""
        self.stdout.write(
            self.style.SUCCESS('🤖 Запуск Telegram бота ExamFlow...')  # type: ignore
        )

        # Проверяем, не запущен ли уже бот
        if self.is_bot_running():
            self.stdout.write(
                self.style.WARNING('⚠️  Бот уже запущен!')  # type: ignore
            )
            return

        try:
            # Проверяем настройки бота
            from django.conf import settings
            token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not token:
                self.stdout.write(
                    # type: ignore
                    self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не настроен!')
                )
                self.stdout.write(
                    '   Добавьте TELEGRAM_BOT_TOKEN в Environment Variables')
                return

            # Проверяем доступность бота
            try:
                from telegram_bot.bot_main import get_bot
                bot = get_bot()
                if not bot:
                    self.stdout.write(
                        # type: ignore
                        self.style.ERROR('❌ Не удалось создать экземпляр бота')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка создания бота: {e}')  # type: ignore
                )
                return

            if daemon:
                # Запуск в фоновом режиме
                self.stdout.write('🔄 Запуск в фоновом режиме...')

                # Запускаем бота через новую команду
                try:
                    from django.core.management import call_command
                    call_command('run_bot_polling', '--daemon')
                    self.stdout.write(
                        self.style.SUCCESS('✅ Бот запущен в фоне')  # type: ignore
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Ошибка запуска бота: {e}')  # type: ignore
                    )
            else:
                # Запуск в интерактивном режиме
                self.stdout.write('🔄 Запуск в интерактивном режиме...')
                self.stdout.write(
                    self.style.WARNING('📝 Нажмите Ctrl+C для остановки')  # type: ignore
                )

                try:
                    from django.core.management import call_command
                    call_command('run_bot_polling')
                except KeyboardInterrupt:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n⚠️  Остановка по запросу пользователя...')  # type: ignore
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Ошибка запуска: {e}')  # type: ignore
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Неожиданная ошибка: {str(e)}')  # type: ignore
            )

    def stop_bot(self):
        """Останавливает бота"""
        self.stdout.write('🛑 Остановка Telegram бота...')

        # Читаем PID из файла
        pid_file = 'bot.pid'
        if not os.path.exists(pid_file):
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  PID файл не найден. Бот может быть не запущен.')  # type: ignore
            )
            return

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Останавливаем процесс
            os.kill(pid, signal.SIGTERM)

            # Удаляем PID файл
            os.remove(pid_file)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Бот остановлен (PID: {pid})')  # type: ignore
            )

        except (ValueError, ProcessLookupError) as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка остановки: {str(e)}')  # type: ignore
            )
            # Удаляем некорректный PID файл
            if os.path.exists(pid_file):
                os.remove(pid_file)

    def restart_bot(self):
        """Перезапускает бота"""
        self.stdout.write('🔄 Перезапуск Telegram бота...')
        self.stop_bot()
        time.sleep(1)
        self.start_bot(daemon=True)

    def show_status(self):
        """Показывает статус бота"""
        if self.is_bot_running():
            pid = self.get_bot_pid()
            self.stdout.write(
                self.style.SUCCESS(
                    f'🟢 Telegram бот запущен (PID: {pid})')  # type: ignore
            )

            # Проверяем, отвечает ли бот
            self.stdout.write('🔍 Проверка доступности бота...')

            # Здесь можно добавить проверку через Telegram API
            try:
                import requests
                from django.conf import settings

                bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
                if bot_token:
                    url = f"https://api.telegram.org/bot{bot_token}/getMe"
                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        bot_info = response.json()
                        if bot_info.get('ok'):
                            bot_name = bot_info['result']['username']
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✅ Бот отвечает: @{bot_name}')  # type: ignore
                            )
                        else:
                            self.stdout.write(
                                # type: ignore
                                self.style.ERROR('❌ Бот не отвечает на запросы')
                            )
                    else:
                        self.stdout.write(
                            # type: ignore
                            self.style.ERROR(f'❌ Ошибка API: {response.status_code}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠️  TELEGRAM_BOT_TOKEN не настроен')  # type: ignore
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Не удалось проверить API: {str(e)}')  # type: ignore
                )
        else:
            self.stdout.write(
                self.style.ERROR('🔴 Telegram бот остановлен')  # type: ignore
            )

    def is_bot_running(self):
        """Проверяет, запущен ли бот"""
        pid_file = 'bot.pid'
        if not os.path.exists(pid_file):
            return False

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Проверяем, существует ли процесс
            os.kill(pid, 0)  # Не убивает процесс, только проверяет
            return True

        except (ValueError, ProcessLookupError, OSError):
            # Удаляем некорректный PID файл
            if os.path.exists(pid_file):
                os.remove(pid_file)
            return False

    def get_bot_pid(self):
        """Возвращает PID бота"""
        pid_file = 'bot.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        return None
