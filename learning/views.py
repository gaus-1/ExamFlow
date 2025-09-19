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

import time
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import logging
from learning.models import Subject, Task  # type: ignore
from core.models import UserProgress  # type: ignore
# import core.seo as seo_utils  # Модуль удален

logger = logging.getLogger(__name__)

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
    # Получаем статистику с обработкой ошибок БД
    try:
        base_qs = Subject.objects.filter(  # type: ignore
            is_archived=False, is_primary=True)  # type: ignore
        subjects_count = base_qs.count()  # type: ignore
        tasks_count = Task.objects.count()  # type: ignore
    except Exception as e:
        # Если БД недоступна, используем значения по умолчанию
        logger.warning(f"Database error in home view: {e}")
        base_qs = Subject.objects.none()  # type: ignore
        subjects_count = 0
        tasks_count = 0

    # Фокус: только математика и русский; безопасный запасной вариант
    try:
        if base_qs.exists():  # type: ignore
            math_qs = base_qs.filter(name__icontains='математ')  # type: ignore
            rus_qs = base_qs.filter(name__icontains='русск')  # type: ignore
            subjects = math_qs.union(rus_qs).order_by('name')  # type: ignore
        else:
            subjects = base_qs  # type: ignore
    except Exception as e:
        logger.warning(f"Error filtering subjects: {e}")
        subjects = base_qs  # type: ignore

    context = {
        'subjects_count': subjects_count,
        'tasks_count': tasks_count,
        'subjects': subjects,
        'timestamp': int(time.time()),
    }

    # SEO - базовые мета-теги встроены в шаблон
    return render(request, 'index_modern.html', context)

def subjects_list(request):
    """
    Отображает список всех доступных предметов

    Показывает:
    - Карточки предметов с иконками
    - Количество тем и заданий
    - Прогресс пользователя (если авторизован)
    """
    # Получаем предметы c фокусом; безопасный fallback
    try:
        subjects = Subject.objects.filter(  # type: ignore
            is_archived=False,
            is_primary=True).order_by('name')  # type: ignore
    except Exception:
        subjects = Subject.objects.all().order_by('name')  # type: ignore

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

    # Добавляем количество заданий для каждого предмета
    for subject in subjects:
        subject.task_count = Task.objects.filter(subject=subject).count()  # type: ignore
    
    ctx = {'subjects': subjects}
    return render(request, 'learning/subjects_list.html', ctx)

def subject_detail(request, subject_id):
    """
    Детальная страница предмета

    Показывает:
    - Описание предмета
    - Список тем с прогрессом
    - Статистику решенных заданий
    """
    subject = get_object_or_404(Subject, id=subject_id)
    # Получаем темы для предмета (временно пустой список)
    topics = []  # Topic.objects.filter(subject=subject)

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
            'progress_percent': round(
                1)}

        # Прогресс по темам (временно отключено)

    ctx = {
        'subject': subject,
        'topics': topics,
        'user_stats': user_stats,
    }
    # SEO мета-теги встроены в базовый шаблон
    return render(request, 'learning/subject_detail.html', ctx)

def topic_detail(request, topic_id):
    """
    Детальная страница темы (временно отключено)
    """
    # Временно перенаправляем на список предметов
    return redirect('learning:subjects_list')

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
            'is_correct': is_correct,
            'attempts': 1
        }
    )

    if not created:
        # Обновляем существующую запись
        progress.user_answer = user_answer
        progress.is_correct = is_correct
        progress.attempts += 1
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
        tasks_query = tasks_query.filter(subject=subject)

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
