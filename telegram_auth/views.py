"""
Views для Telegram аутентификации ExamFlow
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.shortcuts import render

from .services import telegram_auth_service

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def telegram_auth_callback(request):
    """
    Callback для обработки данных от Telegram Login Widget
    """
    try:
        # Получаем IP и User Agent
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Парсим JSON данные
        try:
            auth_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Неверный формат JSON данных'
            }, status=400)

        # Аутентифицируем пользователя
        success, user, message = telegram_auth_service.authenticate_user(
            auth_data, ip_address, user_agent
        )

        if success:
            # Получаем токен сессии
            session = user.auth_sessions.filter(is_active=True).first()
            session_token = session.session_token if session else None

            return JsonResponse({
                'success': True,
                'message': message,
                'user': {
                    'telegram_id': user.telegram_id,
                    'username': user.telegram_username,
                    'first_name': user.telegram_first_name,
                    'display_name': user.display_name,
                    'is_premium': user.is_premium
                },
                'session_token': session_token,
                'redirect_url': '/dashboard/'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=400)

    except Exception as e:
        logger.error(f"Ошибка в telegram_auth_callback: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }, status=500)


@require_http_methods(["GET"])
def telegram_login_widget(request):
    """
    Отображает страницу с Telegram Login Widget
    """
    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'ExamFlowBot')
    site_url = getattr(settings, 'SITE_URL', 'https://examflow.ru')

    context = {
        'bot_username': bot_username,
        'site_url': site_url,
        'callback_url': f"{site_url}/auth/telegram/callback/"
    }

    return render(request, 'telegram_auth/login_widget.html', context)


@require_http_methods(["GET"])
def auth_success(request):
    """
    Страница успешной аутентификации
    """
    return render(request, 'telegram_auth/success.html')


@require_http_methods(["GET"])
def auth_error(request):
    """
    Страница ошибки аутентификации
    """
    error_message = request.GET.get('message', 'Произошла ошибка аутентификации')
    return render(request, 'telegram_auth/error.html', {
        'error_message': error_message
    })


@method_decorator(csrf_exempt, name='dispatch')
class TelegramAuthAPI(View):
    """API для работы с Telegram аутентификацией"""

    def post(self, request):
        """Обработка POST запросов для аутентификации"""
        return telegram_auth_callback(request)

    def get(self, request):
        """Получение информации о текущем пользователе"""
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not session_token:
            return JsonResponse({
                'success': False,
                'message': 'Токен сессии не предоставлен'
            }, status=401)

        user = telegram_auth_service.get_user_by_session(session_token)

        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Недействительная сессия'
            }, status=401)

        return JsonResponse({
            'success': True,
            'user': {
                'telegram_id': user.telegram_id,
                'username': user.telegram_username,
                'first_name': user.telegram_first_name,
                'display_name': user.display_name,
                'is_premium': user.is_premium,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })

    def delete(self, request):
        """Выход из системы"""
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not session_token:
            return JsonResponse({
                'success': False,
                'message': 'Токен сессии не предоставлен'
            }, status=401)

        success = telegram_auth_service.logout_user(session_token)

        return JsonResponse({
            'success': success,
            'message': 'Выход выполнен успешно' if success else 'Ошибка выхода'
        })


@require_http_methods(["GET"])
def telegram_auth_status(request):
    """
    Проверка статуса аутентификации
    """
    session_token = request.GET.get('token')

    if not session_token:
        return JsonResponse({
            'authenticated': False,
            'message': 'Токен не предоставлен'
        })

    user = telegram_auth_service.get_user_by_session(session_token)

    if user:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'telegram_id': user.telegram_id,
                'username': user.telegram_username,
                'first_name': user.telegram_first_name,
                'display_name': user.display_name,
                'is_premium': user.is_premium
            }
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'message': 'Сессия недействительна или истекла'
        })
