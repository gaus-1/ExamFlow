"""
Unified Profile Service - управление профилями пользователей
"""

import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()


class UnifiedProfileService:
    """Сервис для работы с унифицированными профилями пользователей"""

    @staticmethod
    def get_or_create_profile(telegram_id: int, telegram_username: str = None, user=None):  # type: ignore
        """
        Получает или создает профиль пользователя

        Args:
            telegram_id: ID пользователя в Telegram
            telegram_username: Username в Telegram
            user: Django User (опционально)

        Returns:
            Профиль пользователя
        """
        try:
            from core.models import UserProfile

            # Ищем существующий профиль по telegram_id
            profile = UserProfile.objects.filter(telegram_id=telegram_id).first()  # type: ignore

            if profile:
                # Обновляем username если изменился
                if telegram_username and profile.telegram_username != telegram_username:
                    profile.telegram_username = telegram_username
                    profile.save()

                logger.debug(
                    f"Найден существующий профиль для telegram_id={telegram_id}"
                )
                return profile

            # Создаем новый профиль
            with transaction.atomic():
                # Создаем Django пользователя если нужно
                if not user and telegram_username:
                    user = UnifiedProfileService._get_or_create_django_user(
                        telegram_username, telegram_id
                    )

                profile = UserProfile.objects.create(  # type: ignore
                    user=user,
                    telegram_id=telegram_id,
                    telegram_username=telegram_username or f"user_{telegram_id}",
                )

                logger.info(f"Создан новый профиль для telegram_id={telegram_id}")
                return profile

        except Exception as e:
            logger.error(f"Ошибка создания профиля для telegram_id={telegram_id}: {e}")
            # Возвращаем минимальный объект-заглушку
            return UnifiedProfileService._create_mock_profile(
                telegram_id, telegram_username
            )

    @staticmethod
    def _get_or_create_django_user(username: str, telegram_id: int):
        """Создает Django пользователя для Telegram пользователя"""
        try:
            # Проверяем есть ли уже пользователь с таким telegram_id
            user = User.objects.filter(telegram_id=telegram_id).first()
            if user:
                return user

            # Создаем нового пользователя
            unique_username = (
                f"tg_{telegram_id}_{username}" if username else f"tg_{telegram_id}"
            )

            user = User.objects.create_user(username=unique_username)

            logger.info(f"Создан Django пользователь: {unique_username}")
            return user

        except Exception as e:
            logger.error(f"Ошибка создания Django пользователя: {e}")
            return None

    @staticmethod
    def _create_mock_profile(telegram_id: int, telegram_username: str = None):  # type: ignore
        """Создает объект-заглушку профиля для аварийных случаев"""

        class MockProfile:
            def __init__(self):
                self.id = telegram_id
                self.telegram_id = telegram_id
                self.telegram_username = telegram_username or f"user_{telegram_id}"
                self.user = None

            def save(self):
                pass

        return MockProfile()

    @staticmethod
    def update_profile_activity(profile, activity_type: str = "message"):
        """Обновляет активность профиля"""
        try:
            if hasattr(profile, "save"):
                from django.utils import timezone

                # Если есть поле last_activity - обновляем
                if hasattr(profile, "last_activity"):
                    profile.last_activity = timezone.now()
                profile.save()

                logger.debug(
                    f"Обновлена активность профиля {profile.telegram_id}: {activity_type}"
                )

        except Exception as e:
            logger.error(f"Ошибка обновления активности профиля: {e}")

    @staticmethod
    def get_profile_progress(profile) -> dict[str, Any]:
        """Получает прогресс профиля"""
        try:
            from learning.models import UserProgress

            if not profile or not hasattr(profile, "user") or not profile.user:
                return {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "success_rate": 0,
                    "current_streak": 0,
                }

            progress = UserProgress.objects.filter(user=profile.user)  # type: ignore
            total_tasks = progress.count()
            completed_tasks = progress.filter(is_completed=True).count()

            success_rate = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "success_rate": round(success_rate, 1),
                "current_streak": 0,  # TODO: реализовать подсчет серии
            }

        except Exception as e:
            logger.error(f"Ошибка получения прогресса профиля: {e}")
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "success_rate": 0,
                "current_streak": 0,
            }
