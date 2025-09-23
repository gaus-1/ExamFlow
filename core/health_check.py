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
        
        database_status = 'connected'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = 'error'
    
    try:
        # Check cache connection
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check') == 'ok'
        cache_status_text = 'connected' if cache_status else 'error'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        cache_status_text = 'error'
    
    # Determine overall status
    overall_status = 'healthy' if database_status == 'connected' else 'unhealthy'
    
    status = {
        'status': overall_status,
        'database': database_status,
        'cache': cache_status_text,
        'timestamp': str(datetime.now())
    }
    
    return JsonResponse(status, status=200)


@require_http_methods(["GET"])
@csrf_exempt
def simple_health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({'status': 'ok'}, status=200)
