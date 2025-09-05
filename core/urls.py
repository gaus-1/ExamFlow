"""
URL-маршруты для core приложения
"""

from django.urls import path
from . import api
from .minimal_health import minimal_health_check, ultra_simple_health

urlpatterns = [
    # API для RAG-системы
    path('api/ai/query/', api.AIQueryView.as_view(), name='ai_query'),
    path('api/ai/search/', api.SearchView.as_view(), name='ai_search'),
    path('api/ai/stats/', api.VectorStoreStatsView.as_view(), name='vector_stats'),
    path('api/health/', api.HealthCheckView.as_view(), name='health_check'),
    
    # Health check endpoints (минимальные для Render)
    path('health/', ultra_simple_health, name='health_check_basic'),
    path('health/simple/', minimal_health_check, name='health_check_simple'),
]
