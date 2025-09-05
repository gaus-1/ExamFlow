"""
URL-маршруты для модуля обучения

Определяет пути для:
- Главной страницы (/)
- Списка предметов (/subjects/)
- Детального просмотра предмета (/subject/<id>/)
- Детального просмотра темы (/topic/<id>/)
- Детального просмотра задания (/task/<id>/)
- Решения заданий (/task/<id>/solve/)
- Случайного задания (/random/ или /random/<subject_id>/)
"""

from django.urls import path
from . import views
from . import focused_views

app_name = 'learning'

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # Предметы (фокусированные на математике и русском)
    path('subjects/', focused_views.focused_subjects_list, name='subjects_list'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    
    # Специализированные страницы предметов
    path('math/<int:subject_id>/', focused_views.math_subject_detail, name='math_subject_detail'),
    path('russian/<int:subject_id>/', focused_views.russian_subject_detail, name='russian_subject_detail'),

    # Темы
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),

    # Задания
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/solve/', views.solve_task, name='solve_task'),

    # Случайные задания
    path('random/', views.random_task, name='random_task'),
    path('random/<int:subject_id>/', views.random_task, name='random_task_subject'),
    
    # Фокусированный поиск
    path('search/', focused_views.focused_search, name='focused_search'),
    path('api/subject-stats/', focused_views.get_subject_statistics, name='subject_statistics'),
]
