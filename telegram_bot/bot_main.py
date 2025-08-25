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
    start, subjects_menu, show_subject_topics, show_subject_topics,
    show_stats, handle_unknown_callback,
    main_menu, random_task, show_answer, ai_help_handler,
    ai_explain_handler, ai_personal_handler, ai_hint_general_handler,
    handle_ai_message, handle_text_message, learning_plan_menu,
    search_subject_handler, random_subject_handler, show_task_handler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_bot():
    """
    Возвращает экземпляр бота для использования в views
    """
    from telegram import Bot
    return Bot(settings.TELEGRAM_BOT_TOKEN)


def setup_bot_application():
    """
    Настраивает и возвращает приложение бота
    
    Регистрирует все обработчики команд и callback-запросов
    """
    # Создаем приложение бота
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))  # type: ignore
    application.add_handler(CommandHandler("help", start))  # type: ignore
    
    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(start, pattern="start"))
    application.add_handler(CallbackQueryHandler(subjects_menu, pattern="subjects"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    application.add_handler(CallbackQueryHandler(random_task, pattern="random_task"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
    application.add_handler(CallbackQueryHandler(learning_plan_menu, pattern="learning_plan"))
    
    # Обработчики для предметов и тем
    application.add_handler(CallbackQueryHandler(show_subject_topics, pattern=r"subject_\d+"))
    application.add_handler(CallbackQueryHandler(show_subject_topics, pattern=r"topic_\d+"))
    application.add_handler(CallbackQueryHandler(show_subject_topics, pattern=r"random_subject_\d+"))
    
    # Обработчик для показа задания
    application.add_handler(CallbackQueryHandler(show_task_handler, pattern=r"show_task_\d+"))
    
    # Новые обработчики для поиска и случайных предметов
    application.add_handler(CallbackQueryHandler(search_subject_handler, pattern="search_subject"))
    application.add_handler(CallbackQueryHandler(random_subject_handler, pattern="random_subject"))
    
        # Обработчики для ИИ
    application.add_handler(CallbackQueryHandler(ai_help_handler, pattern=r"ai_help"))
    application.add_handler(CallbackQueryHandler(ai_help_handler, pattern=r"ai_help_\d+"))
    application.add_handler(CallbackQueryHandler(ai_explain_handler, pattern=r"ai_explain"))
    application.add_handler(CallbackQueryHandler(ai_personal_handler, pattern=r"ai_personal"))
    application.add_handler(CallbackQueryHandler(ai_hint_general_handler, pattern=r"ai_hint"))
    
    # Обработчики для заданий
    application.add_handler(CallbackQueryHandler(show_answer, pattern=r"answer_\d+"))
    
    # Обработчик текстовых сообщений (для прямого общения с ИИ и нижнего меню)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Обработчик неизвестных callback-запросов
    application.add_handler(CallbackQueryHandler(handle_unknown_callback))
    
    logger.info("Telegram бот настроен и готов к работе")
    return application


if __name__ == '__main__':
    """Запуск бота в режиме polling (для разработки)"""
    application = setup_bot_application()
    
    logger.info("Запуск бота в режиме polling...")
    application.run_polling()
