"""
Минимальный health check для Render
"""

from django.http import JsonResponse
import time


def minimal_health_check(request):
    """Минимальный health check без зависимостей"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': time.time(),
        'service': 'ExamFlow 2.0'
    })


def ultra_simple_health(request):
    """Ультра-простой health check"""
    return JsonResponse({'ok': True})
