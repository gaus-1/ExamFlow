from __future__ import annotations

from typing import Any
from core.container import Container

try:
    from telegram_bot.bot_handlers import (
        db_save_progress as _legacy_save_progress,  # type: ignore
        db_update_rating_points as _legacy_update_rating_points,  # type: ignore
        db_get_profile_progress as _legacy_get_profile_progress,  # type: ignore
    )
except Exception:
    def _legacy_save_progress(user, task, user_answer: str, is_correct: bool):  # type: ignore
        return None

    def _legacy_update_rating_points(user, is_correct: bool):  # type: ignore
        return None

    def _legacy_get_profile_progress(profile):  # type: ignore
        return {}


# Прокси-функции для обратной совместимости
def save_progress(user, task, user_answer: str, is_correct: bool):
    _legacy_save_progress(user, task, user_answer, is_correct)


def update_rating_points(user, is_correct: bool):
    _legacy_update_rating_points(user, is_correct)


def get_profile_progress(profile):
    return _legacy_get_profile_progress(profile)


# Новые функции с использованием контейнера
def get_cache() -> Any:
    """Получает кэш через контейнер зависимостей."""
    return Container.cache()


def get_notifier() -> Any:
    """Получает уведомления через контейнер зависимостей."""
    return Container.notifier()
