"""
Health check views for ExamFlow
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health_check_view(request):
    """
    Comprehensive health check endpoint
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache connection
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check') == 'ok'
        
        status = {
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected' if cache_status else 'error',
            'timestamp': str(datetime.now())
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def simple_health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({'status': 'ok'})
