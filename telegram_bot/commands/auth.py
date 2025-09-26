from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import (
        auth_success_handler as _legacy_auth_success_handler,
    )
    from telegram_bot.bot_handlers import (
        telegram_auth_handler as _legacy_telegram_auth_handler,
    )
except Exception:

    async def _legacy_telegram_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Авторизация недоступна")  # type: ignore

    async def _legacy_auth_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Авторизация завершена")  # type: ignore


async def telegram_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _legacy_telegram_auth_handler(update, context)


async def auth_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _legacy_auth_success_handler(update, context)
