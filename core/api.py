from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
from .models import Subject, Task


def _serialize_task(task: Task) -> dict:
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description or '',
        'difficulty': task.difficulty,
        'subject_id': task.subject_id,
    }


@require_GET
def get_random_task(request):
    task = Task.objects.order_by('?').first()
    if not task:
        return JsonResponse({'ok': False, 'error': 'no_tasks'}, status=404)
    return JsonResponse({'ok': True, 'task': _serialize_task(task)})


@require_GET
def get_subjects(request):
    items = list(Subject.objects.values('id', 'name', 'exam_type'))
    return JsonResponse({'ok': True, 'subjects': items})


@require_GET
def get_tasks_by_subject(request, subject_id: int):
    qs = Task.objects.filter(subject_id=subject_id).order_by('-created_at', '-id')
    tasks = [_serialize_task(t) for t in qs[:100]]
    return JsonResponse({'ok': True, 'tasks': tasks, 'count': qs.count()})


@require_GET
def get_task_by_id(request, task_id: int):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not_found'}, status=404)
    return JsonResponse({'ok': True, 'task': _serialize_task(task)})


@require_GET
def search_tasks(request):
    q = request.GET.get('q', '').strip()
    qs = Task.objects.all()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    tasks = [_serialize_task(t) for t in qs.order_by('-created_at', '-id')[:100]]
    return JsonResponse({'ok': True, 'tasks': tasks})


@require_GET
def get_topics(request):
    # Базовая заглушка: в минимальной модели тем может не быть
    return JsonResponse({'ok': True, 'topics': []})


@require_GET
def get_statistics(request):
    return JsonResponse({
        'ok': True,
        'subjects': Subject.objects.count(),
        'tasks': Task.objects.count(),
    })


@require_POST
def create_subscription(request):
    # Заглушка под платёж
    return JsonResponse({'ok': True, 'status': 'pending_admin_approval'})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from .models import Task, Subject, Topic, UserProgress, UserProfile
from .utils import get_difficulty_color, get_difficulty_icon, format_time_spent
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
from django.conf import settings
from .models import Subscription
import hmac, hashlib

@csrf_exempt
@require_http_methods(["GET"])
def get_random_task(request):
    """API для получения случайного задания"""
    try:
        # Получаем параметры фильтрации
        subject_id = request.GET.get('subject')
        difficulty = request.GET.get('difficulty')
        topic_id = request.GET.get('topic')
        
        # Базовый запрос
        tasks = Task.objects.filter(is_active=True).select_related('subject', 'topic')
        
        # Применяем фильтры
        if subject_id:
            tasks = tasks.filter(subject_id=subject_id)
        if difficulty:
            tasks = tasks.filter(difficulty=difficulty)
        if topic_id:
            tasks = tasks.filter(topic_id=topic_id)
        
        # Получаем случайное задание
        task = tasks.order_by('?').first()
        
        if task:
            data = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'difficulty': task.difficulty,
                'difficulty_display': task.get_difficulty_display(),
                'difficulty_color': get_difficulty_color(task.difficulty),
                'difficulty_icon': get_difficulty_icon(task.difficulty),
                'subject': {
                    'id': task.subject.id,
                    'name': task.subject.name,
                    'code': task.subject.code,
                    'exam_type': task.subject.exam_type
                },
                'topic': {
                    'id': task.topic.id,
                    'name': task.topic.name,
                    'code': task.topic.code
                } if task.topic else None,
                'source': task.source,
                'year': task.year,
                'tags': task.tags.split(',') if task.tags else [],
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
            
            return JsonResponse({
                'status': 'success',
                'data': data,
                'message': 'Задание успешно получено'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Задания не найдены по указанным критериям'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении задания: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_subjects(request):
    """API для получения списка предметов"""
    try:
        # Получаем параметры
        exam_type = request.GET.get('exam_type')
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        
        # Базовый запрос
        subjects = Subject.objects.all()
        
        # Применяем фильтры
        if exam_type:
            subjects = subjects.filter(exam_type=exam_type)
        if active_only:
            subjects = subjects.filter(is_active=True)
        
        # Аннотируем количество заданий и тем
        subjects = subjects.annotate(
            task_count=Count('tasks', filter=Q(tasks__is_active=True)),
            topic_count=Count('topics', filter=Q(topics__is_active=True))
        ).order_by('name')
        
        data = []
        for subject in subjects:
            data.append({
                'id': subject.id,
                'name': subject.name,
                'code': subject.code,
                'exam_type': subject.exam_type,
                'exam_type_display': subject.get_exam_type_display(),
                'description': subject.description,
                'is_active': subject.is_active,
                'task_count': subject.task_count,
                'topic_count': subject.topic_count
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'message': 'Предметы успешно получены'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении предметов: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_tasks_by_subject(request, subject_id):
    """API для получения заданий по предмету"""
    try:
        # Получаем параметры
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)  # Максимум 100
        difficulty = request.GET.get('difficulty')
        topic_id = request.GET.get('topic')
        sort_by = request.GET.get('sort', '-created_at')
        
        # Проверяем существование предмета
        try:
            subject = Subject.objects.get(id=subject_id, is_active=True)
        except Subject.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Предмет не найден'
            }, status=404)
        
        # Базовый запрос
        tasks = subject.tasks.filter(is_active=True).select_related('topic')
        
        # Применяем фильтры
        if difficulty:
            tasks = tasks.filter(difficulty=difficulty)
        if topic_id:
            tasks = tasks.filter(topic_id=topic_id)
        
        # Сортировка
        valid_sort_fields = ['title', 'difficulty', 'created_at', '-title', '-difficulty', '-created_at']
        if sort_by in valid_sort_fields:
            tasks = tasks.order_by(sort_by)
        
        # Пагинация
        paginator = Paginator(tasks, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        data = []
        for task in page_obj:
            data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description[:200] + '...' if len(task.description) > 200 else task.description,
                'difficulty': task.difficulty,
                'difficulty_display': task.get_difficulty_display(),
                'difficulty_color': get_difficulty_color(task.difficulty),
                'difficulty_icon': get_difficulty_icon(task.difficulty),
                'topic': {
                    'id': task.topic.id,
                    'name': task.topic.name,
                    'code': task.topic.code
                } if task.topic else None,
                'source': task.source,
                'year': task.year,
                'tags': task.tags.split(',') if task.tags else [],
                'created_at': task.created_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page_obj.number,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'code': subject.code
            },
            'message': 'Задания успешно получены'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении заданий: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_task_by_id(request, task_id):
    """API для получения задания по ID"""
    try:
        # Получаем задание
        try:
            task = Task.objects.get(id=task_id, is_active=True)
        except Task.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Задание не найдено'
            }, status=404)
        
        # Статистика по этому заданию
        total_attempts = UserProgress.objects.filter(task=task).count()
        correct_attempts = UserProgress.objects.filter(task=task, is_correct=True).count()
        avg_score = UserProgress.objects.filter(task=task).aggregate(avg=Avg('score'))['avg'] or 0
        avg_time = UserProgress.objects.filter(task=task).aggregate(avg=Avg('time_spent'))['avg'] or 0
        
        data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'difficulty': task.difficulty,
            'difficulty_display': task.get_difficulty_display(),
            'difficulty_color': get_difficulty_color(task.difficulty),
            'difficulty_icon': get_difficulty_icon(task.difficulty),
            'subject': {
                'id': task.subject.id,
                'name': task.subject.name,
                'code': task.subject.code,
                'exam_type': task.subject.exam_type
            },
            'topic': {
                'id': task.topic.id,
                'name': task.topic.name,
                'code': task.topic.code,
                'description': task.topic.description
            } if task.topic else None,
            'answer': task.answer,
            'solution': task.solution,
            'source': task.source,
            'year': task.year,
            'tags': task.tags.split(',') if task.tags else [],
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'statistics': {
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'success_rate': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'average_score': round(avg_score, 1),
                'average_time': format_time_spent(int(avg_time)) if avg_time else '0 сек'
            }
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'message': 'Задание успешно получено'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении задания: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def search_tasks(request):
    """API для поиска заданий"""
    try:
        # Получаем параметры поиска
        query = request.GET.get('q', '')
        subject_id = request.GET.get('subject')
        difficulty = request.GET.get('difficulty')
        topic_id = request.GET.get('topic')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)
        sort_by = request.GET.get('sort', '-created_at')
        
        # Базовый запрос
        tasks = Task.objects.filter(is_active=True).select_related('subject', 'topic')
        
        # Поиск по тексту
        if query:
            tasks = tasks.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(subject__name__icontains=query) |
                Q(topic__name__icontains=query)
            )
        
        # Фильтры
        if subject_id:
            tasks = tasks.filter(subject_id=subject_id)
        if difficulty:
            tasks = tasks.filter(difficulty=difficulty)
        if topic_id:
            tasks = tasks.filter(topic_id=topic_id)
        
        # Сортировка
        valid_sort_fields = ['title', 'difficulty', 'created_at', '-title', '-difficulty', '-created_at']
        if sort_by in valid_sort_fields:
            tasks = tasks.order_by(sort_by)
        
        # Пагинация
        paginator = Paginator(tasks, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        data = []
        for task in page_obj:
            data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description[:200] + '...' if len(task.description) > 200 else task.description,
                'difficulty': task.difficulty,
                'difficulty_display': task.get_difficulty_display(),
                'difficulty_color': get_difficulty_color(task.difficulty),
                'difficulty_icon': get_difficulty_icon(task.difficulty),
                'subject': {
                    'id': task.subject.id,
                    'name': task.subject.name,
                    'code': task.subject.code
                },
                'topic': {
                    'id': task.topic.id,
                    'name': task.topic.name,
                    'code': task.topic.code
                } if task.topic else None,
                'source': task.source,
                'year': task.year,
                'created_at': task.created_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page_obj.number,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'search_params': {
                'query': query,
                'subject_id': subject_id,
                'difficulty': difficulty,
                'topic_id': topic_id,
                'sort_by': sort_by
            },
            'message': 'Поиск выполнен успешно'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при поиске: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_topics(request):
    """API для получения тем"""
    try:
        subject_id = request.GET.get('subject')
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        
        topics = Topic.objects.all()
        
        if subject_id:
            topics = topics.filter(subject_id=subject_id)
        if active_only:
            topics = topics.filter(is_active=True)
        
        # Аннотируем количество заданий
        topics = topics.annotate(
            task_count=Count('tasks', filter=Q(tasks__is_active=True))
        ).order_by('subject', 'order', 'name')
        
        data = []
        for topic in topics:
            data.append({
                'id': topic.id,
                'name': topic.name,
                'code': topic.code,
                'description': topic.description,
                'order': topic.order,
                'is_active': topic.is_active,
                'task_count': topic.task_count,
                'subject': {
                    'id': topic.subject.id,
                    'name': topic.subject.name,
                    'code': topic.subject.code
                }
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'message': 'Темы успешно получены'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении тем: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_statistics(request):
    """API для получения общей статистики"""
    try:
        # Общая статистика
        total_tasks = Task.objects.filter(is_active=True).count()
        total_subjects = Subject.objects.filter(is_active=True).count()
        total_topics = Topic.objects.filter(is_active=True).count()
        
        # Статистика по сложности
        difficulty_stats = Task.objects.filter(is_active=True).values('difficulty').annotate(
            count=Count('id')
        ).order_by('difficulty')
        
        # Статистика по предметам
        subject_stats = Subject.objects.filter(is_active=True).annotate(
            task_count=Count('tasks', filter=Q(tasks__is_active=True)),
            topic_count=Count('topics', filter=Q(topics__is_active=True))
        ).order_by('-task_count')[:10]
        
        # Статистика по годам
        year_stats = Task.objects.filter(is_active=True, year__isnull=False).values('year').annotate(
            count=Count('id')
        ).order_by('-year')[:10]
        
        data = {
            'overview': {
                'total_tasks': total_tasks,
                'total_subjects': total_subjects,
                'total_topics': total_topics
            },
            'difficulty_distribution': list(difficulty_stats),
            'top_subjects': [
                {
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'task_count': subject.task_count,
                    'topic_count': subject.topic_count
                }
                for subject in subject_stats
            ],
            'year_distribution': list(year_stats)
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'message': 'Статистика успешно получена'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при получении статистики: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_subscription(request):
    """MVP-вебхук: активирует подписку после оплаты (подпись HMAC)"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        username = payload.get('username')
        plan = payload.get('plan', 'PRO_MONTH')
        signature = payload.get('signature', '')
        mac = hmac.new(settings.BILLING_SECRET.encode('utf-8'), f"{username}|{plan}".encode('utf-8'), hashlib.sha256).hexdigest()
        if mac != signature:
            return HttpResponseBadRequest('bad signature')
        user, _ = User.objects.get_or_create(username=username)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        from django.utils import timezone
        if plan == 'PRO_MONTH':
            until = timezone.now() + timezone.timedelta(days=30)
        else:
            until = timezone.now() + timezone.timedelta(days=90)
        Subscription.objects.create(user=user, plan=plan, expires_at=until, is_active=True)
        return JsonResponse({'ok': True, 'expires_at': until.isoformat()})
    except Exception as e:
        return HttpResponseBadRequest(str(e))

