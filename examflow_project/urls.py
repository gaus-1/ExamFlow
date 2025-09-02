from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Импорты из legacy модулей (для обратной совместимости)
from core.auth_views import (
    register_view, login_view, logout_view, dashboard_view,
    profile_view, subscribe_view, achievements_view, telegram_auth
)
from core.admin_views import trigger_parsing, start_parsing, parsing_status
from core.api import (
    get_random_task,
    get_subjects,
    get_tasks_by_subject,
    get_task_by_id,
    search_tasks as api_search_tasks,
    get_topics,
    get_statistics,
    create_subscription,
)
# Убираем legacy импорты бота - теперь используется модульный telegram_bot

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # ==========================================
    # НОВЫЕ МОДУЛЬНЫЕ ПРИЛОЖЕНИЯ
    # ==========================================
    
    # Модуль аутентификации
    path('auth/', include('authentication.urls')),
    
    # Модуль обучения
    path('', include('learning.urls')),  # Основные маршруты для обучения
    
    # Модуль Telegram бота
    path('bot/', include('telegram_bot.urls')),
    
    # Модуль аналитики
    path('analytics/', include('analytics.urls')),
    
    # Модуль управления дизайнами
    path('themes/', include('themes.urls')),
    
    # Модуль ИИ-ассистента
    path('ai/', include('ai.urls')),
    
    # Модуль core (персонализация и RAG-система)
    path('core/', include('core.urls')),
    
    # ==========================================
    # LEGACY МАРШРУТЫ (для обратной совместимости)
    # ==========================================

    # Аутентификация (legacy)
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('achievements/', achievements_view, name='achievements'),
    path('subscribe/', subscribe_view, name='subscribe'),

    # API
    path('api/tasks/random/', get_random_task, name='api_random_task'),
    path('api/tasks/<int:task_id>/', get_task_by_id, name='api_task_by_id'),
    path('api/tasks/search/', api_search_tasks, name='api_search_tasks'),
    path('api/subjects/', get_subjects, name='api_subjects'),
    path('api/subjects/<int:subject_id>/tasks/', get_tasks_by_subject, name='api_tasks_by_subject'),
    path('api/topics/', get_topics, name='api_topics'),
    path('api/statistics/', get_statistics, name='api_statistics'),
    path('api/billing/create-subscription/', create_subscription, name='api_create_subscription'),
    path('api/auth/telegram/', telegram_auth, name='api_telegram_auth'),
    
    # Административные функции (БЕСПЛАТНЫЙ способ запуска парсинга)
    path('admin/parsing/', trigger_parsing, name='admin_trigger_parsing'),
    path('admin/start-parsing/', start_parsing, name='admin_start_parsing'),
    path('admin/parsing-status/', parsing_status, name='admin_parsing_status'),
    
    # Тестирование тем
    path('test-themes/', lambda request: render(request, 'test_themes.html'), name='test_themes'),
    
    # Демонстрация стилей
    path('style-showcase/', lambda request: render(request, 'style-showcase.html'), name='style_showcase'),
    path('aesop-showcase/', lambda request: render(request, 'aesop-showcase.html'), name='aesop_showcase'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)