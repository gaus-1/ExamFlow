"""
Ультра-простой health check без зависимостей
"""

from django.http import JsonResponse
import time


def ultra_simple_health(request):
    """Ультра-простой health check без зависимостей"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': time.time(),
        'service': 'ExamFlow 2.0',
        'message': 'Service is running'
    })


def minimal_health_check(request):
    """Минимальный health check"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'ExamFlow 2.0',
        'version': '2.0.0'
    })
