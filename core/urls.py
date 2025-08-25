"""
URL конфигурация для приложения core
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Система персонализации
    path('personalization/', views.personalization_dashboard, name='personalization_dashboard'),
    path('personalization/analytics/', views.my_analytics, name='my_analytics'),
    path('personalization/recommendations/', views.my_recommendations, name='my_recommendations'),
    path('personalization/study-plan/', views.study_plan_view, name='study_plan'),
    path('personalization/weak-topics/', views.weak_topics_view, name='weak_topics'),

    # API для персонализации
    path('api/personalization/insights/', views.api_user_insights, name='api_user_insights'),
    path('api/personalization/recommended-tasks/', views.api_recommended_tasks, name='api_recommended_tasks'),
    path('api/personalization/study-plan/', views.api_study_plan, name='api_study_plan'),
    path('api/personalization/weak-topics/', views.api_weak_topics, name='api_weak_topics'),
    path('api/personalization/preferences/', views.api_user_preferences, name='api_user_preferences'),
]
