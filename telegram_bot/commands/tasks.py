from __future__ import annotations

from telegram import Update  # type: ignore
from telegram.ext import ContextTypes  # type: ignore

try:
    from telegram_bot.bot_handlers import (
        show_subject_topics as _show_subject_topics,
        random_task as _random_task,
        show_answer as _show_answer,
        show_task_handler as _show_task_handler,
        search_subject_handler as _search_subject_handler,
        random_subject_handler as _random_subject_handler,
    )
except Exception:
    async def _show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Темы недоступны')  # type: ignore

    async def _random_task(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Случайная задача недоступна')  # type: ignore

    async def _show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Ответ недоступен')  # type: ignore

    async def _show_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Задача недоступна')  # type: ignore

    async def _search_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Поиск предметов недоступен')  # type: ignore

    async def _random_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        await update.effective_chat.send_message('Случайный предмет недоступен')  # type: ignore


async def show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _show_subject_topics(update, context)


async def random_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _random_task(update, context)


async def show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _show_answer(update, context)


async def show_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _show_task_handler(update, context)


async def search_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _search_subject_handler(update, context)


async def random_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _random_subject_handler(update, context)
