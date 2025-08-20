"""
Команда Django для запуска Telegram бота
"""

from django.core.management.base import BaseCommand
import subprocess
import sys
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
            # Путь к файлу бота
            bot_path = os.path.join(os.getcwd(), 'bot', 'bot.py')
            
            if not os.path.exists(bot_path):
                self.stdout.write(
                    self.style.ERROR(f'❌ Файл бота не найден: {bot_path}')  # type: ignore
                )
                return
            
            if daemon:
                # Запуск в фоновом режиме
                self.stdout.write('🔄 Запуск в фоновом режиме...')
                
                # Создаем процесс в фоне
                process = subprocess.Popen(
                    [sys.executable, bot_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                
                # Сохраняем PID
                with open('bot.pid', 'w') as f:
                    f.write(str(process.pid))
                
                # Ждем немного и проверяем, что процесс запустился
                time.sleep(2)
                if process.poll() is None:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Бот запущен в фоне (PID: {process.pid})')  # type: ignore
                    )
                else:
                    # Читаем ошибки
                    stdout, stderr = process.communicate()
                    self.stdout.write(
                        self.style.ERROR(f'❌ Ошибка запуска бота: {stderr.decode()}')  # type: ignore
                    )
            else:
                # Запуск в интерактивном режиме
                self.stdout.write('🔄 Запуск в интерактивном режиме...')
                self.stdout.write(
                    self.style.WARNING('📝 Нажмите Ctrl+C для остановки')  # type: ignore
                )
                
                try:
                    subprocess.run([sys.executable, bot_path], check=True)
                except KeyboardInterrupt:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️  Остановка по запросу пользователя...')  # type: ignore
                    )
                except subprocess.CalledProcessError as e:
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
                self.style.WARNING('⚠️  PID файл не найден. Бот может быть не запущен.')  # type: ignore
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
                self.style.SUCCESS(f'🟢 Telegram бот запущен (PID: {pid})')  # type: ignore
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
                                self.style.SUCCESS(f'✅ Бот отвечает: @{bot_name}')  # type: ignore
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR('❌ Бот не отвечает на запросы')  # type: ignore
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Ошибка API: {response.status_code}')  # type: ignore
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  TELEGRAM_BOT_TOKEN не настроен')  # type: ignore
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Не удалось проверить API: {str(e)}')  # type: ignore
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
