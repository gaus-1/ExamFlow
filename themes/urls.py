from django.urls import path
from . import views

app_name = 'themes'

urlpatterns = [
    # Тестовая страница для проверки дизайнов
    path('test/', views.test_themes, name='test_themes'),

    # API для переключения дизайнов
    path('api/switch/', views.switch_theme, name='switch_theme'),
    path('api/current/', views.get_current_theme, name='get_current_theme'),
    path('api/preview/<str:theme>/', views.preview_theme, name='preview_theme'),
        ]
