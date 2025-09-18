"""
Современный сервис для работы с пользователями Telegram бота.
Объединяет всю логику управления пользователями в одном месте.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Dict
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import sync_to_async

from core.models import UnifiedProfile, UserProfile
from learning.models import UserRating

logger = logging.getLogger(__name__)
User = get_user_model()


class TelegramUserService:
    """
    Сервис для работы с пользователями Telegram бота.
    Следует принципам SOLID и современным стандартам.
    """

    @staticmethod
    @sync_to_async
    def get_or_create_user(telegram_user) -> tuple[Any, bool]:
        """
        Получить или создать пользователя Django с профилем.
        
        Args:
            telegram_user: Объект пользователя Telegram
            
        Returns:
            Кортеж (пользователь, создан_ли_новый)
        """
        try:
            user, created = User.objects.get_or_create(  # type: ignore
                telegram_id=telegram_user.id,
                defaults={
                    'telegram_first_name': telegram_user.first_name or '',
                    'telegram_last_name': telegram_user.last_name or '',
                    'telegram_username': telegram_user.username or '',
                }
            )

            # Создаем профиль если нужно
            profile, profile_created = UserProfile.objects.get_or_create(  # type: ignore
                user=user,
                defaults={}
            )

            # Создаем рейтинг если нужно
            rating, rating_created = UserRating.objects.get_or_create(user=user)  # type: ignore

            if created:
                logger.info(f"Создан новый пользователь: {telegram_user.id}")

            return user, created

        except Exception as e:
            logger.error(f"Ошибка создания пользователя {telegram_user.id}: {e}")
            raise

    @staticmethod
    @sync_to_async
    def get_user_profile(user) -> Optional[Any]:
        """
        Получает профиль пользователя.
        
        Args:
            user: Django пользователь
            
        Returns:
            Профиль пользователя или None
        """
        try:
            return UnifiedProfile.objects.get(user=user)  # type: ignore
        except UnifiedProfile.DoesNotExist:  # type: ignore
            return None
        except Exception as e:
            logger.error(f"Ошибка получения профиля {user.id}: {e}")
            return None

    @staticmethod
    @sync_to_async
    def update_user_activity(user) -> None:
        """
        Обновляет время последней активности пользователя.
        
        Args:
            user: Django пользователь
        """
        try:
            profile = UnifiedProfile.objects.get(user=user)  # type: ignore
            profile.last_activity = timezone.now()  # type: ignore
            profile.save()  # type: ignore

        except UnifiedProfile.DoesNotExist:  # type: ignore
            # Создаем профиль если не существует
            UnifiedProfile.objects.create(user=user, last_activity=timezone.now())  # type: ignore

        except Exception as e:
            logger.error(f"Ошибка обновления активности {user.id}: {e}")

    @staticmethod
    @sync_to_async
    def get_user_stats(user) -> Dict[str, Any]:
        """
        Получает статистику пользователя.
        
        Args:
            user: Django пользователь
            
        Returns:
            Словарь со статистикой
        """
        try:
            from learning.models import UserProgress

            # Получаем прогресс
            progress_count = UserProgress.objects.filter(user=user).count()  # type: ignore

            # Получаем рейтинг
            try:
                rating = UserRating.objects.get(user=user)  # type: ignore
                points = rating.total_points  # type: ignore
                level = rating.level  # type: ignore
            except UserRating.DoesNotExist:  # type: ignore
                points = 0
                level = 1

            return {
                'progress_count': progress_count,
                'total_points': points,
                'level': level,
                'tasks_solved': progress_count,  # Упрощение
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики {user.id}: {e}")
            return {
                'progress_count': 0,
                'total_points': 0,
                'level': 1,
                'tasks_solved': 0,
            }

    @staticmethod
    @sync_to_async
    def save_user_progress(user, task, answer: str, is_correct: bool) -> None:
        """
        Сохраняет прогресс пользователя по задаче.
        
        Args:
            user: Django пользователь
            task: Задача
            answer: Ответ пользователя
            is_correct: Правильность ответа
        """
        try:
            from learning.models import UserProgress

            # Создаем или обновляем прогресс
            progress, created = UserProgress.objects.get_or_create(  # type: ignore
                user=user,
                task=task,
                defaults={
                    'user_answer': answer,
                    'is_correct': is_correct,
                    'completed_at': timezone.now(),
                }
            )

            if not created:
                # Обновляем существующий прогресс
                progress.user_answer = answer  # type: ignore
                progress.is_correct = is_correct  # type: ignore
                progress.completed_at = timezone.now()  # type: ignore
                progress.save()  # type: ignore

            # Обновляем рейтинг
            if is_correct:
                TelegramUserService.update_user_rating(user, 10)  # 10 очков за правильный ответ

            logger.info(f"Сохранен прогресс пользователя {user.id} по задаче {task.id}")

        except Exception as e:
            logger.error(f"Ошибка сохранения прогресса {user.id}: {e}")

    @staticmethod
    @sync_to_async
    def update_user_rating(user, points: int) -> None:
        """
        Обновляет рейтинг пользователя.
        
        Args:
            user: Django пользователь
            points: Количество очков для добавления
        """
        try:
            rating, created = UserRating.objects.get_or_create(user=user)  # type: ignore

            rating.total_points += points  # type: ignore

            # Простая формула уровня
            rating.level = min(rating.total_points // 100 + 1, 100)  # type: ignore

            rating.save()  # type: ignore

            logger.info(f"Обновлен рейтинг пользователя {user.id}: +{points} очков")

        except Exception as e:
            logger.error(f"Ошибка обновления рейтинга {user.id}: {e}")


# Глобальный экземпляр сервиса
user_service = TelegramUserService()
