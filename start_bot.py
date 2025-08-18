#!/usr/bin/env python3
"""
Автозапуск Telegram бота при деплое
"""

import os
import sys
import time
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция запуска"""
    logger.info("🤖 Автозапуск ExamFlow Telegram Bot...")
    
    # Проверяем наличие токена
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return False
    
    logger.info("✅ Токен бота найден")
    
    # Ждем немного, чтобы база данных была готова
    logger.info("⏳ Ожидание готовности системы...")
    time.sleep(10)
    
    try:
        # Запускаем бота
        logger.info("🚀 Запуск бота...")
        
        # Путь к файлу бота
        bot_path = os.path.join(os.path.dirname(__file__), 'bot', 'bot.py')
        
        if not os.path.exists(bot_path):
            logger.error(f"❌ Файл бота не найден: {bot_path}")
            return False
        
        # Запускаем процесс бота
        process = subprocess.Popen(
            [sys.executable, bot_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info(f"✅ Бот запущен с PID: {process.pid}")
        
        # Читаем и выводим логи
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
        
        # Ждем завершения процесса
        return_code = process.wait()
        logger.info(f"🛑 Бот завершен с кодом: {return_code}")
        
        return return_code == 0
        
    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал остановки")
        if 'process' in locals():
            process.terminate()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {str(e)}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
