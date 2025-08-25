"""
Middleware для обработки заголовков безопасности
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


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
                    policy_parts.append(f"{feature}=({', '.join(origins)})")
                else:
                    policy_parts.append(f"{feature}=()")
            
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
                f"[SECURITY] Подозрительный запрос: {request.method} {request.path} "
                f"от IP {self._get_client_ip(request)}"
            )
        
        return response
    
    def _get_client_ip(self, request):
        """Получает реальный IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
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
            threshold = settings.SECURITY_MONITORING.get('suspicious_ip_threshold', 10)
            # Здесь можно добавить логику подсчета запросов по IP
        
        return False
