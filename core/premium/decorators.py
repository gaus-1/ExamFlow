"""
Декораторы для контроля доступа к премиум функциям
"""

import logging
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


def premium_required(view_func):
    """
    Декоратор, требующий премиум подписку для доступа к функции
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                "error": "Authentication required",
                "upgrade_required": True
            }, status=401)

        try:
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)  # type: ignore
            
            if not profile.is_premium:
                return JsonResponse({
                    "error": "Premium subscription required",
                    "upgrade_required": True,
                    "current_plan": "free",
                    "upgrade_url": "/subscription/"
                }, status=403)

            return view_func(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Ошибка при проверке премиум доступа: {e}")
            return JsonResponse({
                "error": "Access check failed",
                "upgrade_required": True
            }, status=500)

    return wrapper


def rate_limited(max_requests_per_hour=10, max_requests_per_day=50):
    """
    Декоратор для ограничения частоты запросов
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Определяем ключ для кеша
            if request.user.is_authenticated:
                cache_key_prefix = f"user_{request.user.id}"
            else:
                cache_key_prefix = f"anonymous_{request.META.get('REMOTE_ADDR', 'unknown')}"

            # Проверяем дневной лимит
            daily_key = f"{cache_key_prefix}_daily"
            daily_count = cache.get(daily_key, 0)
            
            if daily_count >= max_requests_per_day:
                return JsonResponse({
                    "error": "Daily request limit exceeded",
                    "limit": max_requests_per_day,
                    "reset_time": "24 hours"
                }, status=429)

            # Проверяем часовой лимит
            hourly_key = f"{cache_key_prefix}_hourly"
            hourly_count = cache.get(hourly_key, 0)
            
            if hourly_count >= max_requests_per_hour:
                return JsonResponse({
                    "error": "Hourly request limit exceeded",
                    "limit": max_requests_per_hour,
                    "reset_time": "1 hour"
                }, status=429)

            # Увеличиваем счетчики
            cache.set(daily_key, daily_count + 1, 86400)  # 24 часа
            cache.set(hourly_key, hourly_count + 1, 3600)  # 1 час

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def free_tier_allowed(view_func):
    """
    Декоратор, разрешающий доступ бесплатным пользователям с ограничениями
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Если пользователь не авторизован, разрешаем с ограничениями
        if not request.user.is_authenticated:
            return rate_limited(max_requests_per_hour=2, max_requests_per_day=5)(view_func)(request, *args, **kwargs)

        try:
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)  # type: ignore
            
            # Премиум пользователи получают полный доступ
            if profile.is_premium:
                return view_func(request, *args, **kwargs)

            # Бесплатные пользователи получают ограниченный доступ
            return rate_limited(max_requests_per_hour=10, max_requests_per_day=20)(view_func)(request, *args, **kwargs)

        except Exception as e:
            logger.error(f"Ошибка при проверке доступа: {e}")
            # В случае ошибки применяем строгие ограничения
            return rate_limited(max_requests_per_hour=1, max_requests_per_day=3)(view_func)(request, *args, **kwargs)

    return wrapper
