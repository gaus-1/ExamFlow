from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponse
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap, RootViewSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Импорты из legacy модулей (для обратной совместимости)
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


    # Модуль обучения
    path('', include('learning.urls')),  # Основные маршруты для обучения

    # Модуль Telegram бота
    path('bot/', include('telegram_bot.urls')),

    # Модуль Telegram аутентификации
    path('auth/', include('telegram_auth.urls')),

    # Модуль аналитики
    path('analytics/', include('analytics.urls')),

    # Модуль управления дизайнами
    path('themes/', include('themes.urls')),

    # Модуль ИИ-ассистента
    path('ai/', include('ai.urls')),

    # Telegram Web App
    path('webapp/', include('telegram_bot.webapp_urls')),

    # Модуль core (персонализация и RAG-система)
    path('core/', include('core.urls')),
    
    # AI API маршруты на корневом уровне для фронтенда
    path('', include('core.urls')),  # Добавляем core URLs на корень для AI API

    # Health check endpoints (для Render и мониторинга)
    path('healthz', lambda request: JsonResponse({'status': 'ok'})),

    # Модуль персонализации
    path('personalization/', include('core.personalization.urls')),

    # ==========================================
    # LEGACY МАРШРУТЫ (для обратной совместимости)
    # ==========================================


    # API
    path('api/tasks/random/', get_random_task, name='api_random_task'),
    path('api/tasks/<int:task_id>/', get_task_by_id, name='api_task_by_id'),
    path('api/tasks/search/', api_search_tasks, name='api_search_tasks'),
    path('api/subjects/', get_subjects, name='api_subjects'),
    path('api/subjects/<int:subject_id>/tasks/', get_tasks_by_subject, name='api_tasks_by_subject'),
    path('api/topics/', get_topics, name='api_topics'),
    path('api/statistics/', get_statistics, name='api_statistics'),
    path('api/billing/create-subscription/', create_subscription, name='api_create_subscription'),

    # Административные функции (БЕСПЛАТНЫЙ способ запуска парсинга)
    path('admin/parsing/', trigger_parsing, name='admin_trigger_parsing'),
    path('admin/start-parsing/', start_parsing, name='admin_start_parsing'),
    path('admin/parsing-status/', parsing_status, name='admin_parsing_status'),

    # Тестирование тем
    path('test-themes/', lambda request: render(request, 'test_themes.html'), name='test_themes'),

    # Демонстрация стилей
    path('style-showcase/', lambda request: render(request, 'style-showcase.html'), name='style_showcase'),
    path('aesop-showcase/', lambda request: render(request, 'aesop-showcase.html'), name='aesop_showcase'),

    # Новые страницы
    path('features/', lambda request: render(request, 'features.html'), name='features'),
    path('pricing/', lambda request: render(request, 'pricing.html'), name='pricing'),
    path('subscribe/', lambda request: render(request, 'subscribe.html'), name='subscribe'),
    # Sitemap.xml
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': {'static': StaticViewSitemap, 'root': RootViewSitemap}},
        name='django.contrib.sitemaps.views.sitemap'
    ),
    # robots.txt (минимально достаточный)
    path(
        'robots.txt',
        lambda r: HttpResponse(
            b"User-agent: *\nAllow: /\nSitemap: https://examflow.ru/sitemap.xml\n",  # type: ignore
            content_type='text/plain'
        )
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
