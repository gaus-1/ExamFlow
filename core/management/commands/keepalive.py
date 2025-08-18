"""
Команда Django для управления системой keep-alive
"""

from django.core.management.base import BaseCommand
from core.keepalive import start_keepalive, stop_keepalive, keepalive_service
import signal
import sys
import time


class Command(BaseCommand):
    help = 'Управление системой поддержания активности сайта'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status'],
            help='Действие: start, stop или status',
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить в фоновом режиме',
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_service(options.get('daemon', False))
        elif action == 'stop':
            self.stop_service()
        elif action == 'status':
            self.show_status()

    def start_service(self, daemon=False):
        """Запускает keep-alive службу"""
        self.stdout.write(
            self.style.SUCCESS('🚀 Запуск системы поддержания активности...')
        )
        
        # Настраиваем обработчик сигналов для корректного завершения
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING('\n⚠️  Получен сигнал завершения. Останавливаем службу...')
            )
            stop_keepalive()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            start_keepalive()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Keep-alive служба запущена успешно!')
            )
            self.stdout.write(
                self.style.SUCCESS('🔄 Сайт будет пинговаться каждые 10 минут')
            )
            self.stdout.write(
                self.style.WARNING('📝 Нажмите Ctrl+C для остановки')
            )
            
            if daemon:
                # В демон-режиме просто держим процесс
                while keepalive_service.is_running:
                    time.sleep(60)
            else:
                # В интерактивном режиме показываем статус
                self.run_interactive_mode()
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Остановка по запросу пользователя...')
            )
            stop_keepalive()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка запуска: {str(e)}')
            )

    def stop_service(self):
        """Останавливает keep-alive службу"""
        self.stdout.write('🛑 Остановка keep-alive службы...')
        stop_keepalive()
        self.stdout.write(
            self.style.SUCCESS('✅ Служба остановлена')
        )

    def show_status(self):
        """Показывает статус службы"""
        if keepalive_service.is_running:
            self.stdout.write(
                self.style.SUCCESS('🟢 Keep-alive служба активна')
            )
            self.stdout.write(f'🌐 URL: {keepalive_service.site_url}')
            self.stdout.write(f'⏰ Интервал: {keepalive_service.ping_interval} минут')
        else:
            self.stdout.write(
                self.style.WARNING('🔴 Keep-alive служба остановлена')
            )

    def run_interactive_mode(self):
        """Запускает интерактивный режим с отображением статуса"""
        try:
            while keepalive_service.is_running:
                # Очищаем экран (для Unix-систем)
                # print('\033[2J\033[H', end='')
                
                self.stdout.write('\n' + '='*50)
                self.stdout.write('🤖 ExamFlow Keep-Alive Service')
                self.stdout.write('='*50)
                self.stdout.write(f'🌐 URL: {keepalive_service.site_url}')
                self.stdout.write(f'⏰ Интервал: {keepalive_service.ping_interval} минут')
                self.stdout.write(f'🟢 Статус: Активен')
                self.stdout.write('📝 Нажмите Ctrl+C для остановки')
                self.stdout.write('='*50)
                
                # Ждем 30 секунд перед следующим обновлением
                time.sleep(30)
                
        except KeyboardInterrupt:
            pass
