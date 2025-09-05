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
        
        # Быстрая проверка базы данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            response_time = time.time() - start_time
            
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'response_time': round(response_time, 3),
                'database': 'connected',
                'service': 'ExamFlow 2.0',
                'version': '2.0.0'
            })
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'error': 'Database check failed',
                'timestamp': timezone.now().isoformat()
            }, status=503)
            
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
