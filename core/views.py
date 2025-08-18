from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.core import management
from .models import Task, Subject
from .utils import generate_qr_code


@cache_page(30)
def home(request):
    # Лёгкий автосид: если база пуста, попробуем загрузить демо-данные
    if Subject.objects.count() == 0 and Task.objects.count() == 0:
        try:
            management.call_command('load_sample_data')
        except Exception:
            pass

    total_tasks = Task.objects.count()
    total_subjects = Subject.objects.count()
    subjects = Subject.objects.all()[:6]
    qr_code = generate_qr_code("https://t.me/ExamFlowBot")
    return render(request, 'home.html', {
        'qr_code': qr_code,
        'subjects': subjects,
        'total_subjects': total_subjects,
        'total_tasks': total_tasks,
    })


@cache_page(30)
def subject_list(request):
    items = Subject.objects.all().order_by('name')
    return render(request, 'core/subject_list.html', {'subjects': items})


@cache_page(30)
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    tasks = Task.objects.filter(subject=subject).order_by('-created_at', '-id')
    paginator = Paginator(tasks, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'subject': subject,
        'page_obj': page_obj,
        'total_tasks': tasks.count(),
    }
    return render(request, 'core/subject_detail.html', context)


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    similar_tasks = Task.objects.filter(subject=task.subject).exclude(id=task.id).order_by('-created_at')[:3]
    return render(request, 'core/task_detail.html', {'task': task, 'similar_tasks': similar_tasks})