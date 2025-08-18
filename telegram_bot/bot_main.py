"""
Основной файл Telegram бота

Настраивает приложение бота и регистрирует обработчики команд
"""

import os
import django
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from django.conf import settings
from .bot_handlers import (
    start, subjects_menu, show_subject_topics, show_task,
    handle_answer, show_stats, voice_hint, handle_unknown_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_bot_application():
    """
    Настраивает и возвращает приложение бота
    
    Регистрирует все обработчики команд и callback-запросов
    """
    # Создаем приложение бота
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    
    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(subjects_menu, pattern="subjects"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    application.add_handler(CallbackQueryHandler(show_task, pattern="random_task"))
    application.add_handler(CallbackQueryHandler(start, pattern="main_menu"))
    
    # Обработчики для предметов и тем
    application.add_handler(CallbackQueryHandler(show_subject_topics, pattern=r"subject_\d+"))
    application.add_handler(CallbackQueryHandler(show_task, pattern=r"topic_\d+"))
    application.add_handler(CallbackQueryHandler(show_task, pattern=r"random_subject_\d+"))
    
    # Обработчики для заданий
    application.add_handler(CallbackQueryHandler(voice_hint, pattern=r"voice_\d+"))
    application.add_handler(CallbackQueryHandler(show_task, pattern=r"answer_\d+"))
    
    # Обработчик текстовых сообщений (ответы на задания)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    
    # Обработчик неизвестных callback-запросов
    application.add_handler(CallbackQueryHandler(handle_unknown_callback))
    
    logger.info("Telegram бот настроен и готов к работе")
    return application


if __name__ == '__main__':
    """Запуск бота в режиме polling (для разработки)"""
    application = setup_bot_application()
    
    logger.info("Запуск бота в режиме polling...")
    application.run_polling()
