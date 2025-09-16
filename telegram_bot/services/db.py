from __future__ import annotations

from typing import Any, Optional
from django.utils import timezone

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


check_connection = _db_check_connection
get_or_create_unified_profile = _db_get_or_create_unified_profile
update_profile_activity = _db_update_profile_activity
get_profile_progress = _db_get_profile_progress
get_or_create_chat_session = _db_get_or_create_chat_session
add_user_message_to_session = _db_add_user_message_to_session
add_assistant_message_to_session = _db_add_assistant_message_to_session
create_enhanced_prompt = _db_create_enhanced_prompt
clear_chat_session_context = _db_clear_chat_session_context
