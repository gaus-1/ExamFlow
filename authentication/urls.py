"""
URL маршруты для модуля аутентификации ExamFlow 2.0
"""

from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Упрощенная авторизация
    path('login/', views.simple_login, name='simple_login'),  # type: ignore

    # OAuth авторизация
    path('telegram/', views.telegram_login, name='telegram_login'),  # type: ignore
    path('google/', views.google_login, name='google_login'),  # type: ignore
    path('yandex/', views.yandex_login, name='yandex_login'),  # type: ignore

    # Callback'и OAuth
    path(
        'telegram/callback/',
        views.telegram_callback,
        name='telegram_callback'),
    # type: ignore
    path(
        'google/callback/',
        views.google_callback,
        name='google_callback'),
    # type: ignore
    path(
        'yandex/callback/',
        views.yandex_callback,
        name='yandex_callback'),
    # type: ignore

    # Выход
    path('logout/', views.logout_view, name='logout'),  # type: ignore

    # Гостевой доступ
    path('guest/', views.guest_access, name='guest_access'),  # type: ignore
]
