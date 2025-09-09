"""
Middleware для контроля доступа к премиум функциям
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PremiumAccessMiddleware(MiddlewareMixin):
    """
    Middleware для проверки доступа к премиум функциям
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """
        Проверяет доступ к премиум эндпоинтам
        """
        # Список эндпоинтов, требующих премиум доступ
        premium_endpoints = [
            '/api/ai/ask/',
            '/api/fipi/search/',
            '/api/ai/statistics/',
        ]

        # Проверяем, является ли запрос к премиум эндпоинту
        if any(request.path.startswith(endpoint) for endpoint in premium_endpoints):
            return self._check_premium_access(request)

        return None

    def _check_premium_access(self, request):
        """
        Проверяет, имеет ли пользователь доступ к премиум функциям
        """
        try:
            # Если пользователь не авторизован, разрешаем ограниченный доступ
            if not request.user.is_authenticated:
                return self._check_rate_limit(request, is_anonymous=True)

            # Получаем профиль пользователя
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)  # type: ignore

            # Если пользователь премиум, разрешаем полный доступ
            if profile.is_premium:
                return None

            # Для бесплатных пользователей проверяем лимиты
            return self._check_rate_limit(request, user_id=request.user.id)

        except Exception as e:
            logger.error(f"Ошибка при проверке премиум доступа: {e}")
            # В случае ошибки разрешаем ограниченный доступ
            return self._check_rate_limit(request, is_anonymous=True)

    def _check_rate_limit(self, request, user_id=None, is_anonymous=False):
        """
        Проверяет лимиты запросов для бесплатных пользователей
        """
        # Лимиты для бесплатных пользователей
        if is_anonymous:
            daily_limit = 5
            hourly_limit = 2
            cache_key_prefix = "anonymous"
        else:
            daily_limit = 20
            hourly_limit = 5
            cache_key_prefix = f"user_{user_id}"

        # Проверяем дневной лимит
        daily_key = f"{cache_key_prefix}_daily_{request.META.get('REMOTE_ADDR', 'unknown')}"
        daily_count = cache.get(daily_key, 0)
        
        if daily_count >= daily_limit:
            return JsonResponse({
                "error": "Daily request limit exceeded",
                "limit": daily_limit,
                "upgrade_required": True
            }, status=429)

        # Проверяем часовой лимит
        hourly_key = f"{cache_key_prefix}_hourly_{request.META.get('REMOTE_ADDR', 'unknown')}"
        hourly_count = cache.get(hourly_key, 0)
        
        if hourly_count >= hourly_limit:
            return JsonResponse({
                "error": "Hourly request limit exceeded",
                "limit": hourly_limit,
                "upgrade_required": True
            }, status=429)

        # Увеличиваем счетчики
        cache.set(daily_key, daily_count + 1, 86400)  # 24 часа
        cache.set(hourly_key, hourly_count + 1, 3600)  # 1 час

        return None
