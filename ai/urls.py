from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    # Основные страницы ИИ
    path('', views.ai_chat, name='dashboard'),
    path('chat/', views.ai_chat, name='chat'),
    path('explain/', views.ai_explain, name='explain'),
    path('search/', views.ai_search, name='search'),
    path('generate/', views.ai_generate, name='generate'),
    
    # API для ИИ
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/explain/', views.api_explain, name='api_explain'),
    path('api/search/', views.api_search, name='api_search'),
    path('api/generate/', views.api_generate, name='api_generate'),
    
    # Управление лимитами
    path('limits/', views.ai_limits, name='limits'),
    path('api/limits/', views.api_limits, name='api_limits'),
    
    # Голосовой помощник
    path('voice/', views.voice_assistant, name='voice'),
    path('api/voice/', views.api_voice, name='api_voice'),
    
    # Административные функции
    path('admin/providers/', views.admin_providers, name='admin_providers'),
    path('admin/templates/', views.admin_templates, name='admin_templates'),
]
