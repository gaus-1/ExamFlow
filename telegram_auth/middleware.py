"""
Middleware для Telegram аутентификации ExamFlow
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import reverse

from .services import telegram_auth_service

logger = logging.getLogger(__name__)


class TelegramAuthMiddleware(MiddlewareMixin):
    """
    Middleware для проверки аутентификации через Telegram
    """
    
    # URL-пути, которые не требуют аутентификации
    EXEMPT_URLS = [
        '/auth/',
        '/admin/',
        '/static/',
        '/media/',
        '/health/',
        '/api/health/',
        '/bot/',
        '/',
        '/login/',
        '/register/',
        '/success/',
        '/error/',
    ]
    
    # API endpoints, которые требуют JSON ответа при отсутствии аутентификации
    API_ENDPOINTS = [
        '/api/',
    ]
    
    def process_request(self, request):
        """
        Обрабатывает входящий запрос
        """
        # Проверяем, нужна ли аутентификация для этого URL
        if self._is_exempt_url(request.path):
            return None
        
        # Получаем токен сессии
        session_token = self._get_session_token(request)
        
        if not session_token:
            return self._handle_unauthenticated(request)
        
        # Проверяем сессию
        user = telegram_auth_service.get_user_by_session(session_token)
        
        if not user:
            return self._handle_unauthenticated(request)
        
        # Добавляем пользователя в request
        request.telegram_user = user
        request.session_token = session_token
        
        return None
    
    def _is_exempt_url(self, path):
        """
        Проверяет, освобожден ли URL от аутентификации
        """
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return True
        return False
    
    def _get_session_token(self, request):
        """
        Извлекает токен сессии из запроса
        """
        # Проверяем заголовок Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        # Проверяем GET параметр
        token = request.GET.get('token')
        if token:
            return token
        
        # Проверяем POST параметр
        token = request.POST.get('token')
        if token:
            return token
        
        return None
    
    def _handle_unauthenticated(self, request):
        """
        Обрабатывает неаутентифицированные запросы
        """
        # Для API endpoints возвращаем JSON
        if self._is_api_endpoint(request.path):
            return JsonResponse({
                'success': False,
                'message': 'Требуется аутентификация',
                'auth_required': True,
                'login_url': '/auth/telegram/login/'
            }, status=401)
        
        # Для обычных страниц перенаправляем на страницу входа
        return None  # Django будет обрабатывать это как обычно
    
    def _is_api_endpoint(self, path):
        """
        Проверяет, является ли путь API endpoint
        """
        for api_endpoint in self.API_ENDPOINTS:
            if path.startswith(api_endpoint):
                return True
        return False


def telegram_user_required(view_func):
    """
    Декоратор для проверки аутентификации пользователя
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'telegram_user') or not request.telegram_user:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False,
                    'message': 'Требуется аутентификация',
                    'auth_required': True
                }, status=401)
            else:
                from django.shortcuts import redirect
                return redirect('/auth/telegram/login/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def telegram_premium_required(view_func):
    """
    Декоратор для проверки премиум статуса пользователя
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'telegram_user') or not request.telegram_user:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False,
                    'message': 'Требуется аутентификация',
                    'auth_required': True
                }, status=401)
            else:
                from django.shortcuts import redirect
                return redirect('/auth/telegram/login/')
        
        if not request.telegram_user.is_premium:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False,
                    'message': 'Требуется премиум подписка',
                    'premium_required': True
                }, status=403)
            else:
                from django.shortcuts import redirect
                return redirect('/subscribe/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
