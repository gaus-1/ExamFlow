"""
Взгляды для модуля аутентификации ExamFlow 2.0
"""

from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import messages
from django.utils.crypto import get_random_string


def simple_login(request):
    """Упрощенная страница входа"""
    return render(request, 'auth/simple_login.html')


def telegram_login(request):
    """Инициация входа через Telegram"""
    # Telegram Login Widget
    redirect_url = request.build_absolute_uri('/auth/telegram/callback/')

    # Параметры для Telegram Login Widget
    params = {
        'bot_id': settings.TELEGRAM_BOT_ID,
        'origin': request.get_host(),
        'return_to': redirect_url,
        'request_access': 'write'
    }

    telegram_url = f"https://oauth.telegram.org/auth?{urlencode(params)}"
    return redirect(telegram_url)


def telegram_callback(request):
    """Callback для Telegram авторизации"""
    try:
        # Получаем данные от Telegram
        auth_data = request.GET.dict()

        # Проверяем подпись (упрощенно для демо)
        if not _verify_telegram_auth(auth_data):
            messages.error(request, 'Ошибка авторизации через Telegram')
            return redirect('auth:simple_login')

        # Создаем или находим пользователя
        telegram_id = auth_data.get('id')
        username = f"telegram_{telegram_id}"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': auth_data.get('first_name', ''),
                'last_name': auth_data.get('last_name', ''),
                'email': f"{username}@telegram.local"
            }
        )

        # Авторизуем пользователя
        login(request, user)

        if created:
            messages.success(request, 'Добро пожаловать в ExamFlow!')
        else:
            messages.success(request, 'Добро пожаловать обратно!')

        return redirect('learning:home')

    except Exception as e:
        messages.error(request, f'Ошибка авторизации: {str(e)}')
        return redirect('auth:simple_login')


def google_login(request):
    """Инициация входа через Google"""
    # Google OAuth 2.0
    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'demo')
    redirect_uri = request.build_absolute_uri('/auth/google/callback/')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': get_random_string(32)
    }

    google_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(google_url)


def google_callback(request):
    """Callback для Google авторизации"""
    try:
        code = request.GET.get('code')
        if not code:
            messages.error(request, 'Ошибка авторизации через Google')
            return redirect('auth:simple_login')

        # Обмениваем код на токен (упрощенно для демо)
        # В реальном проекте здесь будет обмен кода на access_token

        # Создаем пользователя (демо)
        user, created = User.objects.get_or_create(
            username=f"google_{get_random_string(8)}",
            defaults={
                'first_name': 'Google',
                'last_name': 'User',
                'email': f"google_{get_random_string(8)}@google.local"
            }
        )

        login(request, user)

        if created:
            messages.success(request, 'Добро пожаловать в ExamFlow!')
        else:
            messages.success(request, 'Добро пожаловать обратно!')

        return redirect('learning:home')

    except Exception as e:
        messages.error(request, f'Ошибка авторизации: {str(e)}')
        return redirect('auth:simple_login')


def yandex_login(request):
    """Инициация входа через Яндекс"""
    # Яндекс OAuth 2.0
    client_id = getattr(settings, 'YANDEX_OAUTH_CLIENT_ID', 'demo')
    redirect_uri = request.build_absolute_uri('/auth/yandex/callback/')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': get_random_string(32)
    }

    yandex_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    return redirect(yandex_url)


def yandex_callback(request):
    """Callback для Яндекс авторизации"""
    try:
        code = request.GET.get('code')
        if not code:
            messages.error(request, 'Ошибка авторизации через Яндекс')
            return redirect('auth:simple_login')

        # Создаем пользователя (демо)
        user, created = User.objects.get_or_create(
            username=f"yandex_{get_random_string(8)}",
            defaults={
                'first_name': 'Яндекс',
                'last_name': 'Пользователь',
                'email': f"yandex_{get_random_string(8)}@yandex.local"
            }
        )

        login(request, user)

        if created:
            messages.success(request, 'Добро пожаловать в ExamFlow!')
        else:
            messages.success(request, 'Добро пожаловать обратно!')

        return redirect('learning:home')

    except Exception as e:
        messages.error(request, f'Ошибка авторизации: {str(e)}')
        return redirect('auth:simple_login')


def guest_access(request):
    """Гостевой доступ"""
    # Создаем временного пользователя
    guest_username = f"guest_{get_random_string(8)}"
    user, created = User.objects.get_or_create(
        username=guest_username,
        defaults={
            'first_name': 'Гость',
            'last_name': '',
            'email': f"{guest_username}@guest.local"
        }
    )

    login(request, user)
    messages.info(request, 'Вы вошли как гость. Данные сохраняются локально.')

    return redirect('learning:subjects_list')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('learning:home')


def _verify_telegram_auth(auth_data):
    """Проверка подписи Telegram (упрощенно)"""
    # В реальном проекте здесь должна быть проверка HMAC подписи
    # Для демо просто проверяем наличие обязательных полей
    required_fields = ['id', 'first_name', 'auth_date']
    return all(field in auth_data for field in required_fields)
