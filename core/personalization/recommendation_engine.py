"""
Система персонализации и рекомендаций для ExamFlow 2.0
"""

import logging
from typing import Dict, List
from django.db import models
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Движок персонализации и рекомендаций
    """

    def __init__(self):
        self.learning_style_weights = {
            'visual': 0.3,
            'auditory': 0.2,
            'kinesthetic': 0.2,
            'reading': 0.3
        }

    def get_personalized_recommendations(self, user_id: int, limit: int = 5) -> Dict:
        """
        Получает персонализированные рекомендации для пользователя
        """
        try:
            from core.models import UnifiedProfile, UserProgress, Task, Subject  # type: ignore

            # Получаем профиль пользователя
            user_profile = UnifiedProfile.objects.filter(  # type: ignore
                models.Q(user_id=user_id) | models.Q(telegram_id=user_id)
            ).first()

            if not user_profile:
                return self.get_default_recommendations()

            # Анализируем прогресс пользователя
            user_analysis = self.analyze_user_progress(user_id)

            # Генерируем рекомендации
            recommendations = {
                'topics_to_focus': self.get_topics_to_focus(user_analysis),
                'practice_tasks': self.get_practice_tasks(
                    user_id,
                    user_analysis,
                    limit),
                'learning_path': self.get_learning_path(user_analysis),
                'weak_areas': self.get_weak_areas(user_analysis),
                'strengths': self.get_strengths(user_analysis),
                'next_goals': self.get_next_goals(user_analysis)}

            return recommendations

        except Exception as e:
            logger.error(f"Ошибка при получении рекомендаций: {e}")
            return self.get_default_recommendations()

    def analyze_user_progress(self, user_id: int) -> Dict:
        """
        Анализирует прогресс пользователя
        """
        try:
            from core.models import UserProgress, Task  # type: ignore

            # Получаем прогресс по предметам
            progress_entries = UserProgress.objects.filter(
                user_id=user_id)  # type: ignore

            analysis = {
                'total_problems_solved': 0,
                'average_accuracy': 0.0,
                'subject_performance': {},
                'recent_activity': {},
                'learning_velocity': 0.0,
                'weak_subjects': [],
                'strong_subjects': []
            }

            total_accuracy = 0
            subject_count = 0

            for progress in progress_entries:
                subject_name = progress.subject.name
                accuracy = progress.accuracy or 0

                analysis['subject_performance'][subject_name] = {
                    'problems_solved': progress.problems_solved,
                    'accuracy': accuracy,
                    'last_activity': progress.last_activity
                }

                analysis['total_problems_solved'] += progress.problems_solved
                total_accuracy += accuracy
                subject_count += 1

                # Определяем слабые и сильные предметы
                if accuracy < 60:
                    analysis['weak_subjects'].append(subject_name)
                elif accuracy > 80:
                    analysis['strong_subjects'].append(subject_name)

            if subject_count > 0:
                analysis['average_accuracy'] = total_accuracy / subject_count

            # Анализируем скорость обучения
            analysis['learning_velocity'] = self.calculate_learning_velocity(user_id)

            return analysis

        except Exception as e:
            logger.error(f"Ошибка при анализе прогресса: {e}")
            return {}

    def get_topics_to_focus(self, user_analysis: Dict) -> List[Dict]:
        """
        Определяет темы, на которых нужно сосредоточиться
        """
        focus_topics = []

        # Сортируем предметы по точности (от худших к лучшим)
        subject_performance = user_analysis.get('subject_performance', {})
        sorted_subjects = sorted(
            subject_performance.items(),
            key=lambda x: x[1]['accuracy']
        )

        for subject_name, performance in sorted_subjects[:3]:  # Топ-3 худших
            if performance['accuracy'] < 70:
                focus_topics.append({
                    'subject': subject_name,
                    'priority': 'high',
                    'reason': f'Точность: {performance["accuracy"]:.1f}%',
                    'recommended_actions': [
                        'Решайте больше задач по этой теме',
                        'Изучите теорию заново',
                        'Обратитесь к учителю за помощью'
                    ]
                })

        return focus_topics

    def get_practice_tasks(
            self,
            user_id: int,
            user_analysis: Dict,
            limit: int) -> List[Dict]:
        """
        Получает задачи для практики
        """
        try:
            from core.models import Task, Subject  # type: ignore

            # Определяем предметы для практики
            weak_subjects = user_analysis.get('weak_subjects', [])
            if not weak_subjects:
                # Если нет слабых предметов, берем случайные
                subjects = Subject.objects.all()[:2]  # type: ignore
                weak_subjects = [s.name for s in subjects]

            tasks = []
            for subject_name in weak_subjects[:2]:  # Максимум 2 предмета
                subject_tasks = Task.objects.filter(  # type: ignore
                    subject__name__icontains=subject_name,
                    difficulty__lte=3  # Начинаем с простых задач
                ).order_by('?')[:limit // 2]

                for task in subject_tasks:
                    tasks.append({
                        'id': task.id,
                        'title': task.title,
                        'text': task.text[:200] + '...' if len(task.text) > 200 else task.text,
                        'subject': subject_name,
                        'difficulty': task.difficulty,
                        'priority': 'high' if subject_name in weak_subjects else 'medium'
                    })

            return tasks[:limit]

        except Exception as e:
            logger.error(f"Ошибка при получении задач: {e}")
            return []

    def get_learning_path(self, user_analysis: Dict) -> List[Dict]:
        """
        Создает персональный путь обучения
        """
        learning_path = []

        # Базовый путь для новичков
        if user_analysis.get('total_problems_solved', 0) < 10:
            learning_path = [
                {
                    'step': 1,
                    'title': 'Изучение основ',
                    'description': 'Начните с базовых понятий и теории',
                    'estimated_time': '1-2 недели',
                    'priority': 'high'
                },
                {
                    'step': 2,
                    'title': 'Практические задания',
                    'description': 'Решайте простые задачи для закрепления',
                    'estimated_time': '2-3 недели',
                    'priority': 'high'
                },
                {
                    'step': 3,
                    'title': 'Сложные задачи',
                    'description': 'Переходите к более сложным заданиям',
                    'estimated_time': '3-4 недели',
                    'priority': 'medium'
                }
            ]
        else:
            # Персонализированный путь для опытных пользователей
            weak_subjects = user_analysis.get('weak_subjects', [])

            for i, subject in enumerate(weak_subjects[:3], 1):
                learning_path.append({
                    'step': i,
                    'title': f'Улучшение по {subject}',
                    'description': f'Сосредоточьтесь на улучшении результатов по {subject}',
                    'estimated_time': '2-3 недели',
                    'priority': 'high'
                })

        return learning_path

    def get_weak_areas(self, user_analysis: Dict) -> List[Dict]:
        """
        Определяет слабые области
        """
        weak_areas = []
        subject_performance = user_analysis.get('subject_performance', {})

        for subject, performance in subject_performance.items():
            if performance['accuracy'] < 60:
                weak_areas.append({
                    'subject': subject,
                    'accuracy': performance['accuracy'],
                    'problems_solved': performance['problems_solved'],
                    'improvement_suggestions': [
                        'Изучите теорию заново',
                        'Решайте больше задач',
                        'Обратитесь за помощью к учителю'
                    ]
                })

        return weak_areas

    def get_strengths(self, user_analysis: Dict) -> List[Dict]:
        """
        Определяет сильные стороны
        """
        strengths = []
        subject_performance = user_analysis.get('subject_performance', {})

        for subject, performance in subject_performance.items():
            if performance['accuracy'] > 80:
                strengths.append({
                    'subject': subject,
                    'accuracy': performance['accuracy'],
                    'problems_solved': performance['problems_solved'],
                    'encouragement': f'Отличные результаты по {subject}!'
                })

        return strengths

    def get_next_goals(self, user_analysis: Dict) -> List[Dict]:
        """
        Определяет следующие цели
        """
        goals = []

        # Цель по точности
        current_accuracy = user_analysis.get('average_accuracy', 0)
        if current_accuracy < 70:
            goals.append({
                'type': 'accuracy',
                'title': 'Повысить точность',
                'description': f'Увеличить среднюю точность с {current_accuracy:.1f}% до 75%',
                'target_value': 75,
                'current_value': current_accuracy,
                'deadline': '2 недели'
            })

        # Цель по количеству решенных задач
        total_solved = user_analysis.get('total_problems_solved', 0)
        if total_solved < 50:
            goals.append({
                'type': 'quantity',
                'title': 'Решить больше задач',
                'description': f'Решить {50 - total_solved} задач до 50',
                'target_value': 50,
                'current_value': total_solved,
                'deadline': '1 месяц'
            })

        return goals

    def calculate_learning_velocity(self, user_id: int) -> float:
        """
        Вычисляет скорость обучения пользователя
        """
        try:
            from core.models import UserProgress  # type: ignore

            # Получаем прогресс за последние 30 дней
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_progress = UserProgress.objects.filter(  # type: ignore
                user_id=user_id,
                last_activity__gte=thirty_days_ago
            )

            total_problems = sum(p.problems_solved for p in recent_progress)
            return total_problems / 30  # Задач в день

        except Exception as e:
            logger.error(f"Ошибка при вычислении скорости обучения: {e}")
            return 0.0

    def get_default_recommendations(self) -> Dict:
        """
        Возвращает рекомендации по умолчанию
        """
        return {
            'topics_to_focus': [
                {
                    'subject': 'Математика',
                    'priority': 'high',
                    'reason': 'Базовый предмет для ЕГЭ',
                    'recommended_actions': [
                        'Начните с алгебры',
                        'Изучите геометрию',
                        'Практикуйтесь в решении задач'
                    ]
                }
            ],
            'practice_tasks': [],
            'learning_path': [
                {
                    'step': 1,
                    'title': 'Начало обучения',
                    'description': 'Изучите основы выбранного предмета',
                    'estimated_time': '1-2 недели',
                    'priority': 'high'
                }
            ],
            'weak_areas': [],
            'strengths': [],
            'next_goals': [
                {
                    'type': 'general',
                    'title': 'Начать обучение',
                    'description': 'Выберите предмет и начните решать задачи',
                    'target_value': 1,
                    'current_value': 0,
                    'deadline': 'Сегодня'
                }
            ]
        }
