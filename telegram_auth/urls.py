"""
URL маршруты для Telegram аутентификации ExamFlow
"""

from django.urls import path
from . import views

app_name = 'telegram_auth'

urlpatterns = [
    # Telegram Login Widget
    path('telegram/login/', views.telegram_login_widget, name='telegram_login'),
    path('telegram/callback/', views.telegram_auth_callback, name='telegram_callback'),

    # Страницы результатов
    path('success/', views.auth_success, name='auth_success'),
    path('error/', views.auth_error, name='auth_error'),

    # API для аутентификации
    path('api/', views.TelegramAuthAPI.as_view(), name='api_auth'),
    path('api/status/', views.telegram_auth_status, name='api_status'),
]
