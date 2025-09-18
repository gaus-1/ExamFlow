#!/usr/bin/env python3
"""
ExamFlow Bot Worker для Render.com
24/7 Telegram бот в облаке
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

# Настройка логирования для Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Render использует stdout для логов
)

logger = logging.getLogger(__name__)

# Импортируем наш 24/7 бот
from telegram_bot.bot_24_7 import ExamFlowBot24_7


async def main():
    """Главная функция для Render.com"""
    logger.info("🚀 Запуск ExamFlow Bot на Render.com")
    
    # Проверяем переменные окружения
    required_vars = ['TELEGRAM_BOT_TOKEN', 'DATABASE_URL', 'SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют переменные окружения: {missing_vars}")
        sys.exit(1)
    
    # Создаем и запускаем бота
    bot = ExamFlowBot24_7()
    
    try:
        await bot.start_bot()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        sys.exit(1)
