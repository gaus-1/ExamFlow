"""
URL-маршруты для модуля аналитики

Определяет пути для:
- Главной панели аналитики (/analytics/)
- Аналитики пользователей (/analytics/users/)
- Аналитики заданий (/analytics/tasks/)
- API статистики (/analytics/api/stats/)
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Панели аналитики
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_analytics, name='users'),
    path('tasks/', views.tasks_analytics, name='tasks'),

    # API
    path('api/stats/', views.api_stats, name='api_stats'),
    path(
        'api/update-user-profile/',
        views.update_user_profile,
        name='update_user_profile'),
        ]
