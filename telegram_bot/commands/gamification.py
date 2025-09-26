from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import achievements_handler as _achievements_handler
    from telegram_bot.bot_handlers import bonus_handler as _bonus_handler
    from telegram_bot.bot_handlers import (
        daily_challenges_handler as _daily_challenges_handler,
    )
    from telegram_bot.bot_handlers import (
        gamification_menu_handler as _gamification_menu_handler,
    )
    from telegram_bot.bot_handlers import (
        handle_unknown_callback as _handle_unknown_callback,
    )
    from telegram_bot.bot_handlers import leaderboard_handler as _leaderboard_handler
    from telegram_bot.bot_handlers import (
        overall_progress_handler as _overall_progress_handler,
    )
    from telegram_bot.bot_handlers import progress_handler as _progress_handler
    from telegram_bot.bot_handlers import show_stats as _show_stats
    from telegram_bot.bot_handlers import (
        subjects_progress_handler as _subjects_progress_handler,
    )
    from telegram_bot.bot_handlers import user_stats_handler as _user_stats_handler
except Exception:

    async def _gamification_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Геймификация недоступна")  # type: ignore

    async def _user_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Статистика недоступна")  # type: ignore

    async def _achievements_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Достижения недоступны")  # type: ignore

    async def _progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Прогресс недоступен")  # type: ignore

    async def _overall_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Общий прогресс недоступен")  # type: ignore

    async def _subjects_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Прогресс по предметам недоступен")  # type: ignore

    async def _daily_challenges_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Ежедневные челленджи недоступны")  # type: ignore

    async def _leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Таблица лидеров недоступна")  # type: ignore

    async def _bonus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Бонус недоступен")  # type: ignore

    async def _show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Статистика недоступна")  # type: ignore

    async def _handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Неизвестная команда")  # type: ignore


async def gamification_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _gamification_menu_handler(update, context)


async def user_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _user_stats_handler(update, context)


async def achievements_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _achievements_handler(update, context)


async def progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _progress_handler(update, context)


async def overall_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _overall_progress_handler(update, context)


async def subjects_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _subjects_progress_handler(update, context)


async def daily_challenges_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _daily_challenges_handler(update, context)


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _leaderboard_handler(update, context)


async def bonus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _bonus_handler(update, context)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _show_stats(update, context)


async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_unknown_callback(update, context)
