"""
URL маршруты для AI API ExamFlow 2.0
"""

from django.urls import path
from . import views

app_name = 'ai'  # Определяем namespace

urlpatterns = [
    # AI чат (основной endpoint)
    path('chat/', views.api_chat, name='chat'),

    # AI чат (API endpoint) - основной путь для фронтенда
    path('api/', views.api_chat, name='ai_api'),
    path('api/chat/', views.api_chat, name='ai_chat_api'),

    # Управление контекстом
    path('clear-context/', views.clear_context, name='clear_context'),
]
    