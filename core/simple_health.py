"""
Упрощенный health check для Render без внешних зависимостей
"""

import time
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


def simple_health_check(request):
    """Простой health check для Render без внешних зависимостей"""
    try:
        start_time = time.time()
        response_time = time.time() - start_time
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'response_time': round(response_time, 3),
            'service': 'ExamFlow 2.0',
            'version': '2.0.0',
            'message': 'Service is running'
        })
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)


def basic_health_check(request):
    """Базовый health check только для проверки доступности"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'ExamFlow 2.0'
    })
