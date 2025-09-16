from __future__ import annotations

from typing import Any
from core.container import Container

try:
    from telegram_bot.bot_handlers import (
        db_get_all_subjects_with_tasks as _db_get_all_subjects_with_tasks,  # type: ignore
        db_get_subject_ids as _db_get_subject_ids,  # type: ignore
        db_get_subjects_by_ids as _db_get_subjects_by_ids,  # type: ignore
        db_count_tasks_for_subject as _db_count_tasks_for_subject,  # type: ignore
        db_get_tasks_by_subject as _db_get_tasks_by_subject,  # type: ignore
        db_get_all_tasks as _db_get_all_tasks,  # type: ignore
        db_get_subject_name_for_task as _db_get_subject_name_for_task,  # type: ignore
        db_get_subject_by_id as _db_get_subject_by_id,  # type: ignore
        db_get_subject_name as _db_get_subject_name,  # type: ignore
        db_set_current_task_id as _db_set_current_task_id,  # type: ignore
        db_get_task_by_id as _db_get_task_by_id,  # type: ignore
        get_current_task_id as _get_current_task_id,  # type: ignore
        set_current_task_id as _set_current_task_id,  # type: ignore
    )
except Exception:
    def _db_get_all_subjects_with_tasks():  # type: ignore
        return []

    def _db_get_subject_ids():  # type: ignore
        return []

    def _db_get_subjects_by_ids(ids):  # type: ignore
        return []

    def _db_count_tasks_for_subject(subject_id: int) -> int:  # type: ignore
        return 0

    def _db_get_tasks_by_subject(subject_id: int):  # type: ignore
        return []

    def _db_get_all_tasks():  # type: ignore
        return []

    def _db_get_subject_name_for_task(task):  # type: ignore
        return ''

    def _db_get_subject_by_id(subject_id: int):  # type: ignore
        return None

    def _db_get_subject_name(subject_id: int) -> str:  # type: ignore
        return ''

    def _db_set_current_task_id(user, task_id: int):  # type: ignore
        return None

    def _db_get_task_by_id(task_id: int):  # type: ignore
        return None

    def _get_current_task_id(user):  # type: ignore
        return None

    def _set_current_task_id(user, task_id):  # type: ignore
        return None


# Прокси-функции для обратной совместимости
get_all_subjects_with_tasks = _db_get_all_subjects_with_tasks
get_subject_ids = _db_get_subject_ids
get_subjects_by_ids = _db_get_subjects_by_ids
count_tasks_for_subject = _db_count_tasks_for_subject
get_tasks_by_subject = _db_get_tasks_by_subject
get_all_tasks = _db_get_all_tasks
get_subject_name_for_task = _db_get_subject_name_for_task
get_subject_by_id = _db_get_subject_by_id
get_subject_name = _db_get_subject_name
set_current_task_id = _db_set_current_task_id
get_task_by_id = _db_get_task_by_id
get_current_task_id = _get_current_task_id
set_current_task_id_alt = _set_current_task_id


# Новые функции с использованием контейнера
def get_cache() -> Any:
    """Получает кэш через контейнер зависимостей."""
    return Container.cache()


def get_notifier() -> Any:
    """Получает уведомления через контейнер зависимостей."""
    return Container.notifier()
