"""
URL маршруты для системы персонализации
"""

from django.urls import path
from . import api

urlpatterns = [
    path('api/personalization/', api.personalization_api, name='personalization_api'),
    path('api/learning-path/', api.learning_path_api, name='learning_path_api'),
        ]
