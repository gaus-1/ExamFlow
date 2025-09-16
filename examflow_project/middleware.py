"""
Middleware для обработки заголовков безопасности и ошибок базы данных
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class DatabaseErrorMiddleware(MiddlewareMixin):
    """
    Middleware для обработки ошибок базы данных
    """

    def process_exception(self, request, exception):
        """Обрабатывает исключения базы данных"""
        if isinstance(exception, OperationalError):
            logger.error("Database error: {exception}")
            # Закрываем проблемное соединение
            try:
                connection.close()
            except Exception:
                pass

            # Возвращаем простую страницу без обращения к БД
            if request.path == '/':
                return JsonResponse({
                    'error': 'Database temporarily unavailable',
                    'message': 'Пожалуйста, попробуйте позже'
                }, status=503)

        return None

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления дополнительных заголовков безопасности
    """

    def process_response(self, request, response):
        """Добавляет заголовки безопасности к ответу"""

        # Permissions-Policy
        if hasattr(settings, 'PERMISSIONS_POLICY'):
            policy_parts = []
            for feature, origins in settings.PERMISSIONS_POLICY.items():
                if origins:
                    policy_parts.append("{feature}=({', '.join(origins)})")
                else:
                    policy_parts.append("{feature}=()")

            if policy_parts:
                response['Permissions-Policy'] = ', '.join(policy_parts)

        # Cross-Origin Opener Policy
        if hasattr(settings, 'SECURE_CROSS_ORIGIN_OPENER_POLICY'):
            response['Cross-Origin-Opener-Policy'] = settings.SECURE_CROSS_ORIGIN_OPENER_POLICY

        # Cross-Origin Embedder Policy
        if hasattr(settings, 'SECURE_CROSS_ORIGIN_EMBEDDER_POLICY'):
            response['Cross-Origin-Embedder-Policy'] = settings.SECURE_CROSS_ORIGIN_EMBEDDER_POLICY

        # Дополнительные заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'

        # Логирование подозрительной активности
        if self._is_suspicious_request(request):
            logger.warning(
                "[SECURITY] Подозрительный запрос: {request.method} {request.path} "
                "от IP {self._get_client_ip(request)}"
            )

        return response

    def _get_client_ip(self, request):
        """Получает реальный IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(', ')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _is_suspicious_request(self, request):
        """Проверяет, является ли запрос подозрительным"""
        suspicious_patterns = [
            '/admin/', '/wp-admin/', '/phpmyadmin/', '/mysql/',
            'union select', 'script>', 'javascript:', 'eval(',
            'document.cookie', 'onload=', 'onerror='
        ]

        path = request.path.lower()
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

        # Проверяем подозрительные пути
        for pattern in suspicious_patterns:
            if pattern in path or pattern in user_agent:
                return True

        # Проверяем количество запросов с одного IP
        if hasattr(settings, 'SECURITY_MONITORING'):
            _threshold = settings.SECURITY_MONITORING.get('suspicious_ip_threshold', 10)
            # Здесь можно добавить логику подсчета запросов по IP

        return False
