"""
URL-маршруты для премиум-функций
"""

from django.urls import path
from . import api

app_name = 'premium'

urlpatterns = [
    # Статус и функции
    path('status/', api.get_premium_status, name='premium_status'),
    path('features/', api.get_premium_features, name='premium_features'),

    # Отслеживание использования
    path('usage/track/', api.track_usage, name='track_usage'),
    path('usage/stats/', api.get_usage_stats, name='usage_stats'),

    # Премиум-функции
    path('export/pdf/', api.export_to_pdf, name='export_pd'),
    path('search/advanced/', api.advanced_search, name='advanced_search'),
    path(
        'recommendations/',
        api.get_personalized_recommendations,
        name='recommendations'),
    path('compare/versions/', api.compare_versions, name='compare_versions'),
        ]
