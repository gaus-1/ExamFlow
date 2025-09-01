"""
Сервис для работы с унифицированными профилями пользователей
"""

from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import UnifiedProfile, DailyChallenge, UserChallenge
import logging

logger = logging.getLogger(__name__)


class UnifiedProfileService:
    """Сервис для управления унифицированными профилями"""
    
    @staticmethod
    def get_or_create_profile(telegram_id: int, **kwargs) -> UnifiedProfile:
        """Получает или создает унифицированный профиль"""
        try:
            profile, created = UnifiedProfile.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'display_name': kwargs.get('display_name', f'Пользователь {telegram_id}'),
                    'telegram_username': kwargs.get('telegram_username', ''),
                    'notification_settings': {
                        'daily_challenges': True,
                        'achievements': True,
                        'level_up': True,
                        'reminders': True
                    }
                }
            )
            
            if created:
                logger.info(f"Создан новый унифицированный профиль для TG ID: {telegram_id}")
            
            # Обновляем последнюю активность
            profile.last_activity = timezone.now()
            profile.save()
            
            return profile
            
        except Exception as e:
            logger.error(f"Ошибка при создании/получении профиля для TG ID {telegram_id}: {e}")
            raise
    
    @staticmethod
    def link_django_user(profile: UnifiedProfile, user: User) -> bool:
        """Связывает профиль с Django пользователем"""
        try:
            profile.user = user
            profile.save()
            logger.info(f"Профиль {profile.telegram_id} связан с Django пользователем {user.username}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при связывании профиля с пользователем: {e}")
            return False
    
    @staticmethod
    def update_stats(profile: UnifiedProfile, solved_correctly: bool = True) -> Dict[str, Any]:
        """Обновляет статистику профиля после решения задачи"""
        try:
            result = {'level_up': False, 'achievements': []}
            
            if solved_correctly:
                profile.total_solved += 1
                profile.current_streak += 1
                
                # Обновляем лучшую серию
                if profile.current_streak > profile.best_streak:
                    profile.best_streak = profile.current_streak
                
                # Добавляем опыт
                xp_gained = 10 + (profile.current_streak // 5)  # Бонус за серию
                level_up = profile.add_experience(xp_gained)
                result['level_up'] = level_up
                result['xp_gained'] = xp_gained
                
                # Проверяем достижения
                achievements = UnifiedProfileService._check_achievements(profile)
                result['achievements'] = achievements
                
            else:
                # Сбрасываем серию при неправильном ответе
                profile.current_streak = 0
            
            profile.save()
            
            # Обновляем прогресс по ежедневным вызовам
            UnifiedProfileService._update_daily_challenges(profile, solved_correctly)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики профиля {profile.telegram_id}: {e}")
            return {'level_up': False, 'achievements': []}
    
    @staticmethod
    def _check_achievements(profile: UnifiedProfile) -> list:
        """Проверяет и добавляет новые достижения"""
        new_achievements = []
        
        # Достижения за количество решенных задач
        task_achievements = {
            10: 'first_10_tasks',
            50: 'first_50_tasks',
            100: 'century_solver',
            500: 'task_master',
            1000: 'grand_master'
        }
        
        for count, achievement_id in task_achievements.items():
            if profile.total_solved >= count:
                if profile.add_achievement(achievement_id):
                    new_achievements.append(achievement_id)
        
        # Достижения за серии
        streak_achievements = {
            5: 'streak_5',
            10: 'streak_10',
            25: 'streak_25',
            50: 'streak_50',
            100: 'streak_legend'
        }
        
        for count, achievement_id in streak_achievements.items():
            if profile.current_streak >= count:
                if profile.add_achievement(achievement_id):
                    new_achievements.append(achievement_id)
        
        # Достижения за уровни
        level_achievements = {
            5: 'level_5',
            10: 'level_10',
            25: 'level_25',
            50: 'level_50',
            100: 'level_100'
        }
        
        for level, achievement_id in level_achievements.items():
            if profile.level >= level:
                if profile.add_achievement(achievement_id):
                    new_achievements.append(achievement_id)
        
        return new_achievements
    
    @staticmethod
    def _update_daily_challenges(profile: UnifiedProfile, solved_correctly: bool):
        """Обновляет прогресс по ежедневным вызовам"""
        try:
            today = timezone.now().date()
            daily_challenges = DailyChallenge.objects.filter(date=today)
            
            for challenge in daily_challenges:
                user_challenge, created = UserChallenge.objects.get_or_create(
                    profile=profile,
                    challenge=challenge,
                    defaults={'current_progress': 0}
                )
                
                if not user_challenge.is_completed:
                    # Обновляем прогресс в зависимости от типа вызова
                    if challenge.challenge_type == 'solve_tasks' and solved_correctly:
                        user_challenge.current_progress += 1
                    elif challenge.challenge_type == 'streak':
                        user_challenge.current_progress = profile.current_streak
                    
                    # Проверяем завершение вызова
                    if user_challenge.current_progress >= challenge.target_value:
                        user_challenge.is_completed = True
                        user_challenge.completed_at = timezone.now()
                        
                        # Добавляем награду
                        profile.add_experience(challenge.reward_xp)
                        
                        logger.info(f"Пользователь {profile.telegram_id} завершил вызов: {challenge.title}")
                    
                    user_challenge.save()
                    
        except Exception as e:
            logger.error(f"Ошибка при обновлении ежедневных вызовов для профиля {profile.telegram_id}: {e}")
    
    @staticmethod
    def get_daily_challenges(profile: UnifiedProfile) -> Dict[str, Any]:
        """Получает ежедневные вызовы для пользователя"""
        try:
            today = timezone.now().date()
            daily_challenges = DailyChallenge.objects.filter(date=today)
            
            result = {
                'challenges': [],
                'completed_count': 0,
                'total_count': daily_challenges.count()
            }
            
            for challenge in daily_challenges:
                user_challenge, _ = UserChallenge.objects.get_or_create(
                    profile=profile,
                    challenge=challenge,
                    defaults={'current_progress': 0}
                )
                
                challenge_data = {
                    'id': challenge.id,
                    'title': challenge.title,
                    'description': challenge.description,
                    'type': challenge.challenge_type,
                    'target_value': challenge.target_value,
                    'current_progress': user_challenge.current_progress,
                    'progress_percentage': user_challenge.progress_percentage,
                    'is_completed': user_challenge.is_completed,
                    'reward_xp': challenge.reward_xp
                }
                
                result['challenges'].append(challenge_data)
                
                if user_challenge.is_completed:
                    result['completed_count'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении ежедневных вызовов для профиля {profile.telegram_id}: {e}")
            return {'challenges': [], 'completed_count': 0, 'total_count': 0}
    
    @staticmethod
    def get_profile_stats(profile: UnifiedProfile) -> Dict[str, Any]:
        """Получает полную статистику профиля"""
        try:
            daily_challenges = UnifiedProfileService.get_daily_challenges(profile)
            
            return {
                'profile': {
                    'display_name': profile.display_name,
                    'level': profile.level,
                    'experience_points': profile.experience_points,
                    'experience_to_next_level': profile.experience_to_next_level,
                    'total_solved': profile.total_solved,
                    'current_streak': profile.current_streak,
                    'best_streak': profile.best_streak,
                    'achievements_count': len(profile.achievements),
                    'avatar_url': profile.avatar_url
                },
                'daily_challenges': daily_challenges,
                'recent_achievements': profile.achievements[-5:] if profile.achievements else []
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики профиля {profile.telegram_id}: {e}")
            return {}


class DailyChallengeService:
    """Сервис для управления ежедневными вызовами"""
    
    @staticmethod
    def create_daily_challenges(date=None):
        """Создает ежедневные вызовы на указанную дату"""
        if date is None:
            date = timezone.now().date()
        
        try:
            # Удаляем существующие вызовы на эту дату
            DailyChallenge.objects.filter(date=date).delete()
            
            challenges = [
                {
                    'title': 'Решить 5 задач',
                    'description': 'Решите правильно 5 задач любой сложности',
                    'challenge_type': 'solve_tasks',
                    'target_value': 5,
                    'reward_xp': 50
                },
                {
                    'title': 'Серия из 3 задач',
                    'description': 'Решите подряд 3 задачи без ошибок',
                    'challenge_type': 'streak',
                    'target_value': 3,
                    'reward_xp': 30
                }
            ]
            
            created_challenges = []
            for challenge_data in challenges:
                challenge = DailyChallenge.objects.create(
                    date=date,
                    **challenge_data
                )
                created_challenges.append(challenge)
            
            logger.info(f"Созданы ежедневные вызовы на {date}: {len(created_challenges)} вызовов")
            return created_challenges
            
        except Exception as e:
            logger.error(f"Ошибка при создании ежедневных вызовов на {date}: {e}")
            return []
