"""
Сервис для дашборда персонализации
Применяет принцип Single Responsibility Principle (SRP)
"""

import logging
from typing import Dict, Any, List
from django.contrib.auth.models import User

from ..personalization_system import (
    get_user_insights,
    PersonalizedRecommendations
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Сервис для подготовки данных дашборда персонализации"""
    
    def __init__(self, user: User):
        self.user = user
        self._recommender = None
    
    @property
    def recommender(self) -> PersonalizedRecommendations:
        """Ленивая инициализация рекомендателя"""
        if self._recommender is None:
            self._recommender = PersonalizedRecommendations(self.user.id)
        return self._recommender
    
    def get_user_insights(self) -> Dict[str, Any]:
        """Получить аналитику пользователя"""
        try:
            return get_user_insights(self.user.id)
        except Exception as e:
            logger.error(f"Ошибка получения аналитики для пользователя {self.user.id}: {e}")
            return {}
    
    def get_recommended_tasks(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Получить рекомендованные задачи"""
        try:
            return self.recommender.get_recommended_tasks(limit)
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций для пользователя {self.user.id}: {e}")
            return []
    
    def get_study_plan(self) -> Dict[str, Any]:
        """Получить план обучения"""
        try:
            return self.recommender.get_study_plan()
        except Exception as e:
            logger.error(f"Ошибка получения плана обучения для пользователя {self.user.id}: {e}")
            return {}
    
    def get_weak_topics(self) -> List[Dict[str, Any]]:
        """Получить слабые темы"""
        try:
            return self.recommender.get_weak_topics()
        except Exception as e:
            logger.error(f"Ошибка получения слабых тем для пользователя {self.user.id}: {e}")
            return []
    
    def build_dashboard_context(self) -> Dict[str, Any]:
        """Построить контекст для дашборда"""
        return {
            'user_insights': self.get_user_insights(),
            'recommended_tasks': self.get_recommended_tasks(),
            'study_plan': self.get_study_plan(),
            'weak_topics': self.get_weak_topics(),
            'page_title': 'Персонализация - ExamFlow'
        }
