"""
Представления для системы персонализации ExamFlow
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

from .personalization_system import (
    get_user_insights,
    PersonalizedRecommendations,
    UserBehaviorAnalyzer
)

logger = logging.getLogger(__name__)


@login_required
def personalization_dashboard(request):
    """Дашборд персонализации с аналитикой и рекомендациями"""
    try:
        # Получаем персональные данные пользователя
        user_insights = get_user_insights(request.user.id)

        # Получаем рекомендации
        recommender = PersonalizedRecommendations(request.user.id)
        recommended_tasks = recommender.get_recommended_tasks(6)
        study_plan = recommender.get_study_plan()
        weak_topics = recommender.get_weak_topics()

        context = {
            'user_insights': user_insights,
            'recommended_tasks': recommended_tasks,
            'study_plan': study_plan,
            'weak_topics': weak_topics,
            'page_title': 'Персонализация - ExamFlow'
        }

        return render(request, 'core/personalization_dashboard.html', context)

    except Exception as e:
        logger.error(f"Ошибка в personalization_dashboard: {e}")
        messages.error(request, "Произошла ошибка при загрузке персонализации")
        return redirect('home')


@login_required
def my_analytics(request):
    """Детальная аналитика пользователя"""
    try:
        # Получаем аналитику
        analyzer = UserBehaviorAnalyzer(request.user.id)
        preferences = analyzer.get_user_preferences()
        patterns = analyzer.get_study_patterns()

        # Получаем прогресс
        user_insights = get_user_insights(request.user.id)
        progress_summary = user_insights.get('progress_summary', {})

        context = {
            'preferences': preferences,
            'patterns': patterns,
            'progress_summary': progress_summary,
            'page_title': 'Моя аналитика - ExamFlow'
        }

        return render(request, 'core/my_analytics.html', context)

    except Exception as e:
        logger.error(f"Ошибка в my_analytics: {e}")
        messages.error(request, "Произошла ошибка при загрузке аналитики")
        return redirect('home')


@login_required
def my_recommendations(request):
    """Персональные рекомендации"""
    try:
        # Получаем рекомендации
        recommender = PersonalizedRecommendations(request.user.id)
        recommended_tasks = recommender.get_recommended_tasks(10)
        weak_topics = recommender.get_weak_topics()

        context = {
            'recommended_tasks': recommended_tasks,
            'weak_topics': weak_topics,
            'page_title': 'Мои рекомендации - ExamFlow'
        }

        return render(request, 'core/my_recommendations.html', context)

    except Exception as e:
        logger.error(f"Ошибка в my_recommendations: {e}")
        messages.error(request, "Произошла ошибка при загрузке рекомендаций")
        return redirect('home')


@login_required
def study_plan_view(request):
    """Персональный план обучения"""
    try:
        # Получаем план обучения
        recommender = PersonalizedRecommendations(request.user.id)
        study_plan = recommender.get_study_plan()

        context = {
            'study_plan': study_plan,
            'page_title': 'План обучения - ExamFlow'
        }

        return render(request, 'core/study_plan.html', context)

    except Exception as e:
        logger.error(f"Ошибка в study_plan_view: {e}")
        messages.error(request, "Произошла ошибка при загрузке плана обучения")
        return redirect('home')


@login_required
def weak_topics_view(request):
    """Анализ слабых тем"""
    try:
        # Получаем слабые темы
        recommender = PersonalizedRecommendations(request.user.id)
        weak_topics = recommender.get_weak_topics()

        context = {
            'weak_topics': weak_topics,
            'page_title': 'Слабые темы - ExamFlow'
        }

        return render(request, 'core/weak_topics.html', context)

    except Exception as e:
        logger.error(f"Ошибка в weak_topics_view: {e}")
        messages.error(request, "Произошла ошибка при загрузке слабых тем")
        return redirect('home')


# API endpoints для AJAX запросов
@login_required
@require_http_methods(["GET"])
def api_user_insights(request):
    """API для получения персональных данных пользователя"""
    try:
        user_insights = get_user_insights(request.user.id)
        return JsonResponse(user_insights)
    except Exception as e:
        logger.error(f"Ошибка в api_user_insights: {e}")
        return JsonResponse({'error': 'Ошибка загрузки данных'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_recommended_tasks(request):
    """API для получения рекомендуемых задач"""
    try:
        limit = int(request.GET.get('limit', 6))
        recommender = PersonalizedRecommendations(request.user.id)
        tasks = recommender.get_recommended_tasks(limit)
        return JsonResponse({'tasks': tasks})
    except Exception as e:
        logger.error(f"Ошибка в api_recommended_tasks: {e}")
        return JsonResponse({'error': 'Ошибка загрузки рекомендаций'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_study_plan(request):
    """API для получения плана обучения"""
    try:
        recommender = PersonalizedRecommendations(request.user.id)
        plan = recommender.get_study_plan()
        return JsonResponse({'plan': plan})
    except Exception as e:
        logger.error(f"Ошибка в api_study_plan: {e}")
        return JsonResponse({'error': 'Ошибка загрузки плана'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_weak_topics(request):
    """API для получения слабых тем"""
    try:
        recommender = PersonalizedRecommendations(request.user.id)
        topics = recommender.get_weak_topics()
        return JsonResponse({'topics': topics})
    except Exception as e:
        logger.error(f"Ошибка в api_weak_topics: {e}")
        return JsonResponse({'error': 'Ошибка загрузки слабых тем'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_user_preferences(request):
    """API для получения предпочтений пользователя"""
    try:
        analyzer = UserBehaviorAnalyzer(request.user.id)
        preferences = analyzer.get_user_preferences()
        return JsonResponse({'preferences': preferences})
    except Exception as e:
        logger.error(f"Ошибка в api_user_preferences: {e}")
        return JsonResponse({'error': 'Ошибка загрузки предпочтений'}, status=500)
