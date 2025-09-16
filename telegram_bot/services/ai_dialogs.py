from __future__ import annotations

from typing import Optional

try:
    from telegram_bot.bot_handlers import (
        get_ai_response as _legacy_get_ai_response,  # type: ignore
        db_create_enhanced_prompt as _legacy_create_enhanced_prompt,  # type: ignore
        db_add_user_message_to_session as _legacy_add_user_message,  # type: ignore
        db_add_assistant_message_to_session as _legacy_add_assistant_message,  # type: ignore
        db_get_or_create_chat_session as _legacy_get_or_create_chat_session,  # type: ignore
    )
except Exception:
    def _legacy_get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:  # type: ignore
        return 'Сервис ИИ временно недоступен'

    def _legacy_create_enhanced_prompt(user_message: str, session) -> str:  # type: ignore
        return user_message

    def _legacy_add_user_message(session, message):  # type: ignore
        return None

    def _legacy_add_assistant_message(session, message):  # type: ignore
        return None

    def _legacy_get_or_create_chat_session(telegram_user, django_user=None):  # type: ignore
        return None


# Фасадные функции (тонкие обёртки)

def get_or_create_chat_session(telegram_user, django_user=None):  # type: ignore
    return _legacy_get_or_create_chat_session(telegram_user, django_user)


def create_enhanced_prompt(user_message: str, session) -> str:
    return _legacy_create_enhanced_prompt(user_message, session)


def add_user_message_to_session(session, message) -> None:
    _legacy_add_user_message(session, message)


def add_assistant_message_to_session(session, message) -> None:
    _legacy_add_assistant_message(session, message)


def get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:
    return _legacy_get_ai_response(prompt, task_type=task_type, user=user, task=task)
