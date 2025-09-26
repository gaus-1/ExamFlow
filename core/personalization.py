"""
🎯 Система персонализации ExamFlow

Функции:
- Анализ поведения пользователей
- Персональные рекомендации
- Адаптивный контент
- Машинное обучение на JavaScript
"""

import json
import logging
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from learning.models import Subject, Task, UserProgress

logger = logging.getLogger(__name__)


class UserBehaviorAnalyzer:
    """Анализатор поведения пользователей"""

    def __init__(self, user):
        self.user = user
        self.profile = self._get_or_create_profile()

    def _get_or_create_profile(self):
        """Получает или создает профиль пользователя"""
        profile, created = UserProfile.objects.get_or_create(  # type: ignore
            user=self.user,
            defaults={
                "telegram_id": "",
                "current_task_id": None,
                "preferences": "{}",
                "learning_style": "visual",
                "difficulty_level": "medium",
            },
        )
        return profile

    def analyze_behavior(self):
        """Анализирует поведение пользователя"""
        try:
            # Анализируем историю посещений
            visit_patterns = self._analyze_visit_patterns()

            # Анализируем выбранные предметы
            subject_preferences = self._analyze_subject_preferences()

            # Анализируем типы заданий
            task_preferences = self._analyze_task_preferences()

            # Анализируем время на сайте
            time_patterns = self._analyze_time_patterns()

            # Формируем профиль пользователя
            user_profile = {
                "visit_patterns": visit_patterns,
                "subject_preferences": subject_preferences,
                "task_preferences": task_preferences,
                "time_patterns": time_patterns,
                "learning_style": self._determine_learning_style(),
                "difficulty_level": self._determine_difficulty_level(),
                "last_updated": timezone.now().isoformat(),
            }

            # Сохраняем профиль
            self.profile.preferences = json.dumps(user_profile, default=str)
            self.profile.save()

            logger.info("Профиль пользователя {self.user.username} обновлен")
            return user_profile

        except Exception:
            logger.error(
                "Ошибка анализа поведения пользователя {self.user.username}: {e}"
            )
            return {}

    def _analyze_visit_patterns(self):
        """Анализирует паттерны посещений"""
        # Здесь будет логика анализа посещений
        # Пока возвращаем базовые данные
        return {
            "total_visits": 10,
            "average_session_duration": 25,  # минуты
            "preferred_days": ["понедельник", "среда", "пятница"],
            "preferred_hours": [9, 14, 20],
        }

    def _analyze_subject_preferences(self):
        """Анализирует предпочтения по предметам"""
        try:
            # Получаем прогресс по предметам
            subject_progress = (
                UserProgress.objects.filter(user=self.user)  # type: ignore
                .select_related("task__subject")
                .values("task__subject__name")
                .annotate(
                    total_attempts=Count("id"),
                    correct_attempts=Count("id", filter=Q(is_correct=True)),
                    avg_difficulty=Avg("task__difficulty"),
                )
            )

            preferences = {}
            for progress in subject_progress:
                subject_name = progress["task__subject__name"]
                accuracy = (
                    progress["correct_attempts"] / progress["total_attempts"]
                ) * 100

                preferences[subject_name] = {
                    "total_attempts": progress["total_attempts"],
                    "correct_attempts": progress["correct_attempts"],
                    "accuracy": round(accuracy, 2),
                    "avg_difficulty": round(progress["avg_difficulty"], 1),
                    "preference_score": self._calculate_preference_score(progress),
                }

            # Сортируем по предпочтению
            sorted_preferences = sorted(
                preferences.items(),
                key=lambda x: x[1]["preference_score"],
                reverse=True,
            )

            return dict(sorted_preferences)

        except Exception:
            logger.error("Ошибка анализа предпочтений по предметам: {e}")
            return {}

    def _analyze_task_preferences(self):
        """Анализирует предпочтения по типам заданий"""
        try:
            # Анализируем предпочтения по сложности
            difficulty_preferences = (
                UserProgress.objects.filter(user=self.user)  # type: ignore
                .select_related("task")
                .values("task__difficulty")
                .annotate(
                    total_attempts=Count("id"),
                    success_rate=Count("id", filter=Q(is_correct=True))
                    * 100.0
                    / Count("id"),
                )
            )

            # Анализируем предпочтения по темам
            topic_preferences = (
                UserProgress.objects.filter(user=self.user)  # type: ignore
                .select_related("task__subject")
                .values("task__subject__name")
                .annotate(
                    total_attempts=Count("id"),
                    success_rate=Count("id", filter=Q(is_correct=True))
                    * 100.0
                    / Count("id"),
                )
            )

            return {
                "difficulty_preferences": list(difficulty_preferences),
                "topic_preferences": list(topic_preferences),
                "preferred_difficulty": self._get_preferred_difficulty(),
                "preferred_topics": self._get_preferred_topics(),
            }

        except Exception:
            logger.error("Ошибка анализа предпочтений по заданиям: {e}")
            return {}

    def _analyze_time_patterns(self):
        """Анализирует паттерны времени"""
        try:
            # Анализируем время последних попыток
            recent_attempts = UserProgress.objects.filter(  # type: ignore
                user=self.user, last_attempt__gte=timezone.now() - timedelta(days=30)
            ).order_by("last_attempt")

            time_patterns = {
                "morning_attempts": 0,  # 6-12
                "afternoon_attempts": 0,  # 12-18
                "evening_attempts": 0,  # 18-22
                "night_attempts": 0,  # 22-6
                "weekday_attempts": 0,
                "weekend_attempts": 0,
            }

            for attempt in recent_attempts:
                hour = attempt.last_attempt.hour
                weekday = attempt.last_attempt.weekday()

                # Определяем время суток
                if 6 <= hour < 12:
                    time_patterns["morning_attempts"] += 1
                elif 12 <= hour < 18:
                    time_patterns["afternoon_attempts"] += 1
                elif 18 <= hour < 22:
                    time_patterns["evening_attempts"] += 1
                else:
                    time_patterns["night_attempts"] += 1

                # Определяем день недели
                if weekday < 5:  # Понедельник - Пятница
                    time_patterns["weekday_attempts"] += 1
                else:
                    time_patterns["weekend_attempts"] += 1

            return time_patterns

        except Exception:
            logger.error("Ошибка анализа временных паттернов: {e}")
            return {}

    def _calculate_preference_score(self, progress):
        """Вычисляет оценку предпочтения предмета"""
        accuracy = progress["correct_attempts"] / progress["total_attempts"]
        attempts = progress["total_attempts"]

        # Формула: точность * 0.6 + количество попыток * 0.4
        score = (accuracy * 0.6) + (min(attempts / 10, 1.0) * 0.4)
        return round(score, 3)

    def _get_preferred_difficulty(self):
        """Определяет предпочитаемую сложность"""
        try:
            difficulty_stats = (
                UserProgress.objects.filter(user=self.user)  # type: ignore
                .select_related("task")
                .values("task__difficulty")
                .annotate(
                    success_rate=Count("id", filter=Q(is_correct=True))
                    * 100.0
                    / Count("id")
                )
                .order_by("-success_rate")
            )

            if difficulty_stats:
                return difficulty_stats[0]["task__difficulty"]
            return 2  # Средняя сложность по умолчанию

        except Exception:
            logger.error("Ошибка определения предпочитаемой сложности: {e}")
            return 2

    def _get_preferred_topics(self):
        """Определяет предпочитаемые темы"""
        try:
            topic_stats = (
                UserProgress.objects.filter(user=self.user)  # type: ignore
                .select_related("task__subject")
                .values("task__subject__name")
                .annotate(
                    total_attempts=Count("id"),
                    success_rate=Count("id", filter=Q(is_correct=True))
                    * 100.0
                    / Count("id"),
                )
                .order_by("-total_attempts")[:5]
            )

            return [topic["task__subject__name"] for topic in topic_stats]

        except Exception:
            logger.error("Ошибка определения предпочитаемых тем: {e}")
            return []

    def _determine_learning_style(self):
        """Определяет стиль обучения"""
        try:
            # Анализируем паттерны ответов
            quick_answers = UserProgress.objects.filter(  # type: ignore
                user=self.user, last_attempt__gte=timezone.now() - timedelta(days=7)
            ).count()

            if quick_answers > 20:
                return "fast_paced"
            elif quick_answers > 10:
                return "balanced"
            else:
                return "thorough"

        except Exception:
            logger.error("Ошибка определения стиля обучения: {e}")
            return "balanced"

    def _determine_difficulty_level(self):
        """Определяет уровень сложности"""
        try:
            recent_progress = UserProgress.objects.filter(  # type: ignore
                user=self.user, last_attempt__gte=timezone.now() - timedelta(days=14)
            )

            if not recent_progress.exists():
                return "medium"

            success_rate = (
                recent_progress.filter(is_correct=True).count()
                / recent_progress.count()
            )

            if success_rate > 0.8:
                return "advanced"
            elif success_rate > 0.6:
                return "medium"
            else:
                return "beginner"

        except Exception:
            logger.error("Ошибка определения уровня сложности: {e}")
            return "medium"


class PersonalizedRecommendations:
    """Система персональных рекомендаций"""

    def __init__(self, user):
        self.user = user
        self.analyzer = UserBehaviorAnalyzer(user)

    def get_recommendations(self, limit=10):
        """Получает персональные рекомендации"""
        try:
            # Анализируем поведение пользователя
            behavior_profile = self.analyzer.analyze_behavior()

            # Получаем рекомендации по предметам
            subject_recommendations = self._get_subject_recommendations(
                behavior_profile
            )

            # Получаем рекомендации по заданиям
            task_recommendations = self._get_task_recommendations(behavior_profile)

            # Получаем рекомендации по темам
            topic_recommendations = self._get_topic_recommendations(behavior_profile)

            return {
                "subject_recommendations": subject_recommendations,
                "task_recommendations": task_recommendations,
                "topic_recommendations": topic_recommendations,
                "learning_plan": self._generate_learning_plan(behavior_profile),
                "behavior_profile": behavior_profile,
            }

        except Exception:
            logger.error("Ошибка получения рекомендаций для {self.user.username}: {e}")
            return {}

    def _get_subject_recommendations(self, behavior_profile):
        """Получает рекомендации по предметам"""
        try:
            subject_prefs = behavior_profile.get("subject_preferences", {})

            if not subject_prefs:
                # Если нет данных, рекомендуем базовые предметы
                return []

            # Рекомендуем предметы с низкой точностью для улучшения
            improvement_recommendations = []
            for subject, stats in subject_prefs.items():
                if stats["accuracy"] < 70:
                    improvement_recommendations.append(
                        {
                            "subject": subject,
                            "reason": 'Точность {stats["accuracy"]}% - есть возможности для улучшения',
                            "current_accuracy": stats["accuracy"],
                            "priority": "high",
                        }
                    )

            # Рекомендуем новые предметы для изучения
            all_subjects = Subject.objects.all()  # type: ignore
            studied_subjects = set(subject_prefs.keys())
            new_subjects = []

            for subject in all_subjects:
                if subject.name not in studied_subjects:
                    new_subjects.append(
                        {
                            "subject": subject.name,
                            "reason": "Новый предмет для изучения",
                            "priority": "medium",
                        }
                    )

            return {
                "improvement": improvement_recommendations[:3],
                "new_subjects": new_subjects[:3],
                "current_progress": subject_prefs,
            }

        except Exception:
            logger.error("Ошибка получения рекомендаций по предметам: {e}")
            return {}

    def _get_task_recommendations(self, behavior_profile):
        """Получает рекомендации по заданиям"""
        try:
            task_prefs = behavior_profile.get("task_preferences", {})
            preferred_difficulty = task_prefs.get("preferred_difficulty", 2)

            # Получаем задания подходящей сложности
            recommended_tasks = Task.objects.filter(  # type: ignore
                difficulty__lte=preferred_difficulty + 1,
                difficulty__gte=max(1, preferred_difficulty - 1),
            ).exclude(userprogress__user=self.user)[:10]

            recommendations = []
            for task in recommended_tasks:
                recommendations.append(
                    {
                        "id": task.id,
                        "title": task.title,
                        "subject": task.subject.name,
                        "difficulty": task.difficulty,
                        "reason": "Сложность {task.difficulty}/5 подходит вашему уровню",
                    }
                )

            return recommendations

        except Exception:
            logger.error("Ошибка получения рекомендаций по заданиям: {e}")
            return []

    def _get_topic_recommendations(self, behavior_profile):
        """Получает рекомендации по темам"""
        try:
            topic_prefs = behavior_profile.get("task_preferences", {})
            preferred_topics = topic_prefs.get("preferred_topics", [])

            if not preferred_topics:
                # Рекомендуем базовые темы
                return []

            # Рекомендуем темы для углубления
            recommendations = []
            for topic_name in preferred_topics[:3]:
                recommendations.append(
                    {
                        "topic": topic_name,
                        "reason": "Углубление знаний по интересующей теме",
                        "priority": "high",
                    }
                )

            return recommendations

        except Exception:
            logger.error("Ошибка получения рекомендаций по темам: {e}")
            return []

    def _generate_learning_plan(self, behavior_profile):
        """Генерирует персональный план обучения"""
        try:
            learning_style = behavior_profile.get("learning_style", "balanced")
            difficulty_level = behavior_profile.get("difficulty_level", "medium")

            # Адаптируем план под стиль обучения
            if learning_style == "fast_paced":
                daily_goal = 5
                weekly_goal = 25
                focus = "Количество и разнообразие заданий"
            elif learning_style == "thorough":
                daily_goal = 2
                weekly_goal = 10
                focus = "Качество и понимание материала"
            else:  # balanced
                daily_goal = 3
                weekly_goal = 15
                focus = "Баланс количества и качества"

            # Адаптируем под уровень сложности
            if difficulty_level == "beginner":
                difficulty_focus = "Базовые задания для закрепления основ"
            elif difficulty_level == "advanced":
                difficulty_focus = "Сложные задания для углубления знаний"
            else:
                difficulty_focus = "Разнообразные задания для развития навыков"

            return {
                "daily_goal": daily_goal,
                "weekly_goal": weekly_goal,
                "focus": focus,
                "difficulty_focus": difficulty_focus,
                "recommended_session_duration": 45,  # минуты
                "break_frequency": "Каждые 45 минут - перерыв 10 минут",
            }

        except Exception:
            logger.error("Ошибка генерации плана обучения: {e}")
            return {}


def get_user_recommendations(user):
    """Получает рекомендации для пользователя"""
    try:
        recommender = PersonalizedRecommendations(user)
        return recommender.get_recommendations()
    except Exception:
        logger.error("Ошибка получения рекомендаций: {e}")
        return {}


def analyze_user_behavior(user):
    """Анализирует поведение пользователя"""
    try:
        analyzer = UserBehaviorAnalyzer(user)
        return analyzer.analyze_behavior()
    except Exception:
        logger.error("Ошибка анализа поведения: {e}")
        return {}
