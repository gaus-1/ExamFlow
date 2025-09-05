"""
Middleware для проверки лимитов FREEMIUM
"""

from django.http import JsonResponse
from .models import UserSubscription, DailyUsage, SubscriptionLimit


class FreemiumMiddleware:
    """Middleware для проверки лимитов подписки"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем лимиты только для аутентифицированных пользователей
        if request.user.is_authenticated:
            self._check_subscription_limits(request)

        response = self.get_response(request)
        return response

    def _check_subscription_limits(self, request):
        """Проверка лимитов подписки"""
        user = request.user

        # Создаем подписку если её нет
        if not hasattr(user, 'subscription'):
            UserSubscription.objects.create(user=user, subscription_type='free')

        # Добавляем информацию о подписке в request
        request.user_subscription = user.subscription
        request.subscription_limits = SubscriptionLimit.get_limits(
            user.subscription.subscription_type)

        # Проверяем ежедневное использование ИИ
        if request.path.startswith('/ai/'):
            daily_usage = DailyUsage.get_today_usage(user)
            request.daily_usage = daily_usage

            # Проверяем лимит запросов
            if not daily_usage.can_make_request():
                if request.path.endswith('/api/chat/'):
                    return JsonResponse({
                        'error': 'Превышен лимит запросов к ИИ',
                        'limit_reached': True,
                        'daily_limit': request.subscription_limits.daily_ai_requests,
                        'used_today': daily_usage.ai_requests_count,
                        'upgrade_url': '/pricing/'
                    }, status=429)
                else:
                    # Для обычных запросов - редирект на страницу тарифов
                    from django.shortcuts import redirect
                    return redirect('pricing')
