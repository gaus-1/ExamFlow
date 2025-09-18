"""
Менеджер достижений (Single Responsibility: управление достижениями)
"""

from typing import Dict, List
from asgiref.sync import sync_to_async
from core.models import UnifiedProfile
import logging

logger = logging.getLogger(__name__)


class AchievementsManager:
    """Управляет достижениями пользователей"""
    
    def __init__(self):
        self.achievements_config = {
            'first_correct': {
                'title': '🎯 Первый успех',
                'description': 'Правильно ответил на первое задание',
                'points': 25
            },
            'streak_5': {
                'title': '🔥 Серия 5',
                'description': 'Правильно ответил на 5 заданий подряд',
                'points': 50
            },
            'streak_10': {
                'title': '🚀 Серия 10',
                'description': 'Правильно ответил на 10 заданий подряд',
                'points': 100
            },
            'level_5': {
                'title': '⭐ Уровень 5',
                'description': 'Достиг 5-го уровня',
                'points': 200
            },
            'daily_learner': {
                'title': '📅 Ежедневное обучение',
                'description': 'Занимался каждый день в течение недели',
                'points': 150
            }
        }

    @sync_to_async
    def check_achievements(self, user_id: int) -> List[Dict]:
        """Проверяет и выдает новые достижения"""
        try:
            profile = UnifiedProfile.objects.get(telegram_id=user_id)  # type: ignore
            new_achievements = []
            
            # Проверяем каждое достижение
            for achievement_key, config in self.achievements_config.items():
                if not self._has_achievement(profile, achievement_key):
                    if self._check_achievement_condition(profile, achievement_key):
                        # Выдаем достижение
                        self._grant_achievement(profile, achievement_key)
                        new_achievements.append({
                            'key': achievement_key,
                            'title': config['title'],
                            'description': config['description'],
                            'points': config['points']
                        })
            
            return new_achievements
            
        except UnifiedProfile.DoesNotExist:  # type: ignore
            return []
        except Exception as e:
            logger.error(f"Ошибка проверки достижений: {e}")
            return []

    def _has_achievement(self, profile, achievement_key: str) -> bool:
        """Проверяет, есть ли уже достижение у пользователя"""
        achievements = profile.achievements or {}
        return achievement_key in achievements

    def _check_achievement_condition(self, profile, achievement_key: str) -> bool:
        """Проверяет условие для получения достижения"""
        if achievement_key == 'first_correct':
            return (profile.correct_answers or 0) >= 1
        elif achievement_key == 'streak_5':
            return (profile.current_streak or 0) >= 5
        elif achievement_key == 'streak_10':
            return (profile.current_streak or 0) >= 10
        elif achievement_key == 'level_5':
            return (profile.level or 1) >= 5
        elif achievement_key == 'daily_learner':
            # Упрощенная проверка - можно улучшить
            return (profile.total_answers or 0) >= 7
        
        return False

    def _grant_achievement(self, profile, achievement_key: str):
        """Выдает достижение пользователю"""
        if not profile.achievements:
            profile.achievements = {}
        
        profile.achievements[achievement_key] = {
            'granted_at': profile.updated_at.isoformat() if profile.updated_at else None,
            'points_earned': self.achievements_config[achievement_key]['points']
        }
        
        # Добавляем очки за достижение
        achievement_points = self.achievements_config[achievement_key]['points']
        profile.points = (profile.points or 0) + achievement_points
        profile.total_points = (profile.total_points or 0) + achievement_points
        
        profile.save()

    @sync_to_async
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получает все достижения пользователя"""
        try:
            profile = UnifiedProfile.objects.get(telegram_id=user_id)  # type: ignore
            achievements = profile.achievements or {}
            
            result = []
            for key, data in achievements.items():
                if key in self.achievements_config:
                    config = self.achievements_config[key]
                    result.append({
                        'key': key,
                        'title': config['title'],
                        'description': config['description'],
                        'granted_at': data.get('granted_at'),
                        'points_earned': data.get('points_earned', 0)
                    })
            
            return result
            
        except UnifiedProfile.DoesNotExist:  # type: ignore
            return []
