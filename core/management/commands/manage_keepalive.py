"""
Команда управления keepalive сервисом для ExamFlow 2.0
"""

import time
import logging
from django.core.management.base import BaseCommand
from core.keepalive_service import keepalive_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Управляет keepalive сервисом для поддержания работы 24/7'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'check', 'wake'],
            help='Действие: start, stop, status, check, wake'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,
            help='Интервал проверки в секундах (по умолчанию 300)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить в режиме демона (только для start)'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_keepalive(options)
        elif action == 'stop':
            self.stop_keepalive()
        elif action == 'status':
            self.show_status()
        elif action == 'check':
            self.perform_check()
        elif action == 'wake':
            self.wake_up_services()
    
    def start_keepalive(self, options):
        """Запускает keepalive сервис"""
        if keepalive_service.is_running:
            self.stdout.write(self.style.WARNING("Keepalive сервис уже запущен")) # type: ignore
            return
        
        # Обновляем настройки
        keepalive_service.check_interval = options['interval']
        
        if options['daemon']:
            self.stdout.write("🚀 Запуск keepalive сервиса в режиме демона...")
            keepalive_service.start()
            self.stdout.write(self.style.SUCCESS("✅ Keepalive сервис запущен в фоне")) # type: ignore
        else:
            self.stdout.write(f"🚀 Запуск keepalive сервиса с интервалом {options['interval']} секунд...")
            self.stdout.write("Нажмите Ctrl+C для остановки")
            
            try:
                keepalive_service.start()
                # В интерактивном режиме ждем
                while keepalive_service.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n🛑 Остановка keepalive сервиса...")) # type: ignore
                keepalive_service.stop()
                self.stdout.write(self.style.SUCCESS("✅ Keepalive сервис остановлен")) # type: ignore
    
    def stop_keepalive(self):
        """Останавливает keepalive сервис"""
        if not keepalive_service.is_running:
            self.stdout.write(self.style.WARNING("Keepalive сервис не запущен")) # type: ignore
            return
        
        keepalive_service.stop()
        self.stdout.write(self.style.SUCCESS("✅ Keepalive сервис остановлен")) # type: ignore
    
    def show_status(self):
        """Показывает статус keepalive сервиса"""
        stats = keepalive_service.get_stats()
        
        self.stdout.write("📊 Статус Keepalive сервиса:")
        self.stdout.write(f"   Запущен: {'✅' if stats['is_running'] else '❌'}")
        
        if stats['stats']['last_check']:
            self.stdout.write(f"   Последняя проверка: {stats['stats']['last_check']}")
        
        if stats['stats']['last_success']:
            self.stdout.write(f"   Последний успех: {stats['stats']['last_success']}")
        
        self.stdout.write(f"   Всего проверок: {stats['stats']['checks_performed']}")
        self.stdout.write(f"   Успешных: {stats['stats']['successful_checks']}")
        self.stdout.write(f"   Неудачных: {stats['stats']['failed_checks']}")
        self.stdout.write(f"   Последовательных неудач: {stats['stats']['consecutive_failures']}")
        
        if stats['stats']['checks_performed'] > 0:
            success_rate = (stats['stats']['successful_checks'] / stats['stats']['checks_performed']) * 100
            self.stdout.write(f"   Процент успеха: {success_rate:.1f}%")
    
    def perform_check(self):
        """Выполняет однократную проверку"""
        self.stdout.write("🔍 Выполняем проверку компонентов...")
        
        health_results = keepalive_service.perform_health_check()
        
        self.stdout.write(f"📊 Общий статус: {health_results['overall_status']}")
        
        for component, result in health_results.items():
            if component in ['timestamp', 'overall_status', 'stats']:
                continue
            
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                status_icon = '✅' if status == 'success' else '❌'
                self.stdout.write(f"   {component}: {status_icon} {status}")
                
                if 'response_time' in result:
                    self.stdout.write(f"      Время ответа: {result['response_time']:.2f}s")
                
                if 'error' in result:
                    self.stdout.write(f"      Ошибка: {result['error']}")
    
    def wake_up_services(self):
        """Будит все сервисы"""
        self.stdout.write("🌐 Пробуждаем сервисы...")
        
        website_ok = keepalive_service.wake_up_website()
        database_ok = keepalive_service.wake_up_database()
        
        self.stdout.write(f"   Сайт: {'✅' if website_ok else '❌'}")
        self.stdout.write(f"   База данных: {'✅' if database_ok else '❌'}")
        
        if website_ok and database_ok:
            self.stdout.write(self.style.SUCCESS("✅ Все сервисы разбужены")) # type: ignore
        else:
            self.stdout.write(self.style.WARNING("⚠️ Некоторые сервисы не удалось разбудить")) # type: ignore   
