"""
Фокусированные представления для математики и русского языка
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Subject, Task, Topic

def focused_subjects_list(request):
    """Список предметов с фокусом на математике и русском языке"""
    # Получаем только основные предметы (не архивированные)
    subjects = Subject.objects.filter(
        is_archived=False,
        is_primary=True
    ).order_by('name')

    # Группируем по типам
    math_subjects = subjects.filter(name__icontains='математика')
    russian_subjects = subjects.filter(name__icontains='русский')

    context = {
        'math_subjects': math_subjects,
        'russian_subjects': russian_subjects,
        'total_subjects': subjects.count(),
        'focus_message': 'Специализируемся на математике и русском языке'
    }

    return render(request, 'learning/focused_subjects.html', context)

def math_subject_detail(request, subject_id):
    """Детальная страница предмета математики"""
    try:
        subject = Subject.objects.get(id=subject_id, name__icontains='математика')

        # Получаем темы по математике
        topics = Topic.objects.filter(subject=subject).order_by('name')

        # Статистика
        total_tasks = Task.objects.filter(subject=subject).count()
        completed_tasks = 0  # TODO: реализовать подсчет выполненных задач

        context = {
            'subject': subject,
            'topics': topics,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'subject_type': 'math'
        }

        return render(request, 'learning/math_subject_detail.html', context)

    except Subject.DoesNotExist:
        return render(request, 'learning/subject_not_found.html', {
            'message': 'Предмет математики не найден'
        })

def russian_subject_detail(request, subject_id):
    """Детальная страница предмета русского языка"""
    try:
        subject = Subject.objects.get(id=subject_id, name__icontains='русский')

        # Получаем темы по русскому языку
        topics = Topic.objects.filter(subject=subject).order_by('name')

        # Статистика
        total_tasks = Task.objects.filter(subject=subject).count()
        completed_tasks = 0  # TODO: реализовать подсчет выполненных задач

        context = {
            'subject': subject,
            'topics': topics,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'subject_type': 'russian'
        }

        return render(request, 'learning/russian_subject_detail.html', context)

    except Subject.DoesNotExist:
        return render(request, 'learning/subject_not_found.html', {
            'message': 'Предмет русского языка не найден'
        })

def focused_search(request):
    """Поиск с фокусом на математике и русском языке"""
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'results': [], 'message': 'Введите поисковый запрос'})

    # Поиск только по основным предметам
    math_tasks = Task.objects.filter(
        subject__name__icontains='математика',
        subject__is_archived=False,
        subject__is_primary=True
    ).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )[:10]

    russian_tasks = Task.objects.filter(
        subject__name__icontains='русский',
        subject__is_archived=False,
        subject__is_primary=True
    ).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )[:10]

    results = []

    # Добавляем результаты по математике
    for task in math_tasks:
        results.append({
            'id': task.id,
            'title': task.title,
            'subject': task.subject.name,
            'type': 'math',
            'url': '/task/{task.id}/'
        })

    # Добавляем результаты по русскому языку
    for task in russian_tasks:
        results.append({
            'id': task.id,
            'title': task.title,
            'subject': task.subject.name,
            'type': 'russian',
            'url': '/task/{task.id}/'
        })

    return JsonResponse({
        'results': results,
        'total': len(results),
        'focus_message': 'Поиск сфокусирован на математике и русском языке'
    })

def get_subject_statistics(request):
    """Статистика по предметам"""
    math_subjects = Subject.objects.filter(
        name__icontains='математика',
        is_archived=False,
        is_primary=True
    )

    russian_subjects = Subject.objects.filter(
        name__icontains='русский',
        is_archived=False,
        is_primary=True
    )

    stats = {
        'math': {
            'subjects_count': math_subjects.count(),
            'total_tasks': sum(subject.task_count for subject in math_subjects),
            'subjects': [
                    'name': subject.name,
                    'tasks': subject.task_count,
                    'exam_type': subject.get_exam_type_display()
                }
                for subject in math_subjects
            ]
        },
        'russian': {
            'subjects_count': russian_subjects.count(),
            'total_tasks': sum(subject.task_count for subject in russian_subjects),
            'subjects': [
                    'name': subject.name,
                    'tasks': subject.task_count,
                    'exam_type': subject.get_exam_type_display()
                }
                for subject in russian_subjects
            ]
        }
    }

    return JsonResponse(stats)
