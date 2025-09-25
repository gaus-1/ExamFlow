"""
Сервис для работы с пользователями Telegram бота
Применяет принцип Single Responsibility Principle (SRP)
"""

import logging
from typing import Dict, Any, Optional
from telegram import User as TelegramUser
from telegram_auth.models import TelegramUser as DjangoUser

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями бота"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_or_create_user(self, telegram_user: TelegramUser) -> DjangoUser:
        """Получить или создать пользователя Django"""
        try:
            user, created = DjangoUser.objects.get_or_create(
                telegram_id=telegram_user.id,
                defaults={
                    'username': telegram_user.username or f"user_{telegram_user.id}",
                    'first_name': telegram_user.first_name or "",
                    'last_name': telegram_user.last_name or "",
                    'is_active': True,
                }
            )
            
            if created:
                self.logger.info(f"Создан новый пользователь: {user.username}")
            else:
                # Обновляем данные существующего пользователя
                updated = False
                if user.username != telegram_user.username:
                    user.username = telegram_user.username or user.username
                    updated = True
                if user.first_name != telegram_user.first_name:
                    user.first_name = telegram_user.first_name or user.first_name
                    updated = True
                if user.last_name != telegram_user.last_name:
                    user.last_name = telegram_user.last_name or user.last_name
                    updated = True
                
                if updated:
                    user.save()
                    self.logger.info(f"Обновлен пользователь: {user.username}")
            
            return user
            
        except Exception as e:
            self.logger.error(f"Ошибка при работе с пользователем {telegram_user.id}: {e}")
            raise
    
    def get_user_stats(self, user: DjangoUser) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        try:
            from learning.models import UserProgress, UserRating
            
            total_tasks = UserProgress.objects.filter(user=user).count()
            correct_tasks = UserProgress.objects.filter(user=user, is_correct=True).count()
            
            rating = UserRating.objects.filter(user=user).first()
            user_rating = rating.rating if rating else 0
            
            accuracy = (correct_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                'total_tasks': total_tasks,
                'correct_tasks': correct_tasks,
                'accuracy': round(accuracy, 1),
                'rating': user_rating,
                'level': self._calculate_level(user_rating)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики для пользователя {user.id}: {e}")
            return {
                'total_tasks': 0,
                'correct_tasks': 0,
                'accuracy': 0.0,
                'rating': 0,
                'level': 1
            }
    
    def _calculate_level(self, rating: int) -> int:
        """Вычислить уровень пользователя на основе рейтинга"""
        if rating < 100:
            return 1
        elif rating < 300:
            return 2
        elif rating < 600:
            return 3
        elif rating < 1000:
            return 4
        else:
            return 5
    
    def update_user_progress(self, user: DjangoUser, task_id: int, 
                           is_correct: bool, user_answer: str) -> Dict[str, Any]:
        """Обновить прогресс пользователя"""
        try:
            from learning.models import Task, UserProgress, UserRating
            
            task = Task.objects.get(id=task_id)
            
            # Создаем или обновляем прогресс
            progress, created = UserProgress.objects.get_or_create(
                user=user,
                task=task,
                defaults={
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'attempts': 1
                }
            )
            
            if not created:
                progress.attempts += 1
                progress.user_answer = user_answer
                progress.is_correct = is_correct
                progress.save()
            
            # Обновляем рейтинг
            rating, created = UserRating.objects.get_or_create(
                user=user,
                defaults={'rating': 0}
            )
            
            if is_correct:
                rating.rating += 10
                rating.save()
            
            return {
                'success': True,
                'progress': {
                    'attempts': progress.attempts,
                    'is_correct': is_correct,
                    'rating_change': 10 if is_correct else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления прогресса для пользователя {user.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }