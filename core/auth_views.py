"""
Views для аутентификации и управления пользователями
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json

# Импортируем формы из нового модуля authentication
try:
    from authentication.forms import TechRegisterForm, TechLoginForm, ProfileUpdateForm
except ImportError:
    # Если модуль недоступен, используем заглушки
    from .forms import TechRegisterForm, TechLoginForm, ProfileUpdateForm
from authentication.models import UserProfile, Subscription
from learning.models import UserRating, Achievement


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = TechRegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Автоматический вход после регистрации
                    username = form.cleaned_data.get('username')
                    password = form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                        # Создаем рейтинг пользователя
                        UserRating.objects.create(user=user)  # type: ignore
                        # Добавляем достижение за регистрацию
                        Achievement.objects.create(  # type: ignore
                            user=user,
                            name='Добро пожаловать!',
                            description='Регистрация в ExamFlow',
                            icon='fas fa-user-plus',
                            color='#00ff88'
                        )
                        messages.success(
                            request, 'Регистрация успешна! Добро пожаловать в ExamFlow!')
                        return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
    else:
        form = TechRegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = TechLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                # Обновляем время последней активности
                profile, created = UserProfile.objects.get_or_create(
                    user=user)  # type: ignore
                profile.last_activity = timezone.now()
                profile.save()

                messages.success(
                    request, f'Добро пожаловать, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверные данные для входа')
    else:
        form = TechLoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('learning:home')


@login_required
def dashboard_view(request):
    """Личный кабинет пользователя"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)  # type: ignore
    rating, created = UserRating.objects.get_or_create(user=user)  # type: ignore
    achievements = Achievement.objects.filter(
        user=user).order_by('-created_at')  # type: ignore

    # Статистика пользователя
    from learning.models import UserProgress, Subject
    total_tasks_solved = UserProgress.objects.filter(
        user=user, is_correct=True).count()  # type: ignore
    total_subjects = Subject.objects.count()  # type: ignore
    user_subjects = UserProgress.objects.filter(user=user).values(
        'task__subject').distinct().count()  # type: ignore

    # Проверяем подписку
    active_subscription = None
    if profile.is_premium:
        active_subscription = Subscription.objects.filter(  # type: ignore
            user=user,
            status='active',
            expires_at__gt=timezone.now()
        ).first()

    context = {
        'user': user,
        'profile': profile,
        'rating': rating,
        'achievements': achievements[:5],  # Показываем последние 5 достижений
        'total_tasks_solved': total_tasks_solved,
        'total_subjects': total_subjects,
        'user_subjects': user_subjects,
        'active_subscription': active_subscription,
        'can_solve_tasks': profile.can_solve_tasks,
        'tasks_left_today': profile.daily_tasks_limit - profile.tasks_solved_today if not profile.is_premium else 'Безлимитно'
    }

    return render(request, 'auth/dashboard.html', context)


@login_required
def profile_view(request):
    """Профиль пользователя"""
    profile, created = UserProfile.objects.get_or_create(
        user=request.user)  # type: ignore

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)

    return render(request, 'auth/profile.html', {'form': form, 'profile': profile})


@login_required
@require_http_methods(["POST"])
def subscribe_view(request):
    """Оформление подписки"""
    try:
        data = json.loads(request.body)
        subscription_type = data.get('type')  # 'monthly' или 'yearly'
        payment_method = data.get('payment_method')  # 'card' или 'btc'

        if subscription_type not in ['monthly', 'yearly']:
            return JsonResponse({'success': False, 'error': 'Неверный тип подписки'})

        if payment_method not in ['card', 'btc']:
            return JsonResponse({'success': False, 'error': 'Неверный способ оплаты'})

        # Определяем стоимость
        amounts = {
            'monthly': 990.00,
            'yearly': 9900.00
        }
        amount = amounts[subscription_type]

        # Создаем подписку в статусе ожидания
        starts_at = timezone.now()
        expires_at = starts_at + \
            timedelta(days=30 if subscription_type == 'monthly' else 365)

        subscription = Subscription.objects.create(  # type: ignore
            user=request.user,
            subscription_type=subscription_type,
            amount=amount,
            payment_id=f"sub_{timezone.now().timestamp()}_{request.user.id}",
            payment_method=payment_method,
            status='pending',
            starts_at=starts_at,
            expires_at=expires_at
        )

        # Здесь должна быть интеграция с платежной системой
        # Пока имитируем успешную оплату
        if payment_method == 'card':
            # Интеграция с CloudPayments
            payment_url = f"/payment/card/{subscription.id}/"
        else:
            # Интеграция с Bitcoin
            payment_url = f"/payment/btc/{subscription.id}/"

        return JsonResponse({
            'success': True,
            'payment_url': payment_url,
            'subscription_id': subscription.id,
            'amount': float(amount)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def achievements_view(request):
    """Страница достижений пользователя"""
    achievements = Achievement.objects.filter(
        user=request.user).order_by('-created_at')  # type: ignore
    profile = UserProfile.objects.get(user=request.user)  # type: ignore

    # Статистика достижений
    total_achievements = achievements.count()

    context = {
        'achievements': achievements,
        'total_achievements': total_achievements,
        'profile': profile
    }

    return render(request, 'auth/achievements.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def telegram_auth(request):
    """Аутентификация через Telegram"""
    try:
        data = json.loads(request.body)
        telegram_id = data.get('telegram_id')
        data.get('username')
        first_name = data.get('first_name', '')

        if not telegram_id:
            return JsonResponse({'success': False, 'error': 'Telegram ID обязателен'})

        # Ищем пользователя по Telegram ID
        try:
            profile = UserProfile.objects.get(telegram_id=telegram_id)  # type: ignore
            user = profile.user
        except UserProfile.DoesNotExist:  # type: ignore
            # Создаем нового пользователя
            user = User.objects.create_user(
                username=f'tg_{telegram_id}',
                first_name=first_name
            )
            profile = UserProfile.objects.create(  # type: ignore
                user=user,
                telegram_id=telegram_id
            )
            UserRating.objects.create(user=user)  # type: ignore

        # Обновляем время активности
        profile.last_activity = timezone.now()
        profile.save()

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'is_premium': profile.is_premium,
            'can_solve_tasks': profile.can_solve_tasks
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
