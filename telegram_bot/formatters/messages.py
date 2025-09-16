from __future__ import annotations

"""
Форматтеры сообщений/текста для Telegram-бота.
Тонкие обёртки над текущей логикой, чтобы изолировать представление от обработчиков.
"""
from typing import Any

try:
    # Импортируем существующие функции, чтобы сохранить текущее поведение
    from telegram_bot.bot_handlers import (
        create_main_message as _create_main_message,
        create_warning_message as _create_warning_message,
        clean_markdown_text as _clean_markdown_text,
    )
except Exception:
    # При проблемах импорта оставляем безопасные заглушки
    def _create_main_message(text: str) -> str:  # type: ignore
        return text

    def _create_warning_message(text: str) -> str:  # type: ignore
        return f"⚠️ {text}"

    def _clean_markdown_text(text: str) -> str:  # type: ignore
        return text


def clean_markdown_text(text: str) -> str:
    return _clean_markdown_text(text)


def create_main_message(text: str) -> str:
    return _create_main_message(text)


def create_warning_message(text: str) -> str:
    return _create_warning_message(text)
