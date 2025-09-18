#!/usr/bin/env python3
"""
ExamFlow Telegram Bot - 24/7 версия с автоперезапуском
Надежная работа с обработкой ошибок и мониторингом
"""

import os
import sys
import logging
import signal
import asyncio
from datetime import datetime
from typing import Optional

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram.ext import Application, ApplicationBuilder
from telegram_bot.bot_handlers import (
    start, subjects_menu, show_subject_topics,
    show_stats, handle_unknown_callback,
    random_task, show_answer, ai_help_handler,
    ai_explain_handler, ai_personal_handler, ai_hint_general_handler,
    handle_text_message, learning_plan_menu, search_subject_handler,
    random_subject_handler, show_task_handler, gamification_menu_handler,
    user_stats_handler, achievements_handler, progress_handler,
    overall_progress_handler, subjects_progress_handler, daily_challenges_handler,
    leaderboard_handler, bonus_handler, clear_context_handler,
    telegram_auth_handler, auth_success_handler, main_menu,
    handle_ai_message, handle_menu_button
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot_24_7.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ExamFlowBot24_7:
    """
    24/7 Telegram бот с автоперезапуском и мониторингом
    """

    def __init__(self):
        self.token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.application: Optional[Application] = None
        self.is_running = False
        self.restart_count = 0
        self.max_restarts = 10
        self.start_time = datetime.now()

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в настройках")

    async def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        if not self.application:
            return

        # Команды
        self.application.add_handler(CommandHandler('start', start))
        self.application.add_handler(CommandHandler('help', start))
        self.application.add_handler(CommandHandler('menu', main_menu))
        self.application.add_handler(CommandHandler('subjects', subjects_menu))
        self.application.add_handler(CommandHandler('stats', show_stats))
        self.application.add_handler(CommandHandler('ai', ai_help_handler))

        # Callback queries (кнопки)
        self.application.add_handler(CallbackQueryHandler(subjects_menu, pattern=r'^subjects$'))
        self.application.add_handler(CallbackQueryHandler(show_subject_topics, pattern=r'^subject_\d+$'))
        self.application.add_handler(CallbackQueryHandler(random_task, pattern=r'^random_task$'))
        self.application.add_handler(CallbackQueryHandler(show_answer, pattern=r'^show_answer_\d+$'))
        self.application.add_handler(CallbackQueryHandler(show_stats, pattern=r'^stats$'))
        self.application.add_handler(CallbackQueryHandler(learning_plan_menu, pattern=r'^learning_plan$'))

        # AI обработчики
        self.application.add_handler(CallbackQueryHandler(ai_help_handler, pattern=r'^ai_help$'))
        self.application.add_handler(CallbackQueryHandler(ai_explain_handler, pattern=r'^ai_explain_\d+$'))
        self.application.add_handler(CallbackQueryHandler(ai_personal_handler, pattern=r'^ai_personal$'))
        self.application.add_handler(CallbackQueryHandler(ai_hint_general_handler, pattern=r'^ai_hint_general$'))

        # Геймификация
        self.application.add_handler(CallbackQueryHandler(gamification_menu_handler, pattern=r'^gamification$'))
        self.application.add_handler(CallbackQueryHandler(user_stats_handler, pattern=r'^user_stats$'))
        self.application.add_handler(CallbackQueryHandler(achievements_handler, pattern=r'^achievements$'))
        self.application.add_handler(CallbackQueryHandler(progress_handler, pattern=r'^progress$'))
        self.application.add_handler(CallbackQueryHandler(overall_progress_handler, pattern=r'^overall_progress$'))
        self.application.add_handler(CallbackQueryHandler(subjects_progress_handler, pattern=r'^subjects_progress$'))
        self.application.add_handler(CallbackQueryHandler(daily_challenges_handler, pattern=r'^daily_challenges$'))
        self.application.add_handler(CallbackQueryHandler(leaderboard_handler, pattern=r'^leaderboard$'))
        self.application.add_handler(CallbackQueryHandler(bonus_handler, pattern=r'^bonus$'))

        # Поиск и навигация
        self.application.add_handler(CallbackQueryHandler(search_subject_handler, pattern=r'^search_subject_'))
        self.application.add_handler(CallbackQueryHandler(random_subject_handler, pattern=r'^random_subject_\d+$'))
        self.application.add_handler(CallbackQueryHandler(show_task_handler, pattern=r'^task_\d+$'))
        self.application.add_handler(CallbackQueryHandler(clear_context_handler, pattern=r'^clear_context$'))

        # Авторизация
        self.application.add_handler(CallbackQueryHandler(telegram_auth_handler, pattern=r'^telegram_auth$'))
        self.application.add_handler(CallbackQueryHandler(auth_success_handler, pattern=r'^auth_success$'))

        # Главное меню и кнопки
        self.application.add_handler(CallbackQueryHandler(main_menu, pattern=r'^main_menu$'))
        # type: ignore  # Игнорируем ошибку типов из-за лишнего параметра button_text
        self.application.add_handler(CallbackQueryHandler(handle_menu_button, pattern=r'^menu_'))  # type: ignore

        # Обработка неизвестных callback
        self.application.add_handler(CallbackQueryHandler(handle_unknown_callback))
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

        # AI сообщения
        self.application.add_handler(MessageHandler(filters.TEXT, handle_ai_message))

        logger.info("✅ Все обработчики настроены")

    async def error_handler(self, update, context):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке обновления {update}: {context.error}")

        # Отправляем уведомление пользователю при возможности
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="😔 Произошла ошибка. Попробуйте еще раз или обратитесь в поддержку."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    async def health_check(self):
        """Проверка состояния бота"""
        try:
            if self.application and self.application.bot:
                me = await self.application.bot.get_me()
                logger.info(f"✅ Бот здоров: @{me.username} (ID: {me.id})")
                return True
        except Exception as e:
            logger.error(f"❌ Проблема со здоровьем бота: {e}")
            return False
        return False

    async def start_bot(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск ExamFlow Bot 24/7...")

            # Создаем приложение
            self.application = ApplicationBuilder().token(self.token).build()

            # Настраиваем обработчики
            await self.setup_handlers()

            # Добавляем обработчик ошибок
            self.application.add_error_handler(self.error_handler)

            # Проверяем здоровье
            if not await self.health_check():
                raise Exception("Бот не прошел проверку здоровья")

            # Запускаем бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)

            self.is_running = True
            uptime = datetime.now() - self.start_time
            logger.info(f"✅ Бот успешно запущен! Uptime: {uptime}")

            # Бесконечный цикл с периодическими проверками
            while self.is_running:
                await asyncio.sleep(300)  # Проверка каждые 5 минут
                await self.health_check()

        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            await self.restart_bot()

    async def stop_bot(self):
        """Остановка бота"""
        logger.info("🛑 Остановка бота...")
        self.is_running = False

        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("✅ Бот остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")

    async def restart_bot(self):
        """Перезапуск бота"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ Превышено максимальное количество перезапусков ({self.max_restarts})")
            return

        self.restart_count += 1
        logger.warning(f"🔄 Перезапуск бота #{self.restart_count}")

        await self.stop_bot()
        await asyncio.sleep(5)  # Ждем 5 секунд
        await self.start_bot()

    def signal_handler(self, signum, frame):
        """Обработчик системных сигналов"""
        logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.is_running = False


# Импорты для обработчиков
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters


async def main():
    """Главная функция"""
    bot = ExamFlowBot24_7()

    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, bot.signal_handler)
    signal.signal(signal.SIGTERM, bot.signal_handler)

    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения от пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.stop_bot()


if __name__ == "__main__":
    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)

    # Запускаем бота
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        sys.exit(1)
