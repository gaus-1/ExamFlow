from __future__ import annotations

from typing import Any, Optional
from django.utils import timezone
from core.container import Container

try:
    from telegram_bot.bot_handlers import (
        db_check_connection as _db_check_connection, # type: ignore
        db_get_or_create_unified_profile as _db_get_or_create_unified_profile, # type: ignore
        db_update_profile_activity as _db_update_profile_activity, # type: ignore
        db_get_profile_progress as _db_get_profile_progress, # type: ignore
        db_get_or_create_chat_session as _db_get_or_create_chat_session, # type: ignore
        db_add_user_message_to_session as _db_add_user_message_to_session, # type: ignore
        db_add_assistant_message_to_session as _db_add_assistant_message_to_session, # type: ignore
        db_create_enhanced_prompt as _db_create_enhanced_prompt,
        db_clear_chat_session_context as _db_clear_chat_session_context, # type: ignore
    )
except Exception:
    def _db_check_connection() -> bool:  # type: ignore
        return True

    def _db_get_or_create_unified_profile(telegram_user):  # type: ignore
        return None

    def _db_update_profile_activity(profile):  # type: ignore
        return None

    def _db_get_profile_progress(profile):  # type: ignore
        return {}

    def _db_get_or_create_chat_session(telegram_user, django_user=None):  # type: ignore
        return None

    def _db_add_user_message_to_session(session, message):  # type: ignore
        return None

    def _db_add_assistant_message_to_session(session, message):  # type: ignore
        return None

    def _db_create_enhanced_prompt(user_message, session):  # type: ignore
        return user_message

    def _db_clear_chat_session_context(telegram_user):  # type: ignore
        return None


# Современные функции через Container (вместо legacy прокси)
def check_connection() -> bool:
    """Проверяет подключение к базе данных."""
    try:
        from django.db import connection
        connection.ensure_connection()
        return True
    except Exception:
        return False


def get_cache():
    """Получает кэш через контейнер зависимостей."""
    return Container.cache()


def get_notifier():
    """Получает уведомления через контейнер зависимостей."""
    return Container.notifier()


# Функции удалены - используйте функции выше
