"""
Менеджер очков и уровней (Single Responsibility: управление очками)
"""

import logging

from asgiref.sync import sync_to_async

from core.models import UnifiedProfile

logger = logging.getLogger(__name__)


class PointsManager:
    """Управляет начислением очков и уровнями пользователей"""

    def __init__(self):
        self.points_per_correct = 10  # Очки за правильный ответ
        self.points_per_streak = 5  # Бонус за серию правильных ответов
        self.level_multiplier = 100  # Множитель для уровня

    @sync_to_async
    def add_points(self, user_id: int, points: int, reason: str = "Задание") -> dict:
        """Добавляет очки пользователю"""
        try:
            profile, created = UnifiedProfile.objects.get_or_create(  # type: ignore
                telegram_id=user_id, defaults={"telegram_id": user_id}
            )

            # Добавляем очки
            profile.points = (profile.points or 0) + points
            profile.total_points = (profile.total_points or 0) + points

            # Проверяем повышение уровня
            old_level = profile.level or 1
            new_level = self._calculate_level(profile.points)

            level_up = False
            if new_level > old_level:
                profile.level = new_level
                level_up = True

            profile.save()

            return {
                "success": True,
                "points_added": points,
                "total_points": profile.points,
                "level": profile.level,
                "level_up": level_up,
                "reason": reason,
            }

        except Exception as e:
            logger.error(f"Ошибка добавления очков: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_level(self, points: int) -> int:
        """Вычисляет уровень на основе очков"""
        if not points:
            return 1
        return max(1, (points // self.level_multiplier) + 1)

    @sync_to_async
    def get_user_stats(self, user_id: int) -> dict:
        """Получает статистику пользователя"""
        try:
            profile = UnifiedProfile.objects.get(telegram_id=user_id)  # type: ignore

            return {
                "points": profile.points or 0,
                "total_points": profile.total_points or 0,
                "level": profile.level or 1,
                "correct_answers": profile.correct_answers or 0,
                "total_answers": profile.total_answers or 0,
                "accuracy": self._calculate_accuracy(
                    profile.correct_answers or 0, profile.total_answers or 0
                ),
            }
        except UnifiedProfile.DoesNotExist:  # type: ignore
            return {
                "points": 0,
                "total_points": 0,
                "level": 1,
                "correct_answers": 0,
                "total_answers": 0,
                "accuracy": 0.0,
            }

    def _calculate_accuracy(self, correct: int, total: int) -> float:
        """Вычисляет точность ответов"""
        if total == 0:
            return 0.0
        return round((correct / total) * 100, 1)
