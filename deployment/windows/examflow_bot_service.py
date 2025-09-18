#!/usr/bin/env python3
"""
ExamFlow Bot Windows Service
Системный сервис для запуска Telegram бота в фоне
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Настройка путей
PROJECT_ROOT = Path(__file__).parent.parent.parent
BOT_SCRIPT = PROJECT_ROOT / "telegram_bot" / "bot_24_7.py"
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'bot_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ExamFlowBotService:
    """Windows сервис для ExamFlow бота"""
    
    def __init__(self):
        self.process = None
        self.is_running = False
        self.restart_count = 0
        self.max_restarts = 50  # Больше попыток для 24/7
        
    def start_bot_process(self):
        """Запуск процесса бота"""
        try:
            # Команда запуска (прямой скрипт)
            cmd = [str(VENV_PYTHON), str(PROJECT_ROOT / 'start_bot_direct.py')]
            
            # Переменные окружения
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'examflow_project.settings'
            
            # Запуск процесса
            self.process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"Бот запущен с PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            return False
    
    def stop_bot_process(self):
        """Остановка процесса бота"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("✅ Бот остановлен")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("⚠️ Бот принудительно завершен")
            except Exception as e:
                logger.error(f"❌ Ошибка остановки бота: {e}")
            finally:
                self.process = None
    
    def is_bot_alive(self):
        """Проверка жизни бота"""
        if not self.process:
            return False
        
        # Проверяем статус процесса
        poll_result = self.process.poll()
        if poll_result is not None:
            logger.warning(f"⚠️ Процесс бота завершился с кодом: {poll_result}")
            return False
        
        return True
    
    def restart_bot(self):
        """Перезапуск бота"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ Превышено максимальное количество перезапусков ({self.max_restarts})")
            return False
        
        self.restart_count += 1
        logger.warning(f"🔄 Перезапуск бота #{self.restart_count}")
        
        self.stop_bot_process()
        time.sleep(5)  # Ждем 5 секунд
        return self.start_bot_process()
    
    def run_service(self):
        """Основной цикл сервиса"""
        logger.info("Запуск ExamFlow Bot Service")
        
        # Создаем директорию логов
        (PROJECT_ROOT / 'logs').mkdir(exist_ok=True)
        
        # Первоначальный запуск
        if not self.start_bot_process():
            logger.error("❌ Не удалось запустить бота")
            return
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Проверяем жизнь бота каждые 30 секунд
                time.sleep(30)
                
                if not self.is_bot_alive():
                    logger.warning("⚠️ Бот не отвечает, перезапускаем...")
                    if not self.restart_bot():
                        logger.error("❌ Не удалось перезапустить бота")
                        break
                
                # Сбрасываем счетчик перезапусков каждый час
                if self.restart_count > 0 and time.time() % 3600 < 30:
                    self.restart_count = max(0, self.restart_count - 1)
                    
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка сервиса: {e}")
        finally:
            self.stop_bot_process()
            logger.info("🛑 Сервис остановлен")
    
    def stop_service(self):
        """Остановка сервиса"""
        self.is_running = False


def main():
    """Главная функция"""
    service = ExamFlowBotService()
    
    try:
        service.run_service()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
