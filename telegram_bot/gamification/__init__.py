"""
Модуль геймификации для Telegram бота

Разделен по принципу Single Responsibility:
- PointsManager: управление очками и уровнями
- AchievementsManager: управление достижениями
- TelegramGamification: координация (фасад)
"""

from .points_manager import PointsManager
from .achievements_manager import AchievementsManager

__all__ = ['PointsManager', 'AchievementsManager', 'TelegramGamification']


class TelegramGamification:
    """
    Фасад для геймификации (координирует работу менеджеров)
    Соблюдает принцип единственной ответственности
    """
    
    def __init__(self):
        self.points_manager = PointsManager()
        self.achievements_manager = AchievementsManager()

    async def process_correct_answer(self, user_id: int) -> dict:  # type: ignore
        """Обрабатывает правильный ответ пользователя"""
        # Добавляем очки
        points_result = await self.points_manager.add_points(
            user_id, 
            self.points_manager.points_per_correct, 
            "Правильный ответ"
        )
        
        # Проверяем достижения
        new_achievements = await self.achievements_manager.check_achievements(user_id)
        
        return {
            'points': points_result,
            'achievements': new_achievements,
            'level_up': points_result.get('level_up', False)
        }

    async def get_user_profile(self, user_id: int) -> Dict:  # type: ignore
        """Получает полный профиль пользователя"""
        stats = await self.points_manager.get_user_stats(user_id)
        achievements = await self.achievements_manager.get_user_achievements(user_id)
        
        return {
            'stats': stats,
            'achievements': achievements,
            'achievements_count': len(achievements)
        }
