"""
Система геймификации для Telegram бота

Включает:
- Систему очков и уровней
- Достижения и значки
- Ежедневные задания
- Таблицу лидеров
- Прогресс-бары
"""

import logging

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from core.models import UnifiedProfile
from learning.models import Achievement, UserProgress

User = get_user_model()  # Определяем User модель

logger = logging.getLogger(__name__)

# УСТАРЕЛО: Этот класс разделен на модули в telegram_bot/gamification/
# Используйте: from telegram_bot.gamification import TelegramGamification


class TelegramGamification:
    """УСТАРЕВШИЙ класс - используйте новую модульную структуру"""

    def __init__(self):
        self.points_per_correct = 10  # Очки за правильный ответ
        self.points_per_streak = 5  # Бонус за серию правильных ответов
        self.level_multiplier = 100  # Множитель для уровня
        self.daily_bonus = 50  # Ежедневный бонус

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

            if new_level > old_level:
                profile.level = new_level
                level_up_message = (
                    f"🎉 **Поздравляем! Вы достигли {new_level} уровня!**"
                )
            else:
                level_up_message = ""

            profile.save()

            return {
                "success": True,
                "new_points": profile.points,
                "new_level": profile.level,
                "level_up": new_level > old_level,
                "level_up_message": level_up_message,
                "reason": reason,
            }

        except Exception as e:
            logger.error(f"Ошибка при добавлении очков: {e}")
            return {"success": False, "error": str(e)}

    @sync_to_async
    def get_user_stats(self, user_id: int) -> dict:
        """Получает статистику пользователя"""
        try:
            profile = UnifiedProfile.objects.filter(  # type: ignore
                telegram_id=user_id
            ).first()  # type: ignore
            if not profile:
                return {"success": False, "error": "Профиль не найден"}

            # Получаем или создаем Django User
            django_user, _ = User.objects.get_or_create(  # type: ignore
                username=f"tg_{user_id}", defaults={"first_name": f"User {user_id}"}
            )

            # Получаем прогресс по предметам
            subjects_progress = UserProgress.objects.filter(  # type: ignore
                user_id=django_user.id
            ).select_related("subject")

            # Получаем достижения
            achievements = Achievement.objects.filter(  # type: ignore
                user_id=django_user.id
            ).order_by("-date_earned")[:5]

            return {
                "success": True,
                "level": profile.level or 1,
                "points": profile.points or 0,
                "total_points": profile.total_points or 0,
                "subjects_progress": list(subjects_progress.values()),
                "achievements": list(achievements.values()),
                "rank": self._calculate_rank(profile.points or 0),
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {"success": False, "error": str(e)}

    @sync_to_async
    def check_achievements(self, user_id: int, action: str, **kwargs) -> list[dict]:
        """Проверяет и выдаёт достижения"""
        try:
            profile = UnifiedProfile.objects.filter(  # type: ignore
                telegram_id=user_id
            ).first()  # type: ignore
            if not profile:
                return []

            new_achievements = []

            # Получаем или создаем Django User
            django_user, _ = User.objects.get_or_create(  # type: ignore
                username=f"tg_{user_id}", defaults={"first_name": f"User {user_id}"}
            )

            # Достижение за первый правильный ответ
            if action == "correct_answer" and kwargs.get("first_correct"):
                achievement = self._create_achievement(
                    django_user, "Первый шаг", "Решили первое задание правильно", "🥇"
                )
                if achievement:
                    new_achievements.append(achievement)

            # Достижение за серию правильных ответов
            if action == "correct_answer" and kwargs.get("streak", 0) >= 5:
                achievement = self._create_achievement(
                    django_user,
                    "Серия побед",
                    f"Решили {kwargs['streak']} заданий подряд правильно",
                    "🔥",
                )
                if achievement:
                    new_achievements.append(achievement)

            # Достижение за уровень
            if action == "level_up":
                level = kwargs.get("level", 1)
                achievement = self._create_achievement(
                    django_user, f"Уровень {level}", f"Достигли {level} уровня", "⭐"
                )
                if achievement:
                    new_achievements.append(achievement)

            return new_achievements

        except Exception as e:
            logger.error(f"Ошибка при проверке достижений: {e}")
            return []

    @sync_to_async
    def get_daily_challenges(self, user_id: int) -> list[dict]:
        """Получает ежедневные задания для пользователя"""
        try:
            profile = UnifiedProfile.objects.filter(  # type: ignore
                telegram_id=user_id
            ).first()  # type: ignore
            if not profile:
                return []

            # Генерируем задания на основе уровня пользователя
            level = profile.level or 1
            challenges = []

            # Задание на количество решённых задач
            target_tasks = min(level * 2, 20)
            challenges.append(
                {
                    "id": "daily_tasks",
                    "title": f"Решить {target_tasks} заданий",
                    "description": f"Решите {target_tasks} заданий сегодня",
                    "reward": 25,
                    "progress": 0,
                    "target": target_tasks,
                    "icon": "📚",
                }
            )

            # Задание на правильность
            if level >= 3:
                challenges.append(
                    {
                        "id": "accuracy",
                        "title": "Точность 90%+",
                        "description": "Достигните точности 90% или выше",
                        "reward": 30,
                        "progress": 0,
                        "target": 90,
                        "icon": "🎯",
                    }
                )

            # Задание на изучение нового предмета
            if level >= 5:
                challenges.append(
                    {
                        "id": "new_subject",
                        "title": "Новый предмет",
                        "description": "Изучите новый предмет",
                        "reward": 50,
                        "progress": 0,
                        "target": 1,
                        "icon": "🌟",
                    }
                )

            return challenges

        except Exception as e:
            logger.error(f"Ошибка при получении ежедневных заданий: {e}")
            return []

    @sync_to_async
    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """Получает таблицу лидеров"""
        try:
            top_users = UnifiedProfile.objects.filter(  # type: ignore
                points__gt=0
            ).order_by("-points")[:limit]

            leaderboard = []
            for i, profile in enumerate(top_users, 1):
                # Получаем или создаем Django User для отображения имени
                django_user, _ = User.objects.get_or_create(  # type: ignore
                    username=f"tg_{profile.telegram_id}",
                    defaults={"first_name": f"User {profile.telegram_id}"},
                )

                leaderboard.append(
                    {
                        "rank": i,
                        "username": django_user.username
                        or f"Пользователь {profile.telegram_id}",
                        "level": profile.level or 1,
                        "points": profile.points or 0,
                        "emoji": self._get_rank_emoji(i),
                    }
                )

            return leaderboard

        except Exception as e:
            logger.error(f"Ошибка при получении таблицы лидеров: {e}")
            return []

    def create_gamification_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Создаёт клавиатуру для геймификации"""
        keyboard = [
            [
                InlineKeyboardButton("🏆 Статистика", callback_data=f"stats_{user_id}"),
                InlineKeyboardButton(
                    "🎯 Достижения", callback_data=f"achievements_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Прогресс", callback_data=f"progress_{user_id}"
                ),
                InlineKeyboardButton("🏅 Лидеры", callback_data="leaderboard"),
            ],
            [
                InlineKeyboardButton(
                    "📅 Ежедневные задания", callback_data=f"daily_{user_id}"
                ),
                InlineKeyboardButton("🎁 Бонусы", callback_data=f"bonus_{user_id}"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_progress_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Создаёт клавиатуру для прогресса"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📈 Общий прогресс", callback_data=f"overall_progress_{user_id}"
                ),
                InlineKeyboardButton(
                    "📚 По предметам", callback_data=f"subjects_progress_{user_id}"
                ),
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"gamification_{user_id}")],
        ]
        return InlineKeyboardMarkup(keyboard)

    def _calculate_level(self, points: int) -> int:
        """Вычисляет уровень на основе очков"""
        if points <= 0:
            return 1
        return (points // self.level_multiplier) + 1

    def _calculate_rank(self, points: int) -> str:
        """Вычисляет ранг пользователя"""
        if points >= 1000:
            return "🥇 Мастер"
        elif points >= 500:
            return "🥈 Эксперт"
        elif points >= 100:
            return "🥉 Ученик"
        else:
            return "📚 Новичок"

    def _get_rank_emoji(self, rank: int) -> str:
        """Возвращает эмодзи для ранга"""
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        elif rank <= 10:
            return "⭐"
        else:
            return "📊"

    def _create_achievement(
        self, user, title: str, description: str, icon: str
    ) -> dict | None:
        """Создаёт новое достижение"""
        try:
            # Проверяем, не получено ли уже это достижение
            existing = Achievement.objects.filter(  # type: ignore
                user=user, title=title
            ).first()

            if existing:
                return None

            # Создаём новое достижение
            achievement = Achievement.objects.create(  # type: ignore
                user=user,
                title=title,
                description=description,
                icon=icon,
                date_earned=timezone.now(),
            )

            return {
                "title": title,
                "description": description,
                "icon": icon,
                "date_earned": achievement.date_earned,
            }

        except Exception as e:
            logger.error(f"Ошибка при создании достижения: {e}")
            return None
