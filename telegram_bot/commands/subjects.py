from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import subjects_menu as _legacy_subjects_menu
except Exception:

    async def _legacy_subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Список предметов недоступен")  # type: ignore


async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _legacy_subjects_menu(update, context)
