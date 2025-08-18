from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from core.views import home, subject_list, subject_detail, topic_detail, task_detail, user_profile, user_progress, search_tasks, weak_spots
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
from bot.tasks import start_bot_view, restart_bot_view, stop_bot_view, bot_status_view
from bot.views import bot_control_panel, bot_api_status, telegram_webhook

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Главная
    path('', home, name='home'),

    # Основные страницы
    path('subjects/', subject_list, name='subjects'),
    path('subjects/<int:subject_id>/', subject_detail, name='subject_detail'),
    path('topics/<int:topic_id>/', topic_detail, name='topic_detail'),
    path('tasks/<int:task_id>/', task_detail, name='task_detail'),
    path('weak/', weak_spots, name='weak_spots'),
    path('search/', search_tasks, name='search_tasks'),

    # Пользователь
    path('profile/', user_profile, name='profile'),
    path('progress/', user_progress, name='user_progress'),

    # Бот
    path('bot/', bot_control_panel, name='bot_control'),
    path('bot/api/status/', bot_api_status, name='bot_api_status'),
    path('bot/start/', start_bot_view, name='start_bot'),
    path('bot/restart/', restart_bot_view, name='restart_bot'),
    path('bot/stop/', stop_bot_view, name='stop_bot'),
    path('bot/status/', bot_status_view, name='bot_status'),
    path('bot/webhook/', telegram_webhook, name='telegram_webhook'),

    # API
    path('api/', include([
        path('tasks/random/', get_random_task, name='api_random_task'),
        path('tasks/<int:task_id>/', get_task_by_id, name='api_task_by_id'),
        path('tasks/search/', api_search_tasks, name='api_search_tasks'),
        path('subjects/', get_subjects, name='api_subjects'),
        path('subjects/<int:subject_id>/tasks/', get_tasks_by_subject, name='api_tasks_by_subject'),
        path('topics/', get_topics, name='api_topics'),
        path('statistics/', get_statistics, name='api_statistics'),
        path('billing/create-subscription/', create_subscription, name='api_create_subscription'),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)