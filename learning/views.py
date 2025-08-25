"""
Представления для модуля обучения

Обрабатывает:
- Главную страницу
- Просмотр списка предметов
- Детальный просмотр предмета
- Просмотр тем предмета
- Решение заданий
- Отображение прогресса
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Subject, Topic, Task, UserProgress
import random


def home(request):
    """
    Главная страница ExamFlow
    
    Показывает:
    - Hero секцию с описанием платформы
    - Статистику предметов и заданий
    - QR-код для Telegram бота
    - Преимущества платформы
    - Тарифные планы
    - Блок персонализации (для авторизованных)
    """
    # Получаем статистику
    subjects_count = Subject.objects.count()  # type: ignore
    tasks_count = Task.objects.count()  # type: ignore
    
    # Получаем предметы для отображения (без сложных запросов)
    subjects = Subject.objects.all()[:8] # type: ignore
    
    context = {
        'subjects_count': subjects_count,
        'tasks_count': tasks_count,
        'subjects': subjects,
    }
    
    return render(request, 'home.html', context)


def subjects_list(request):
    """
    Отображает список всех доступных предметов
    
    Показывает:
    - Карточки предметов с иконками
    - Количество тем и заданий
    - Прогресс пользователя (если авторизован)
    """
    # Получаем все предметы (без сложных запросов)
    subjects = Subject.objects.all()  # type: ignore
    
    # Добавляем прогресс для авторизованных пользователей
    if request.user.is_authenticated:
        for subject in subjects:
            # Считаем решенные задания для предмета
            solved_tasks = UserProgress.objects.filter(  # type: ignore
                user=request.user,
                task__subject=subject,
                is_correct=True
            ).count()
            subject.user_progress = solved_tasks
    
    return render(request, 'learning/subjects_list.html', {
        'subjects': subjects
    })


def subject_detail(request, subject_id):
    """
    Детальная страница предмета
    
    Показывает:
    - Описание предмета
    - Список тем с прогрессом
    - Статистику решенных заданий
    """
    subject = get_object_or_404(Subject, id=subject_id)
    # Получаем темы для предмета
    topics = Topic.objects.filter(subject=subject)  # type: ignore
    
    # Статистика для авторизованных пользователей
    user_stats = {}
    if request.user.is_authenticated:
        total_tasks = Task.objects.filter(subject=subject).count()  # type: ignore
        solved_tasks = UserProgress.objects.filter(  # type: ignore
            user=request.user,
            task__subject=subject,
            is_correct=True
        ).count()
        
        user_stats = {
            'total_tasks': total_tasks,
            'solved_tasks': solved_tasks,
            'progress_percent': round((solved_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        }
        
        # Прогресс по темам
        for topic in topics:
            topic_solved = UserProgress.objects.filter(  # type: ignore
                user=request.user,
                task__topic=topic,
                is_correct=True
            ).count()
            topic.user_progress = topic_solved
    
    return render(request, 'learning/subject_detail.html', {
        'subject': subject,
        'topics': topics,
        'user_stats': user_stats
    })


def topic_detail(request, topic_id):
    """
    Детальная страница темы
    
    Показывает:
    - Описание темы
    - Список заданий с пагинацией
    - Возможность решать задания
    """
    topic = get_object_or_404(Topic, id=topic_id)
    tasks_list = Task.objects.filter(topic=topic).order_by('id')  # type: ignore
    
    # Пагинация заданий
    paginator = Paginator(tasks_list, 10)  # 10 заданий на страницу
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    # Отмечаем решенные задания для авторизованных пользователей
    if request.user.is_authenticated:
        solved_task_ids = UserProgress.objects.filter(  # type: ignore
            user=request.user,
            task__in=tasks,
            is_correct=True
        ).values_list('task_id', flat=True)
        
        for task in tasks:
            task.is_solved = task.id in solved_task_ids
    
    return render(request, 'learning/topic_detail.html', {
        'topic': topic,
        'tasks': tasks
    })


def task_detail(request, task_id):
    """
    Детальная страница задания
    
    Позволяет:
    - Просматривать условие задания
    - Вводить ответ
    - Получать результат проверки
    - Просматривать объяснение
    """
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем, решал ли пользователь это задание
    user_progress = None
    if request.user.is_authenticated:
        user_progress = UserProgress.objects.filter(  # type: ignore
            user=request.user,
            task=task
        ).first()
    
    return render(request, 'learning/task_detail.html', {
        'task': task,
        'user_progress': user_progress
    })


@login_required
def solve_task(request, task_id):
    """
    AJAX-обработчик для решения задания
    
    Принимает ответ пользователя и возвращает результат проверки
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    task = get_object_or_404(Task, id=task_id)
    user_answer = request.POST.get('answer', '').strip()
    
    if not user_answer:
        return JsonResponse({'error': 'Ответ не может быть пустым'}, status=400)
    
    # Проверяем правильность ответа
    is_correct = task.check_answer(user_answer)
    
    # Сохраняем прогресс пользователя
    progress, created = UserProgress.objects.get_or_create(  # type: ignore
        user=request.user,
        task=task,
        defaults={
            'user_answer': user_answer,
            'is_correct': is_correct
        }
    )
    
    if not created:
        # Обновляем существующую запись
        progress.user_answer = user_answer
        progress.is_correct = is_correct
        progress.save()
    
    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': task.answer,
        'explanation': task.explanation or 'Объяснение пока не добавлено.',
        'message': 'Правильно! 🎉' if is_correct else 'Неправильно. Попробуйте еще раз! 🤔'
    })


def random_task(request, subject_id=None):
    """
    Показывает случайное задание
    
    Если указан subject_id, выбирает задание из этого предмета
    Иначе выбирает из всех доступных заданий
    """
    tasks_query = Task.objects.all()  # type: ignore    
    
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        tasks_query = tasks_query.filter(topic__subject=subject)
    
    # Исключаем уже решенные задания для авторизованных пользователей
    if request.user.is_authenticated:
        solved_task_ids = UserProgress.objects.filter(  # type: ignore
            user=request.user,
            is_correct=True
        ).values_list('task_id', flat=True)
        tasks_query = tasks_query.exclude(id__in=solved_task_ids)
    
    tasks_list = list(tasks_query)
    
    if not tasks_list:
        messages.warning(request, 'Все доступные задания уже решены!')
        return redirect('learning:subjects_list')
    
    random_task = random.choice(tasks_list)
    return redirect('learning:task_detail', task_id=random_task.id)
