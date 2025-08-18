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