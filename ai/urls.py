"""
URL маршруты для AI API ExamFlow 2.0
"""

from django.urls import path
from . import api, emergency_api

app_name = 'ai'  # Определяем namespace

urlpatterns = [
    # AI чат (основной endpoint)
    path('chat/', api.ai_chat_api, name='chat'),

    # AI чат (API endpoint) - основной путь для фронтенда
    path('api/', api.ai_chat_api, name='ai_api'),
    path('api/chat/', api.ai_chat_api, name='ai_chat_api'),

    # Задачи
    path('api/problems/', api.problems_api, name='problems_api'),

    # Профиль пользователя
    path('api/user/profile/', api.user_profile_api, name='user_profile_api'),

    # Экстренный AI API (без базы данных)
    path('emergency/', emergency_api.emergency_ai_api, name='emergency_ai_api'),
]
