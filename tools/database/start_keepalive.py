#!/usr/bin/env python
"""
Скрипт для запуска keepalive сервиса ExamFlow 2.0 в фоновом режиме
"""

import os
import sys
import django
import subprocess
import time
import signal
import logging
from pathlib import Path

# Настройка Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keepalive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class KeepaliveManager:
    """Менеджер для управления keepalive процессами"""

    def __init__(self):
        self.processes = {}
        self.running = False

    def start_keepalive(self, interval=300):
        """Запускает keepalive сервис"""
        try:
            logger.info("🚀 Запуск keepalive сервиса ExamFlow 2.0...")

            # Запускаем Django команду keepalive
            cmd = [
                sys.executable, 'manage.py', 'keepalive',
                '--interval', str(interval)
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.processes['keepalive'] = process
            self.running = True

            logger.info("✅ Keepalive сервис запущен (PID: {process.pid})")
            logger.info("⏰ Интервал проверки: {interval} секунд")

            return process

        except Exception:
            logger.error("❌ Ошибка запуска keepalive: {e}")
            return None

    def stop_keepalive(self):
        """Останавливает keepalive сервис"""
        if 'keepalive' in self.processes:
            process = self.processes['keepalive']
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info("✅ Keepalive сервис остановлен")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning("⚠️ Keepalive сервис принудительно остановлен")
            except Exception:
                logger.error("❌ Ошибка остановки keepalive: {e}")

            del self.processes['keepalive']
            self.running = False

    def check_status(self):
        """Проверяет статус keepalive сервиса"""
        if 'keepalive' in self.processes:
            process = self.processes['keepalive']
            if process.poll() is None:
                logger.info("🟢 Keepalive сервис активен (PID: {process.pid})")
                return True
            else:
                logger.warning("🔴 Keepalive сервис не запущен")
                return False
        else:
            logger.warning("🔴 Keepalive сервис не запущен")
            return False

    def run_foreground(self, interval=300):
        """Запускает keepalive в foreground режиме"""
        try:
            logger.info("🚀 Запуск keepalive в foreground режиме...")
            logger.info("Нажмите Ctrl+C для остановки")

            # Настраиваем обработчик сигналов
            def signal_handler(signum, frame):
                logger.info("🛑 Получен сигнал остановки...")
                self.stop_keepalive()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Запускаем keepalive
            process = self.start_keepalive(interval)
            if not process:
                return

            # Ждем завершения процесса
            while self.running:
                if process.poll() is not None:
                    logger.error("❌ Keepalive процесс завершился неожиданно")
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("🛑 Остановка по запросу пользователя...")
            self.stop_keepalive()
        except Exception:
            logger.error("❌ Ошибка в foreground режиме: {e}")
            self.stop_keepalive()

def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description='Keepalive сервис ExamFlow 2.0')
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Интервал проверки в секундах (по умолчанию 300)'
    )
    parser.add_argument(
        '--foreground',
        action='store_true',
        help='Запустить в foreground режиме'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Показать статус keepalive сервиса'
    )
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Остановить keepalive сервис'
    )

    args = parser.parse_args()

    manager = KeepaliveManager()

    if args.status:
        manager.check_status()
    elif args.stop:
        manager.stop_keepalive()
    elif args.foreground:
        manager.run_foreground(args.interval)
    else:
        # Запуск в background режиме
        manager.start_keepalive(args.interval)
        logger.info("✅ Keepalive сервис запущен в background режиме")
        logger.info("Используйте --status для проверки статуса")
        logger.info("Используйте --stop для остановки")

if __name__ == '__main__':
    main()
