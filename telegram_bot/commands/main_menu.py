from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import main_menu as _legacy_main_menu
except Exception:

    async def _legacy_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Главное меню недоступно")  # type: ignore


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Делегируем в существующую реализацию — постепенная миграция
    return await _legacy_main_menu(update, context)
