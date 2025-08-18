"""
URL-маршруты для модуля аутентификации

Определяет пути для:
- Регистрации (/auth/register/)
- Входа (/auth/login/)
- Выхода (/auth/logout/)
- Личного кабинета (/dashboard/)
- Обновления профиля (/profile/update/)
"""

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Регистрация и вход
    path('register/', views.register_view, name='register'),
    path('login/', views.TechLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Личный кабинет
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
]
