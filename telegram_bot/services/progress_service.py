"""
Сервис для отслеживания прогресса пользователей
Применяет принцип Single Responsibility Principle (SRP)
"""

import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from telegram_auth.models import TelegramUser
from learning.models import Task, UserProgress, UserRating, Subject

logger = logging.getLogger(__name__)


class ProgressService:
    """Сервис для отслеживания прогресса обучения"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_user_progress_summary(self, user: TelegramUser) -> Dict[str, Any]:
        """Получить сводку прогресса пользователя"""
        try:
            # Общая статистика
            total_tasks = UserProgress.objects.filter(user=user).count()
            correct_tasks = UserProgress.objects.filter(user=user, is_correct=True).count()
            
            # Рейтинг
            rating_obj = UserRating.objects.filter(user=user).first()
            rating = rating_obj.rating if rating_obj else 0
            
            # Прогресс по предметам
            subjects_progress = self._get_subjects_progress(user)
            
            # Последние достижения
            recent_progress = self._get_recent_progress(user, limit=5)
            
            return {
                'total_tasks': total_tasks,
                'correct_tasks': correct_tasks,
                'accuracy': round((correct_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
                'rating': rating,
                'level': self._calculate_level(rating),
                'subjects_progress': subjects_progress,
                'recent_progress': recent_progress
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения прогресса для пользователя {user.id}: {e}")
            return {
                'total_tasks': 0,
                'correct_tasks': 0,
                'accuracy': 0.0,
                'rating': 0,
                'level': 1,
                'subjects_progress': [],
                'recent_progress': []
            }
    
    def _get_subjects_progress(self, user: TelegramUser) -> List[Dict[str, Any]]:
        """Получить прогресс по предметам"""
        try:
            subjects_data = []
            
            for subject in Subject.objects.all():
                tasks_count = Task.objects.filter(subject=subject).count()
                user_tasks = UserProgress.objects.filter(user=user, task__subject=subject)
                
                completed = user_tasks.count()
                correct = user_tasks.filter(is_correct=True).count()
                
                accuracy = round((correct / completed * 100) if completed > 0 else 0, 1)
                
                subjects_data.append({
                    'subject': subject.name,
                    'total_tasks': tasks_count,
                    'completed': completed,
                    'correct': correct,
                    'accuracy': accuracy,
                    'progress_percent': round((completed / tasks_count * 100) if tasks_count > 0 else 0, 1)
                })
            
            return subjects_data
            
        except Exception as e:
            self.logger.error(f"Ошибка получения прогресса по предметам: {e}")
            return []
    
    def _get_recent_progress(self, user: TelegramUser, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить последние достижения"""
        try:
            recent_progress = []
            
            progress_items = UserProgress.objects.filter(user=user).select_related('task', 'task__subject').order_by('-id')[:limit]
            
            for progress in progress_items:
                recent_progress.append({
                    'task_title': progress.task.title,
                    'subject': progress.task.subject.name,
                    'is_correct': progress.is_correct,
                    'attempts': progress.attempts,
                    'date': progress.task.created_at.strftime('%d.%m.%Y')
                })
            
            return recent_progress
            
        except Exception as e:
            self.logger.error(f"Ошибка получения последних достижений: {e}")
            return []
    
    def _calculate_level(self, rating: int) -> int:
        """Вычислить уровень пользователя"""
        if rating < 100:
            return 1
        elif rating < 300:
            return 2
        elif rating < 600:
            return 3
        elif rating < 1000:
            return 4
        elif rating < 1500:
            return 5
        else:
            return 6
    
    def get_recommended_tasks(self, user: TelegramUser, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить рекомендованные задачи для пользователя"""
        try:
            # Получаем задачи, которые пользователь еще не решал
            solved_tasks = UserProgress.objects.filter(user=user).values_list('task_id', flat=True)
            
            # Получаем задачи средней сложности
            recommended_tasks = Task.objects.exclude(id__in=solved_tasks).filter(
                difficulty__in=[2, 3, 4]
            ).select_related('subject').order_by('?')[:limit]
            
            tasks_data = []
            for task in recommended_tasks:
                tasks_data.append({
                    'id': task.id,
                    'title': task.title,
                    'subject': task.subject.name,
                    'difficulty': task.difficulty,
                    'difficulty_stars': '⭐' * task.difficulty
                })
            
            return tasks_data
            
        except Exception as e:
            self.logger.error(f"Ошибка получения рекомендованных задач: {e}")
            return []
    
    def get_weak_topics(self, user: TelegramUser) -> List[Dict[str, Any]]:
        """Получить слабые темы пользователя"""
        try:
            # Анализируем ошибки пользователя
            incorrect_tasks = UserProgress.objects.filter(user=user, is_correct=False)
            
            # Группируем по предметам
            subject_errors = {}
            for progress in incorrect_tasks:
                subject_name = progress.task.subject.name
                if subject_name not in subject_errors:
                    subject_errors[subject_name] = 0
                subject_errors[subject_name] += 1
            
            # Сортируем по количеству ошибок
            weak_topics = []
            for subject_name, error_count in sorted(subject_errors.items(), key=lambda x: x[1], reverse=True):
                weak_topics.append({
                    'subject': subject_name,
                    'error_count': error_count,
                    'recommendation': self._get_recommendation_for_subject(subject_name)
                })
            
            return weak_topics[:5]  # Топ-5 слабых тем
            
        except Exception as e:
            self.logger.error(f"Ошибка получения слабых тем: {e}")
            return []
    
    def _get_recommendation_for_subject(self, subject_name: str) -> str:
        """Получить рекомендацию для предмета"""
        recommendations = {
            'Математика': 'Рекомендуем больше практиковаться в решении уравнений и задач',
            'Русский язык': 'Сосредоточьтесь на орфографии и пунктуации',
            'Физика': 'Изучайте формулы и законы, практикуйте решение задач',
            'Химия': 'Повторите основные химические реакции и формулы',
            'Биология': 'Изучайте анатомию и физиологию живых организмов',
            'История': 'Повторите основные даты и события',
            'Обществознание': 'Изучайте основы права и экономики'
        }
        
        return recommendations.get(subject_name, 'Рекомендуем больше практиковаться по этому предмету')
