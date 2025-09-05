"""
Система контроля премиум-доступа
Включает middleware, проверку подписок и кэширование
"""

import logging
from typing import Dict, List, Optional, Any
from functools import wraps
from datetime import datetime

from django.http import HttpRequest, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import UserProfile, Subscription
from core.models import UnifiedProfile

logger = logging.getLogger(__name__)


class PremiumAccessControl:
    """Основной класс контроля премиум-доступа"""

    def __init__(self):
        self.cache_timeout = getattr(settings, 'PREMIUM_CACHE_TIMEOUT', 300)  # 5 минут
        self.feature_cache = {}

    def is_premium_user(self, user: User) -> bool:
        """Проверяет, является ли пользователь премиум"""
        if not user or not user.is_authenticated:
            return False

        try:
            # Проверяем кэш
            cache_key = f"premium_user_{user.id}"  # type: ignore
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            # Получаем профиль пользователя
            try:
                profile = UnifiedProfile.objects.get(user=user)  # type: ignore
                is_premium = profile.is_premium
            except UnifiedProfile.DoesNotExist:  # type: ignore
                # Fallback на старую модель
                try:
                    profile = UserProfile.objects.get(user=user)  # type: ignore
                    is_premium = profile.is_premium
                except UserProfile.DoesNotExist:  # type: ignore
                    is_premium = False

            # Кэшируем результат
            cache.set(cache_key, is_premium, self.cache_timeout)
            return is_premium

        except Exception as e:
            # type: ignore
            logger.error(
                f"Ошибка проверки премиум статуса для пользователя {user.id}: {e}")
            return False

    def has_active_subscription(self, user: User) -> bool:
        """Проверяет активную подписку"""
        if not user or not user.is_authenticated:
            return False

        try:
            cache_key = f"active_subscription_{user.id}"  # type: ignore
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Проверяем активную подписку
            now = datetime.now()
            active_subscription = Subscription.objects.filter(  # type: ignore
                user=user,
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).exists()

            cache.set(cache_key, active_subscription, self.cache_timeout)
            return active_subscription

        except Exception as e:
            # type: ignore
            logger.error(f"Ошибка проверки подписки для пользователя {user.id}: {e}")
            return False

    def get_user_features(self, user: User) -> List[str]:
        """Получает список доступных функций для пользователя"""
        if not user or not user.is_authenticated:
            return ['basic']

        try:
            cache_key = f"user_features_{user.id}"  # type: ignore
            cached_features = cache.get(cache_key)
            if cached_features is not None:
                return cached_features

            features = ['basic']

            if self.is_premium_user(user):
                features.extend([
                    'premium_content',
                    'pdf_export',
                    'advanced_search',
                    'personalized_recommendations',
                    'version_comparison',
                    'unlimited_requests',
                    'priority_support'
                ])

            if self.has_active_subscription(user):
                features.append('subscription_benefits')

            cache.set(cache_key, features, self.cache_timeout)
            return features

        except Exception as e:
            # type: ignore
            logger.error(f"Ошибка получения функций для пользователя {user.id}: {e}")
            return ['basic']

    def can_access_feature(self, user: User, feature: str) -> bool:
        """Проверяет доступ к конкретной функции"""
        user_features = self.get_user_features(user)
        return feature in user_features

    def get_usage_limits(self, user: User) -> Dict[str, int]:
        """Получает лимиты использования для пользователя"""
        if not user or not user.is_authenticated:
            return {
                'daily_requests': 10,
                'monthly_requests': 100,
                'pdf_exports': 0,
                'advanced_searches': 0
            }

        if self.is_premium_user(user):
            return {
                'daily_requests': 1000,
                'monthly_requests': 10000,
                'pdf_exports': 50,
                'advanced_searches': 100
            }
        else:
            return {
                'daily_requests': 10,
                'monthly_requests': 100,
                'pdf_exports': 0,
                'advanced_searches': 0
            }


class PremiumMiddleware:
    """Middleware для проверки премиум-доступа"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.access_control = PremiumAccessControl()

    def __call__(self, request):
        # Добавляем информацию о премиум статусе в request
        if request.user.is_authenticated:
            request.is_premium = self.access_control.is_premium_user(request.user)
            request.user_features = self.access_control.get_user_features(request.user)
            request.usage_limits = self.access_control.get_usage_limits(request.user)
        else:
            request.is_premium = False
            request.user_features = ['basic']
            request.usage_limits = self.access_control.get_usage_limits(
                None)  # type: ignore

        response = self.get_response(request)
        return response


def premium_required(feature: str = 'premium_content'):
    """Декоратор для проверки премиум-доступа"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:  # type: ignore
                return JsonResponse({
                    'error': 'Требуется авторизация',
                    'code': 'AUTH_REQUIRED'
                }, status=401)

            access_control = PremiumAccessControl()
            if not access_control.can_access_feature(
                    request.user, feature):  # type: ignore
                return JsonResponse({
                    'error': 'Требуется премиум-подписка',
                    'code': 'PREMIUM_REQUIRED',
                    'feature': feature,
                    'upgrade_url': '/auth/subscribe/'
                }, status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def subscription_required(view_func):
    """Декоратор для проверки активной подписки"""
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:  # type: ignore
            return JsonResponse({
                'error': 'Требуется авторизация',
                'code': 'AUTH_REQUIRED'
            }, status=401)

        access_control = PremiumAccessControl()
        if not access_control.has_active_subscription(request.user):  # type: ignore
            return JsonResponse({
                'error': 'Требуется активная подписка',
                'code': 'SUBSCRIPTION_REQUIRED',
                'subscribe_url': '/auth/subscribe/'
            }, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper


class UsageTracker:
    """Трекер использования для контроля лимитов"""

    def __init__(self):
        self.cache_timeout = 86400  # 24 часа

    def track_usage(self, user: User, action: str, count: int = 1) -> bool:
        """Отслеживает использование и проверяет лимиты"""
        if not user or not user.is_authenticated:  # type: ignore
            return False

        try:
            today = datetime.now().date()
            cache_key = f"usage_{user.id}_{action}_{today}"  # type: ignore

            current_usage = cache.get(cache_key, 0)
            new_usage = current_usage + count

            # Получаем лимиты
            access_control = PremiumAccessControl()
            limits = access_control.get_usage_limits(user)

            # Проверяем лимит
            limit_key = f"{action}_limit"
            if limit_key in limits:
                if new_usage > limits[limit_key]:
                    return False

            # Обновляем использование
            cache.set(cache_key, new_usage, self.cache_timeout)
            return True

        except Exception as e:
            logger.error(f"Ошибка отслеживания использования: {e}")
            return False

    def get_usage_stats(self, user: User, action: str) -> Dict[str, Any]:
        """Получает статистику использования"""
        if not user or not user.is_authenticated:  # type: ignore
            return {'current': 0, 'limit': 0, 'remaining': 0}

        try:
            today = datetime.now().date()
            cache_key = f"usage_{user.id}_{action}_{today}"  # type: ignore

            current_usage = cache.get(cache_key, 0)

            access_control = PremiumAccessControl()
            limits = access_control.get_usage_limits(user)

            limit_key = f"{action}_limit"
            limit = limits.get(limit_key, 0)
            remaining = max(0, limit - current_usage)

            return {
                'current': current_usage,
                'limit': limit,
                'remaining': remaining,
                'percentage': (current_usage / limit * 100) if limit > 0 else 0
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики использования: {e}")
            return {'current': 0, 'limit': 0, 'remaining': 0}


class PremiumContentWrapper:
    """Обертка для премиум-контента"""

    def __init__(self, access_control: PremiumAccessControl):
        self.access_control = access_control

    def wrap_content(self, content: Any, user: User,
                     feature: str = 'premium_content') -> Dict[str, Any]:
        """Оборачивает контент с проверкой доступа"""
        if self.access_control.can_access_feature(user, feature):
            return {
                'content': content,
                'is_premium': True,
                'access_granted': True
            }
        else:
            return {
                'content': None,
                'is_premium': True,
                'access_granted': False,
                'upgrade_message': 'Для доступа к этому контенту требуется премиум-подписка',
                'upgrade_url': '/auth/subscribe/'}

    def get_preview_content(self, content: Any, preview_length: int = 200) -> str:
        """Возвращает превью контента для не-премиум пользователей"""
        if isinstance(content, str):
            return content[:preview_length] + \
                '...' if len(content) > preview_length else content
        elif isinstance(content, dict) and 'text' in content:
            text = content['text']
            return text[:preview_length] + '...' if len(text) > preview_length else text
        else:
            return str(content)[:preview_length] + '...'


# Глобальные экземпляры
_access_control: Optional[PremiumAccessControl] = None
_usage_tracker: Optional[UsageTracker] = None


def get_access_control() -> PremiumAccessControl:
    """Получает глобальный экземпляр контроля доступа"""
    global _access_control
    if _access_control is None:
        _access_control = PremiumAccessControl()
    return _access_control


def get_usage_tracker() -> UsageTracker:
    """Получает глобальный экземпляр трекера использования"""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker
