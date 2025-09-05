"""
URL-маршруты для core приложения
"""

from django.urls import path
from . import api
from .simple_health import simple_health_check, basic_health_check

urlpatterns = [
    # API для RAG-системы
    path('api/ai/query/', api.AIQueryView.as_view(), name='ai_query'),
    path('api/ai/search/', api.SearchView.as_view(), name='ai_search'),
    path('api/ai/stats/', api.VectorStoreStatsView.as_view(), name='vector_stats'),
    path('api/health/', api.HealthCheckView.as_view(), name='health_check'),
    
    # Health check endpoints (упрощенные для Render)
    path('health/', basic_health_check, name='health_check_basic'),
    path('health/simple/', simple_health_check, name='health_check_simple'),
]
