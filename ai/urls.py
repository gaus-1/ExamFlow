"""
URL маршруты для AI API ExamFlow 2.0
"""

from django.urls import path
from . import api

app_name = 'ai'  # Определяем namespace

urlpatterns = [
    # AI чат (основной endpoint)
    path('chat/', api.ai_chat_api, name='chat'),
    
    # AI чат (API endpoint)
    path('api/chat/', api.ai_chat_api, name='ai_chat_api'),
    
    # Задачи
    path('api/problems/', api.problems_api, name='problems_api'),
    
    # Профиль пользователя
    path('api/user/profile/', api.user_profile_api, name='user_profile_api'),
]
