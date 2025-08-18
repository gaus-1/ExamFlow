from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.core import management
from .models import Task, Subject, Topic, UserProgress, UserProfile
from .utils import generate_qr_code


@cache_page(60)
def home(request):
    # Автосид данных при пустой базе, чтобы сайт не был пустым на проде без Shell
    if Subject.objects.count() == 0 and Task.objects.count() == 0:
        try:
            management.call_command('load_sample_data')
        except Exception:
            pass

    total_tasks = Task.objects.filter(is_active=True).count()
    total_subjects = Subject.objects.filter(is_active=True).count()
    total_users = UserProfile.objects.count()

    subjects = Subject.objects.filter(is_active=True).annotate(
        task_count=Count('tasks')
    ).order_by('-task_count')[:6]

    bot_url = "https://t.me/ExamFlowBot"
    qr_code = generate_qr_code(bot_url)

    context = {
        'total_tasks': total_tasks,
        'total_subjects': total_subjects,
        'total_users': total_users,
        'success_rate': 95,
        'subjects': subjects,
        'qr_code': qr_code,
    }
    return render(request, 'home.html', context)


@cache_page(60)
def subject_list(request):
    subjects = Subject.objects.filter(is_active=True).annotate(
        task_count=Count('tasks'),
        topic_count=Count('topics')
    ).order_by('name')
    return render(request, 'core/subject_list.html', {'subjects': subjects})


@cache_page(60)
def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, is_active=True)
    topics = subject.topics.filter(is_active=True).annotate(task_count=Count('tasks')).order_by('order', 'name')
    tasks = subject.tasks.filter(is_active=True).select_related('topic').order_by('-id')
    paginator = Paginator(tasks, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'subject': subject,
        'topics': topics,
        'page_obj': page_obj,
        'total_tasks': tasks.count(),
        'tasks_with_topics': subject.tasks.filter(is_active=True, topic__isnull=False).count(),
        'show_all_tasks': True,
    }
    return render(request, 'core/subject_detail.html', context)


@cache_page(60)
def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_active=True)
    tasks = topic.tasks.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(tasks, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/topic_detail.html', {'topic': topic, 'page_obj': page_obj})


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, is_active=True)
    similar_tasks = Task.objects.filter(subject=task.subject, is_active=True).exclude(id=task.id).order_by('?')[:3]
    return render(request, 'core/task_detail.html', {'task': task, 'similar_tasks': similar_tasks})


@cache_page(60)
def weak_spots(request):
    subjects = Subject.objects.filter(is_active=True).annotate(task_count=Count('tasks')).order_by('-task_count')[:8]
    return render(request, 'core/weak_spots.html', {'subjects': subjects})


@login_required
def user_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    progress = UserProgress.objects.filter(user=request.user).select_related('task', 'task__subject').order_by('-last_attempt')[:20]
    subject_stats = UserProgress.objects.filter(user=request.user, is_correct=True).values('task__subject__name').annotate(
        completed=Count('id'), avg_score=Avg('score')
    ).order_by('-completed')
    return render(request, 'core/user_profile.html', {'profile': profile, 'progress': progress, 'subject_stats': subject_stats})


@login_required
def user_progress(request):
    progress = UserProgress.objects.filter(user=request.user).select_related('task', 'task__subject', 'task__topic').order_by('-last_attempt')
    subject_filter = request.GET.get('subject')
    if subject_filter:
        progress = progress.filter(task__subject_id=subject_filter)
    paginator = Paginator(progress, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    subjects = Subject.objects.filter(is_active=True).order_by('name')
    return render(request, 'core/user_progress.html', {'page_obj': page_obj, 'subjects': subjects, 'current_subject': subject_filter})


def search_tasks(request):
    query = request.GET.get('q', '')
    subject_id = request.GET.get('subject', '')
    difficulty = request.GET.get('difficulty', '')
    topic_id = request.GET.get('topic', '')
    tasks = Task.objects.filter(is_active=True).select_related('subject', 'topic')
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query))
    if subject_id:
        tasks = tasks.filter(subject_id=subject_id)
    if difficulty:
        tasks = tasks.filter(difficulty=difficulty)
    if topic_id:
        tasks = tasks.filter(topic_id=topic_id)
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['title', 'difficulty', 'created_at', '-title', '-difficulty', '-created_at']:
        tasks = tasks.order_by(sort_by)
    paginator = Paginator(tasks, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    subjects = Subject.objects.filter(is_active=True).order_by('name')
    topics = Topic.objects.filter(is_active=True).order_by('subject', 'order', 'name')
    return render(request, 'core/search_tasks.html', {
        'page_obj': page_obj,
        'subjects': subjects,
        'topics': topics,
        'query': query,
        'current_subject': subject_id,
        'current_difficulty': difficulty,
        'current_topic': topic_id,
        'current_sort': sort_by,
    })