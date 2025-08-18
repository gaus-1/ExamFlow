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
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}! Ваш аккаунт успешно создан.')
            return redirect('dashboard')
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
    return redirect('home')


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
    user_progress = UserProgress.objects.filter(user=request.user)
    total_solved = user_progress.filter(is_correct=True).count()
    total_attempts = user_progress.count()
    
    # Прогресс по предметам
    subjects_progress = {}
    for subject in Subject.objects.all():
        subject_progress = user_progress.filter(task__topic__subject=subject)
        subjects_progress[subject.name] = {
            'total': subject_progress.count(),
            'correct': subject_progress.filter(is_correct=True).count(),
            'subject': subject
        }
    
    # Последние решенные задания
    recent_tasks = user_progress.order_by('-created_at')[:5]
    
    context = {
        'total_solved': total_solved,
        'total_attempts': total_attempts,
        'accuracy': round((total_solved / total_attempts * 100) if total_attempts > 0 else 0, 1),
        'subjects_progress': subjects_progress,
        'recent_tasks': recent_tasks,
    }
    
    return render(request, 'auth/dashboard.html', context)


@login_required
def profile_update_view(request):
    """Обновление профиля пользователя"""
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            # Обновляем данные пользователя
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            
            # Обновляем профиль
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('dashboard')
    else:
        # Предзаполняем форму данными пользователя
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = ProfileUpdateForm(instance=profile, initial=initial_data)
    
    return render(request, 'auth/profile_update.html', {'form': form})
