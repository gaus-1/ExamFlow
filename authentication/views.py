"""
Представления для модуля аутентификации

Обрабатывает:
- Регистрацию пользователей (упрощенная форма)
- Вход в систему (по email)
- Выход из системы
- Личный кабинет пользователя
- Обновление профиля
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import TechRegisterForm, TechLoginForm, ProfileUpdateForm


def register_view(request):
    """
    Регистрация нового пользователя
    
    Использует упрощенную форму: имя, email, пароль (2 раза)
    Автоматически генерирует username из email
    """
    if request.method == 'POST':
        form = TechRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Явно указываем backend для аутентификации
            from authentication.backends import EmailBackend
            login(request, user, backend='authentication.backends.EmailBackend')
            messages.success(request, f'Добро пожаловать, {user.first_name}! Ваш аккаунт успешно создан.')
            return redirect('authentication:dashboard')
    else:
        form = TechRegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})


class TechLoginView(LoginView):
    """Вход в систему в Duolingo-стиле"""
    form_class = TechLoginForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/dashboard/'
    
    def form_valid(self, form):
        messages.success(self.request, f'С возвращением, {form.get_user().first_name}!')
        return super().form_valid(form)


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('learning:home')


@login_required
def dashboard_view(request):
    """
    Личный кабинет пользователя
    
    Показывает:
    - Статистику обучения
    - Последние решенные задания
    - Прогресс по предметам
    - Достижения
    """
    from core.models import UserProgress, Task, Subject
    
    # Получаем статистику пользователя
    user_progress = UserProgress.objects.filter(user=request.user)  # type: ignore
    total_solved = user_progress.filter(is_correct=True).count()  # type: ignore
    total_attempts = user_progress.count()  # type: ignore
    
    # Прогресс по предметам
    subjects_progress = {}
    for subject in Subject.objects.all():  # type: ignore   
        subject_progress = user_progress.filter(task__subject=subject)  # type: ignore
        subjects_progress[subject.name] = {
            'total': subject_progress.count(),  # type: ignore
            'correct': subject_progress.filter(is_correct=True).count(),  # type: ignore
            'subject': subject
        }
    
    # Последние решенные задания
    recent_tasks = user_progress.order_by('-created_at')[:5]  # type: ignore    
    
    context = {
        'total_solved': total_solved,
        'total_attempts': total_attempts,
        'accuracy': round((total_solved / total_attempts * 100) if total_attempts > 0 else 0, 1),
        'subjects_progress': subjects_progress,
        'recent_tasks': recent_tasks,
        # Добавляем недостающие переменные для шаблона
        'total_tasks_solved': total_solved,
        'user_subjects': len(subjects_progress),
        'profile': {
            'level': 1,
            'experience': total_solved * 10,
            'is_premium': False,
            'subscription_type': 'Бесплатный',
            'streak_days': 0,
            'last_activity': request.user.last_login or request.user.date_joined,
            'tasks_solved_today': total_solved,
            'daily_tasks_limit': 10,
            'telegram_id': None
        },
        'rating': {
            'accuracy': round((total_solved / total_attempts * 100) if total_attempts > 0 else 0, 1),
            'rank': '-'
        },
        'achievements': [],
        'can_solve_tasks': True,
        'active_subscription': None
    }
    
    return render(request, 'auth/dashboard.html', context)


@login_required
def profile_update_view(request):
    """Обновление профиля пользователя"""
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST)
        if form.is_valid():
            # Обновляем данные пользователя
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('authentication:dashboard')
    else:
        # Предзаполняем форму данными пользователя
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = ProfileUpdateForm(initial=initial_data)
    
    return render(request, 'auth/profile_update.html', {'form': form})
