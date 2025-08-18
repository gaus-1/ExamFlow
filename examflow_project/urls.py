from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, subject_list, subject_detail, task_detail
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
from bot.views import bot_control_panel, bot_api_status, telegram_webhook

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Главная
    path('', home, name='home'),

    # Основные страницы
    path('subjects/', subject_list, name='subjects'),
    path('subjects/<int:subject_id>/', subject_detail, name='subject_detail'),
    path('tasks/<int:task_id>/', task_detail, name='task_detail'),

    # Аутентификация
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('achievements/', achievements_view, name='achievements'),
    path('subscribe/', subscribe_view, name='subscribe'),

    # Бот
    path('bot/', bot_control_panel, name='bot_control'),
    path('bot/api/status/', bot_api_status, name='bot_api_status'),
    path('bot/webhook/', telegram_webhook, name='telegram_webhook'),

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
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)