"""
Представления для модуля аналитики

Предоставляет:
- Статистику по пользователям
- Анализ активности обучения
- Отчеты по эффективности
- Мониторинг системы
"""

from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import timedelta
from django.contrib.auth.models import User
from learning.models import (
    Subject, Task, UserProgress, UserRating
)
from authentication.models import Subscription

def is_staff_or_superuser(user):
    """Проверяет, является ли пользователь администратором"""
    return user.is_staff or user.is_superuser

@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    """
    Главная панель аналитики

    Показывает основные метрики системы:
    - Количество пользователей
    - Активность решения заданий
    - Популярные предметы
    - Конверсия подписок
    """
    # Общая статистика
    total_users = User.objects.count()
    total_tasks = Task.objects.count()  # type: ignore
    total_attempts = UserProgress.objects.count()  # type: ignore
    active_users_today = User.objects.filter(
        last_login__date=timezone.now().date()
    ).count()

    # Статистика по предметам
    subjects_stats = Subject.objects.annotate(  # type: ignore
        tasks_count=Count('topics__tasks'),
        attempts_count=Count('topics__tasks__userprogress')
    ).filter(tasks_count__gt=0).order_by('-attempts_count')[:10]

    # Активность за последние 7 дней
    week_ago = timezone.now() - timedelta(days=7)
    daily_activity = []
    for i in range(7):
        date = week_ago + timedelta(days=i)
        attempts = UserProgress.objects.filter(  # type: ignore
            created_at__date=date.date()
        ).count()
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'attempts': attempts
        })

    # Топ пользователи
    top_users = UserRating.objects.select_related(
        'user').order_by('-total_points')[:10]  # type: ignore

    # Статистика подписок
    subscriptions_stats = {
        'total': Subscription.objects.count(),  # type: ignore
        'active': Subscription.objects.filter(is_active=True).count(),  # type: ignore
        'expired': Subscription.objects.filter(  # type: ignore
            is_active=False,
            end_date__lt=timezone.now()
        ).count()
    }

    context = {
        'total_users': total_users,
        'total_tasks': total_tasks,
        'total_attempts': total_attempts,
        'active_users_today': active_users_today,
        'subjects_stats': subjects_stats,
        'daily_activity': daily_activity,
        'top_users': top_users,
        'subscriptions_stats': subscriptions_stats,
    }

    return render(request, 'analytics/dashboard.html', context)

@user_passes_test(is_staff_or_superuser)
def users_analytics(request):
    """
    Детальная аналитика по пользователям

    Показывает:
    - Регистрации по дням
    - Активность пользователей
    - Распределение по точности решений
    - Telegram vs Web пользователи
    """
    # Регистрации за последний месяц
    month_ago = timezone.now() - timedelta(days=30)
    registrations = []
    for i in range(30):
        date = month_ago + timedelta(days=i)
        count = User.objects.filter(
            date_joined__date=date.date()
        ).count()
        registrations.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })

    # Активность пользователей
    users_activity = User.objects.annotate(
        attempts_count=Count('userprogress'),
        correct_count=Count('userprogress', filter=Q(userprogress__is_correct=True)),
    ).filter(attempts_count__gt=0)

    # Распределение по точности
    accuracy_distribution = {
        '0-20%': 0,
        '21-40%': 0,
        '41-60%': 0,
        '61-80%': 0,
        '81-100%': 0
    }

    for user in users_activity:
        if user.attempts_count > 0:
            accuracy = (user.correct_count / user.attempts_count) * 100
            if accuracy <= 20:
                accuracy_distribution['0-20%'] += 1
            elif accuracy <= 40:
                accuracy_distribution['21-40%'] += 1
            elif accuracy <= 60:
                accuracy_distribution['41-60%'] += 1
            elif accuracy <= 80:
                accuracy_distribution['61-80%'] += 1
            else:
                accuracy_distribution['81-100%'] += 1

    # Telegram vs Web пользователи
    telegram_users = User.objects.filter(username__startswith='tg_').count()
    web_users = User.objects.exclude(username__startswith='tg_').count()

    context = {
        'registrations': registrations,
        'total_active_users': users_activity.count(),
        'accuracy_distribution': accuracy_distribution,
        'telegram_users': telegram_users,
        'web_users': web_users,
    }

    return render(request, 'analytics/users.html', context)

@user_passes_test(is_staff_or_superuser)
def tasks_analytics(request):
    """
    Аналитика по заданиям

    Показывает:
    - Самые сложные задания (низкий процент правильных ответов)
    - Популярные задания (много попыток)
    - Статистику по предметам и темам
    - Эффективность заданий
    """
    # Статистика по заданиям
    tasks_stats = Task.objects.annotate(  # type: ignore
        attempts_count=Count('userprogress'),
        correct_count=Count('userprogress', filter=Q(userprogress__is_correct=True))
    ).filter(attempts_count__gt=0)

    # Самые сложные задания (низкий процент правильных ответов)
    difficult_tasks = []
    for task in tasks_stats:
        if task.attempts_count >= 5:  # Минимум 5 попыток для статистики
            success_rate = (task.correct_count / task.attempts_count) * 100
            difficult_tasks.append({
                'task': task,
                'success_rate': round(success_rate, 1),
                'attempts': task.attempts_count
            })

    difficult_tasks = sorted(difficult_tasks, key=lambda x: x['success_rate'])[:10]

    # Популярные задания
    popular_tasks = tasks_stats.order_by('-attempts_count')[:10]

    # Статистика по предметам
    subjects_performance = []
    for subject in Subject.objects.all():  # type: ignore
        subject_attempts = UserProgress.objects.filter(  # type: ignore
            task__topic__subject=subject
        ).count()

        if subject_attempts > 0:
            subject_correct = UserProgress.objects.filter(  # type: ignore
                task__topic__subject=subject,
                is_correct=True
            ).count()

            subjects_performance.append({
                'subject': subject,
                'attempts': subject_attempts,
                'correct': subject_correct,
                'success_rate': round((subject_correct / subject_attempts) * 100, 1)
            })

    subjects_performance = sorted(
        subjects_performance,
        key=lambda x: x['attempts'],
        reverse=True)

    context = {
        'total_tasks': Task.objects.count(),  # type: ignore
        'tasks_with_attempts': tasks_stats.count(),
        'difficult_tasks': difficult_tasks,
        'popular_tasks': popular_tasks,
        'subjects_performance': subjects_performance,
    }

    return render(request, 'analytics/tasks.html', context)

def api_stats(request):
    """
    API для получения статистики в JSON формате

    Возвращает основные метрики для внешних интеграций
    """
    stats = {
        'users': {
            'total': User.objects.count(),
            'active_today': User.objects.filter(
                last_login__date=timezone.now().date()
            ).count(),
            'telegram': User.objects.filter(username__startswith='tg_').count(),
            'web': User.objects.exclude(username__startswith='tg_').count(),
        },
        'tasks': {
            'total': Task.objects.count(),  # type: ignore
            'attempts_today': UserProgress.objects.filter(  # type: ignore
                created_at__date=timezone.now().date()
            ).count(),
            'total_attempts': UserProgress.objects.count(),  # type: ignore
        },
        'subjects': {
            'total': Subject.objects.count(),  # type: ignore
            'with_tasks': Subject.objects.annotate(  # type: ignore
                tasks_count=Count('topics__tasks')
            ).filter(tasks_count__gt=0).count(),
        },
        'subscriptions': {
            'total': Subscription.objects.count(),  # type: ignore
            # type: ignore
            'active': Subscription.objects.filter(is_active=True).count(),
        }
    }

    return JsonResponse(stats)

@csrf_exempt
@require_http_methods(["POST"])
def update_user_profile(request):
    """
    API для обновления профиля пользователя

    Принимает данные о поведении пользователя для аналитики
    """
    try:
        data = json.loads(request.body)

        # Логируем данные для отладки
        print("📊 Получены данные профиля: {data}")

        # Здесь можно добавить логику сохранения данных в базу
        # Пока просто возвращаем успех

        response_data = {
            'status': 'success',
            'message': 'Профиль пользователя обновлен',
            'timestamp': timezone.now().isoformat(),
            'received_data': data
        }

        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Неверный формат JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка сервера: {str(e)}'
        }, status=500)
