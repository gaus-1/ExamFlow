"""
Представления для системы персонализации ExamFlow
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .services.dashboard_service import DashboardService
from .services.api_service import APIService, StandardAPIResponseBuilder

logger = logging.getLogger(__name__)

@login_required
def personalization_dashboard(request):
    """Дашборд персонализации с аналитикой и рекомендациями"""
    try:
        dashboard_service = DashboardService(request.user)
        context = dashboard_service.build_dashboard_context()
        
        return render(request, 'core/personalization_dashboard.html', context)

    except Exception as e:
        logger.error(f"Ошибка в personalization_dashboard: {e}")
        messages.error(request, "Произошла ошибка при загрузке персонализации")
        return redirect('home')

@login_required
def my_analytics(request):
    """Детальная аналитика пользователя"""
    try:
        dashboard_service = DashboardService(request.user)
        user_insights = dashboard_service.get_user_insights()
        
        context = {
            'user_insights': user_insights,
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
        dashboard_service = DashboardService(request.user)
        
        context = {
            'recommended_tasks': dashboard_service.get_recommended_tasks(10),
            'weak_topics': dashboard_service.get_weak_topics(),
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
        dashboard_service = DashboardService(request.user)
        
        context = {
            'study_plan': dashboard_service.get_study_plan(),
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
        dashboard_service = DashboardService(request.user)
        
        context = {
            'weak_topics': dashboard_service.get_weak_topics(),
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
@ratelimit(key='user', rate='30/m', block=True)
def api_user_insights(request):
    """API для получения персональных данных пользователя"""
    api_service = APIService(StandardAPIResponseBuilder())
    return api_service.handle_user_insights_request(request.user)

@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='30/m', block=True)
def api_recommended_tasks(request):
    """API для получения рекомендуемых задач"""
    try:
        limit = int(request.GET.get('limit', 6))
        api_service = APIService(StandardAPIResponseBuilder())
        return api_service.handle_recommendations_request(request.user, limit)
    except ValueError:
        api_service = APIService(StandardAPIResponseBuilder())
        return api_service.response_builder.build_error_response(
            "Некорректный параметр limit", 400
        )

@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='30/m', block=True)
def api_study_plan(request):
    """API для получения плана обучения"""
    api_service = APIService(StandardAPIResponseBuilder())
    return api_service.handle_study_plan_request(request.user)

@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='30/m', block=True)
def api_weak_topics(request):
    """API для получения слабых тем"""
    api_service = APIService(StandardAPIResponseBuilder())
    return api_service.handle_weak_topics_request(request.user)

@login_required
@require_http_methods(["GET"])
@ratelimit(key='user', rate='30/m', block=True)
def api_user_preferences(request):
    """API для получения предпочтений пользователя"""
    api_service = APIService(StandardAPIResponseBuilder())
    return api_service.handle_user_insights_request(request.user)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint для Render"""
    return JsonResponse({
        "status": "healthy",
        "service": "ExamFlow 2.0",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    })
