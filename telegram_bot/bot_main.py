"""
Основной файл Telegram бота

Настраивает приложение бота и регистрирует обработчики команд
"""

import hashlib
import hmac
import logging
import os

import django
from django.conf import settings
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram_bot.bot_handlers import (
    achievements_handler,
    ai_explain_handler,
    ai_help_handler,
    ai_hint_general_handler,
    ai_personal_handler,
    bonus_handler,
    clear_context_handler,
    daily_challenges_handler,
    gamification_menu_handler,
    handle_text_message,
    handle_unknown_callback,
    leaderboard_handler,
    learning_plan_menu,
    overall_progress_handler,
    progress_handler,
    random_subject_handler,
    random_task,
    search_subject_handler,
    show_answer,
    show_stats,
    show_subject_topics,
    show_task_handler,
    start,
    subjects_progress_handler,
    user_stats_handler,
)
from telegram_bot.commands.ai import (
    ai_explain_handler,
    ai_help_handler,
    ai_hint_general_handler,
    ai_personal_handler,
    clear_context_handler,
    handle_text_message,
)
from telegram_bot.commands.auth import auth_success_handler, telegram_auth_handler
from telegram_bot.commands.gamification import (
    achievements_handler,
    bonus_handler,
    daily_challenges_handler,
    gamification_menu_handler,
    handle_unknown_callback,
    leaderboard_handler,
    overall_progress_handler,
    progress_handler,
    show_stats,
    subjects_progress_handler,
    user_stats_handler,
)
from telegram_bot.commands.main_menu import main_menu  # тонкая обёртка
from telegram_bot.commands.subjects import subjects_menu
from telegram_bot.commands.tasks import (
    random_subject_handler,
    random_task,
    search_subject_handler,
    show_answer,
    show_subject_topics,
    show_task_handler,
)

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
django.setup()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔒 БЕЗОПАСНОСТЬ: Проверка токена бота


def validate_bot_token():
    """
    Проверяет валидность токена бота
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or len(token) < 40:
        logger.error("НЕДЕЙСТВИТЕЛЬНЫЙ ТОКЕН БОТА")
        return False

    # Проверяем формат токена Telegram
    if not token.count(":") == 1:
        logger.error("НЕПРАВИЛЬНЫЙ ФОРМАТ ТОКЕНА")
        return False

    logger.info("Токен бота валиден")
    return True


# 🔒 БЕЗОПАСНОСТЬ: Проверка webhook


def validate_webhook_secret(secret_token, request_body, signature):
    """
    Проверяет подпись webhook для безопасности
    """
    if not secret_token:
        return False

    expected_signature = hmac.new(
        secret_token.encode("utf-8"), request_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest("sha256={expected_signature}", signature)


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
    # 🔒 БЕЗОПАСНОСТЬ: Проверяем токен перед созданием приложения
    if not validate_bot_token():
        logger.error("❌ Невозможно создать приложение бота - недействительный токен!")
        return None

    # Создаем приложение бота
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # 🔒 БЕЗОПАСНОСТЬ: Логируем успешное создание
    logger.info("Приложение бота создано с проверкой безопасности")

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))  # type: ignore
    application.add_handler(CommandHandler("help", start))  # type: ignore

    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(start, pattern="start"))
    application.add_handler(CallbackQueryHandler(subjects_menu, pattern="subjects"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="stats"))
    application.add_handler(CallbackQueryHandler(random_task, pattern="random_task"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
    application.add_handler(
        CallbackQueryHandler(learning_plan_menu, pattern="learning_plan")
    )

    # Обработчики для предметов и тем
    application.add_handler(
        CallbackQueryHandler(show_subject_topics, pattern=r"subject_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(show_subject_topics, pattern=r"topic_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(show_subject_topics, pattern=r"random_subject_\d+")
    )

    # Обработчик для показа задания
    application.add_handler(
        CallbackQueryHandler(show_task_handler, pattern=r"show_task_\d+")
    )

    # Новые обработчики для поиска и случайных предметов
    application.add_handler(
        CallbackQueryHandler(search_subject_handler, pattern="search_subject")
    )
    application.add_handler(
        CallbackQueryHandler(random_subject_handler, pattern="random_subject")
    )

    # 🔐 Обработчики аутентификации
    application.add_handler(
        CallbackQueryHandler(telegram_auth_handler, pattern="telegram_auth")
    )
    application.add_handler(
        CallbackQueryHandler(auth_success_handler, pattern="auth_success")
    )

    # Обработчики для ИИ
    application.add_handler(CallbackQueryHandler(ai_help_handler, pattern=r"ai_help"))
    application.add_handler(
        CallbackQueryHandler(ai_help_handler, pattern=r"ai_help_\d+")
    )
    application.add_handler(CallbackQueryHandler(ai_help_handler, pattern=r"ai_chat"))
    application.add_handler(
        CallbackQueryHandler(ai_explain_handler, pattern=r"ai_explain")
    )
    application.add_handler(
        CallbackQueryHandler(ai_personal_handler, pattern=r"ai_personal")
    )
    application.add_handler(
        CallbackQueryHandler(ai_hint_general_handler, pattern=r"ai_hint")
    )
    application.add_handler(
        CallbackQueryHandler(clear_context_handler, pattern="clear_context")
    )

    # Обработчики для заданий
    application.add_handler(CallbackQueryHandler(show_answer, pattern=r"answer_\d+"))

    # 🎮 Обработчики геймификации
    application.add_handler(
        CallbackQueryHandler(gamification_menu_handler, pattern=r"gamification_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(user_stats_handler, pattern=r"stats_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(achievements_handler, pattern=r"achievements_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(progress_handler, pattern=r"progress_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(overall_progress_handler, pattern=r"overall_progress_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(
            subjects_progress_handler, pattern=r"subjects_progress_\d+"
        )
    )
    application.add_handler(
        CallbackQueryHandler(daily_challenges_handler, pattern=r"daily_\d+")
    )
    application.add_handler(
        CallbackQueryHandler(leaderboard_handler, pattern="leaderboard")
    )
    application.add_handler(CallbackQueryHandler(bonus_handler, pattern=r"bonus_\d+"))

    # Обработчик текстовых сообщений (для прямого общения с ИИ и нижнего меню)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Обработчик неизвестных callback-запросов
    application.add_handler(CallbackQueryHandler(handle_unknown_callback))

    logger.info("Telegram бот настроен и готов к работе")
    return application


def main():
    """Основная функция для запуска бота"""
    application = setup_bot_application()

    logger.info("Запуск бота в режиме polling")
    # Явно удаляем webhook, если активен, чтобы избежать 409 Conflict
    try:
        import asyncio

        asyncio.run(
            application.bot.delete_webhook(drop_pending_updates=True)  # type: ignore
        )  # type: ignore
    except Exception:
        pass
    # Стартуем polling и отбрасываем накопившиеся обновления
    application.run_polling(drop_pending_updates=True)  # type: ignore


if __name__ == "__main__":
    """Запуск бота в режиме polling (для разработки)"""
    application = setup_bot_application()

    logger.info("Запуск бота в режиме polling")
    # Явно удаляем webhook, если активен, чтобы избежать 409 Conflict
    try:
        import asyncio

        asyncio.run(
            application.bot.delete_webhook(drop_pending_updates=True)  # type: ignore
        )  # type: ignore
    except Exception:
        pass
    # Стартуем polling и отбрасываем накопившиеся обновления
    application.run_polling(drop_pending_updates=True)  # type: ignore
