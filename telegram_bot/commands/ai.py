from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import ai_explain_handler as _ai_explain_handler
    from telegram_bot.bot_handlers import ai_help_handler as _ai_help_handler
    from telegram_bot.bot_handlers import (
        ai_hint_general_handler as _ai_hint_general_handler,
    )
    from telegram_bot.bot_handlers import ai_personal_handler as _ai_personal_handler
    from telegram_bot.bot_handlers import (
        clear_context_handler as _clear_context_handler,
    )
    from telegram_bot.bot_handlers import handle_text_message as _handle_text_message
except Exception:

    async def _ai_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("AI помощь временно недоступна")  # type: ignore

    async def _ai_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("AI объяснение временно недоступно")  # type: ignore

    async def _ai_personal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("AI персонализация временно недоступна")  # type: ignore

    async def _ai_hint_general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("AI подсказка временно недоступна")  # type: ignore

    async def _handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Ответ ИИ временно недоступен")  # type: ignore

    async def _clear_context_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message("Контекст не очищен")  # type: ignore


async def ai_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _ai_help_handler(update, context)


async def ai_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _ai_explain_handler(update, context)


async def ai_personal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _ai_personal_handler(update, context)


async def ai_hint_general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _ai_hint_general_handler(update, context)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_text_message(update, context)


async def clear_context_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _clear_context_handler(update, context)
