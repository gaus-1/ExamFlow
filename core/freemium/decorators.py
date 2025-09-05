"""
Декораторы для проверки лимитов FREEMIUM
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import DailyUsage, SubscriptionLimit


def check_ai_limits(view_func):
    """Декоратор для проверки лимитов ИИ"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        
        # Получаем ежедневное использование
        daily_usage = DailyUsage.get_today_usage(request.user)
        
        # Проверяем лимиты
        if not daily_usage.can_make_request():
            if request.path.endswith('/api/'):
                return JsonResponse({
                    'error': 'Превышен лимит запросов к ИИ',
                    'limit_reached': True,
                    'daily_limit': request.subscription_limits.daily_ai_requests,
                    'used_today': daily_usage.ai_requests_count,
                    'upgrade_url': '/pricing/'
                }, status=429)
            else:
                messages.warning(request, 'Превышен лимит запросов к ИИ. Перейдите на подписку для безлимитного доступа.')
                return redirect('pricing')
        
        # Увеличиваем счетчик использования
        if not daily_usage.increment_usage():
            if request.path.endswith('/api/'):
                return JsonResponse({
                    'error': 'Не удалось зарегистрировать запрос',
                    'limit_reached': True
                }, status=429)
            else:
                messages.error(request, 'Ошибка регистрации запроса')
                return redirect('pricing')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_premium(view_func):
    """Декоратор для проверки премиум подписки"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        
        # Проверяем премиум статус
        if not hasattr(request, 'user_subscription') or not request.user_subscription.is_premium:
            if request.path.endswith('/api/'):
                return JsonResponse({
                    'error': 'Требуется премиум подписка',
                    'upgrade_required': True,
                    'upgrade_url': '/pricing/'
                }, status=403)
            else:
                messages.warning(request, 'Эта функция доступна только с премиум подпиской.')
                return redirect('pricing')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def check_subscription_limits(view_func):
    """Декоратор для проверки общих лимитов подписки"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        
        # Проверяем активность подписки
        if hasattr(request, 'user_subscription') and request.user_subscription.is_expired:
            if request.path.endswith('/api/'):
                return JsonResponse({
                    'error': 'Подписка истекла',
                    'subscription_expired': True,
                    'renew_url': '/pricing/'
                }, status=403)
            else:
                messages.warning(request, 'Ваша подписка истекла. Продлите её для продолжения использования.')
                return redirect('pricing')
        
        return view_func(request, *args, **kwargs)
    return wrapper
