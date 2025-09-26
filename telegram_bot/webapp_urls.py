"""
URL конфигурация для Telegram Web App
"""

from django.urls import path

from . import webapp_views

app_name = "telegram_webapp"

urlpatterns = [
    path("", webapp_views.webapp_home, name="home"),
    path("subjects/", webapp_views.webapp_subjects, name="subjects"),
    path("ai-chat/", webapp_views.webapp_ai_chat, name="ai_chat"),
    path("stats/", webapp_views.webapp_stats, name="stats"),
    path("api/ask/", webapp_views.webapp_ai_api, name="ai_api"),
]
