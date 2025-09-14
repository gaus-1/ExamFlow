"""
Система персонализации для ExamFlow
Анализирует поведение пользователей и предоставляет персонализированные рекомендации
"""

import logging
from typing import List, Dict, Tuple
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from learning.models import Task, UserProgress
from core.models import UnifiedProfile

logger = logging.getLogger(__name__)

class UserBehaviorAnalyzer:
    """Анализатор поведения пользователей"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = UnifiedProfile.objects.get( # type: ignore
            telegram_id=user_id) if UnifiedProfile.objects.filter( # type: ignore
            telegram_id=user_id).exists() else None  # type: ignore

    def get_user_preferences(self) -> Dict:
        """Получает предпочтения пользователя на основе его активности"""
        try:
            # Анализируем последние 30 дней
            thirty_days_ago = timezone.now() - timedelta(days=30)

            # Получаем прогресс пользователя (core модель)
            user_progress = UserProgress.objects.filter(  # type: ignore
                user_id=self.user_id,
                last_attempt__gte=thirty_days_ago
            ).select_related('task__subject')

            preferences = {
                'favorite_subjects': [],
                'difficulty_preference': 3,  # По умолчанию средняя сложность
                'study_time_preference': 'evening',  # По умолчанию вечер
                'learning_style': 'mixed'  # По умолчанию смешанный
            }

            if user_progress.exists():
                # Анализируем любимые предметы
                subject_stats = {}
                for progress in user_progress:
                    subject_name = progress.task.subject.name
                    if subject_name not in subject_stats:
                        subject_stats[subject_name] = {
                            'attempts': 0,
                            'correct_answers': 0,
                            'total_time': 0
                        }

                    subject_stats[subject_name]['attempts'] += progress.attempts
                    if progress.is_correct:
                        subject_stats[subject_name]['correct_answers'] += 1

                # Сортируем предметы по активности
                sorted_subjects = sorted(
                    subject_stats.items(),
                    key=lambda x: x[1]['attempts'],
                    reverse=True
                )

                preferences['favorite_subjects'] = [subject[0]
                                                    for subject in sorted_subjects[:3]]

                # Анализируем предпочтения по сложности
                difficulty_stats = user_progress.values('task__difficulty').annotate(
                    count=Count('id')
                ).order_by('task__difficulty')

                if difficulty_stats:
                    total_attempts = sum(stat['count'] for stat in difficulty_stats)
                    weighted_difficulty = sum(
                        stat['task__difficulty'] * stat['count']
                        for stat in difficulty_stats
                    )
                    preferences['difficulty_preference'] = round(
                        weighted_difficulty / total_attempts, 1)

            return preferences

        except Exception as e:
            logger.error(
                "Ошибка при анализе предпочтений пользователя {self.user_id}: {e}")
            return {
                'favorite_subjects': [],
                'difficulty_preference': 3,
                'study_time_preference': 'evening',
                'learning_style': 'mixed'
            }

    def get_study_patterns(self) -> Dict:
        """Анализирует паттерны обучения пользователя"""
        try:
            # Анализируем последние 60 дней
            sixty_days_ago = timezone.now() - timedelta(days=60)

            user_progress = UserProgress.objects.filter(  # type: ignore
                user_id=self.user_id,
                last_attempt__gte=sixty_days_ago
            )

            patterns = {
                'study_frequency': 'regular',  # regular, irregular, intensive
                'preferred_days': [],
                'preferred_hours': [],
                'session_duration': 'medium'  # short, medium, long
            }

            if user_progress.exists():
                # Анализируем частоту занятий
                daily_activity = {}
                for progress in user_progress:
                    date = progress.last_attempt.date()
                    if date not in daily_activity:
                        daily_activity[date] = 0
                    daily_activity[date] += 1

                avg_daily_tasks = sum(daily_activity.values()) / len(daily_activity)

                if avg_daily_tasks >= 5:
                    patterns['study_frequency'] = 'intensive'
                elif avg_daily_tasks >= 2:
                    patterns['study_frequency'] = 'regular'
                else:
                    patterns['study_frequency'] = 'irregular'

                # Анализируем предпочитаемые дни недели
                weekday_activity = {}
                for progress in user_progress:
                    weekday = progress.last_attempt.strftime('%A')
                    if weekday not in weekday_activity:
                        weekday_activity[weekday] = 0
                    weekday_activity[weekday] += 1

                # Сортируем дни по активности
                sorted_weekdays = sorted(
                    weekday_activity.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                patterns['preferred_days'] = [day[0] for day in sorted_weekdays[:3]]

                # Анализируем предпочитаемые часы
                hour_activity = {}
                for progress in user_progress:
                    hour = progress.last_attempt.hour
                    if hour not in hour_activity:
                        hour_activity[hour] = 0
                    hour_activity[hour] += 1

                # Сортируем часы по активности
                sorted_hours = sorted(
                    hour_activity.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                patterns['preferred_hours'] = [hour[0] for hour in sorted_hours[:3]]

            return patterns

        except Exception as e:
            logger.error(
                "Ошибка при анализе паттернов обучения пользователя {self.user_id}: {e}")
            return {
                'study_frequency': 'regular',
                'preferred_days': [],
                'preferred_hours': [],
                'session_duration': 'medium'
            }

class PersonalizedRecommendations:
    """Система персонализированных рекомендаций"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.analyzer = UserBehaviorAnalyzer(user_id)

    def get_recommended_tasks(self, limit: int = 10) -> List[Task]:
        """Получает персонализированные рекомендации по заданиям"""
        try:
            preferences = self.analyzer.get_user_preferences()

            # Базовый запрос для заданий
            recommended_tasks = Task.objects.all()  # type: ignore

            # Фильтруем по любимым предметам
            if preferences['favorite_subjects']:
                recommended_tasks = recommended_tasks.filter(
                    subject__name__in=preferences['favorite_subjects']
                )

            # Фильтруем по предпочтительной сложности
            difficulty_range = self._get_difficulty_range(
                preferences['difficulty_preference'])
            recommended_tasks = recommended_tasks.filter(
                difficulty__range=difficulty_range
            )

            # Исключаем уже решенные задания
            solved_tasks = UserProgress.objects.filter(  # type: ignore
                user_id=self.user_id,
                is_correct=True
            ).values_list('task_id', flat=True)

            if solved_tasks.exists():
                recommended_tasks = recommended_tasks.exclude(id__in=solved_tasks)

            # Сортируем по релевантности
            recommended_tasks = recommended_tasks.annotate(
                popularity=Count('userprogress')
            ).order_by('-popularity', 'difficulty')[:limit]

            return list(recommended_tasks)

        except Exception as e:
            logger.error(
                "Ошибка при получении рекомендаций для пользователя {self.user_id}: {e}")
            return []

    def get_study_plan(self) -> Dict:
        """Создает персонализированный план обучения"""
        try:
            preferences = self.analyzer.get_user_preferences()
            patterns = self.analyzer.get_study_patterns()

            plan = {
                'daily_goals': [],
                'weekly_focus': [],
                'difficulty_progression': [],
                'time_recommendations': []
            }

            # Определяем ежедневные цели
            if patterns['study_frequency'] == 'intensive':
                plan['daily_goals'] = [
                ]
            elif patterns['study_frequency'] == 'regular':
                plan['daily_goals'] = [
                ]
            else:
                plan['daily_goals'] = [
                ]

            # Определяем еженедельный фокус
            if preferences['favorite_subjects']:
                plan['weekly_focus'] = [
                    f"Фокус на предмете: {subject}"
                    for subject in preferences['favorite_subjects'][:2]  # type: ignore
                ]

            # План прогрессии по сложности
            current_difficulty = preferences['difficulty_preference']
            plan['difficulty_progression'] = [
            ]

            # Рекомендации по времени
            if patterns['preferred_hours']:
                plan['time_recommendations'] = [
                    "Лучшее время для занятий: {hour}:00"
                    for hour in patterns['preferred_hours']
                ]

            return plan

        except Exception as e:
            logger.error(
                "Ошибка при создании плана обучения для пользователя {self.user_id}: {e}")
            return {
                'daily_goals': [],
                'weekly_focus': [],
                'difficulty_progression': [],
                'time_recommendations': []
            }

    def _get_difficulty_range(self, preferred_difficulty: float) -> Tuple[int, int]:
        """Получает диапазон сложности на основе предпочтений"""
        if preferred_difficulty <= 2:
            return (1, 3)
        elif preferred_difficulty <= 3:
            return (2, 4)
        elif preferred_difficulty <= 4:
            return (3, 5)
        else:
            return (4, 5)

    def get_weak_topics(self) -> List[Dict]:
        """Определяет слабые темы пользователя"""
        try:
            # Получаем задания, которые пользователь не смог решить
            weak_progress = UserProgress.objects.filter(  # type: ignore
                user_id=self.user_id,
                is_correct=False,
                attempts__gte=2  # Пытался решить минимум 2 раза
            ).select_related('task__subject')

            weak_topics = {}

            for progress in weak_progress:
                subject_name = progress.task.subject.name
                if subject_name not in weak_topics:
                    weak_topics[subject_name] = {
                        'failed_tasks': 0,
                        'total_attempts': 0,
                        'difficulty_level': 0
                    }

                weak_topics[subject_name]['failed_tasks'] += 1
                weak_topics[subject_name]['total_attempts'] += progress.attempts
                weak_topics[subject_name]['difficulty_level'] += progress.task.difficulty

            # Вычисляем средние значения
            for subject_data in weak_topics.values():
                if subject_data['failed_tasks'] > 0:
                    subject_data['avg_difficulty'] = round(
                        subject_data['difficulty_level'] / subject_data['failed_tasks'],
                        1
                    )
                    subject_data['success_rate'] = 0  # Все задания провалены

            # Сортируем по количеству проваленных заданий
            sorted_weak_topics = sorted(
                weak_topics.items(),
                key=lambda x: x[1]['failed_tasks'],
                reverse=True
            )

            return [
                {
                    'subject': subject, # type: ignore
                    'failed_tasks': data['failed_tasks'],
                    'total_attempts': data['total_attempts'],
                    'avg_difficulty': data.get('avg_difficulty', 0), # type: ignore
                    'success_rate': data.get('success_rate', 0)  # type: ignore
                }
                for subject, data in sorted_weak_topics[:5]  # Топ-5 слабых тем
            ]

        except Exception as e:
            logger.error(
                "Ошибка при определении слабых тем пользователя {self.user_id}: {e}")
            return []

def get_user_insights(user_id: int) -> Dict:
    """Получает комплексные инсайты о пользователе"""
    try:
        analyzer = UserBehaviorAnalyzer(user_id)
        recommender = PersonalizedRecommendations(user_id)

        insights = {
            'preferences': analyzer.get_user_preferences(),
            'patterns': analyzer.get_study_patterns(),
            'recommendations': {
                'tasks': recommender.get_recommended_tasks(5),
                'study_plan': recommender.get_study_plan(),
                'weak_topics': recommender.get_weak_topics()
            },
            'progress_summary': _get_progress_summary(user_id)
        }

        return insights

    except Exception as e:
        logger.error("Ошибка при получении инсайтов для пользователя {user_id}: {e}")
        return {}

def _get_progress_summary(user_id: int) -> Dict:
    """Получает сводку прогресса пользователя"""
    try:
        total_tasks = Task.objects.count()  # type: ignore
        solved_tasks = UserProgress.objects.filter(  # type: ignore
            user_id=user_id,
            is_correct=True
        ).count()

        total_attempts = UserProgress.objects.filter(  # type: ignore
            user_id=user_id
        ).aggregate(total=Count('attempts'))['total'] or 0

        success_rate = (solved_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            'total_tasks': total_tasks,
            'solved_tasks': solved_tasks,
            'total_attempts': total_attempts,
            'success_rate': round(
                success_rate,
                1),
            'completion_percentage': round(
                solved_tasks /
                total_tasks *
                100,
                1) if total_tasks > 0 else 0}

    except Exception as e:
        logger.error(
            "Ошибка при получении сводки прогресса для пользователя {user_id}: {e}")
        return {
            'total_tasks': 0,
            'solved_tasks': 0,
            'total_attempts': 0,
            'success_rate': 0,
            'completion_percentage': 0
        }
