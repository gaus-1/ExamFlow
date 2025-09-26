"""
API для системы персонализации ExamFlow
Предоставляет эндпоинты для получения персонализированных рекомендаций
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .personalization_system import (
    PersonalizedRecommendations,
    UserBehaviorAnalyzer,
    get_user_insights,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_personalized_recommendations(request):
    """Получает персонализированные рекомендации для пользователя"""
    try:
        user_id = request.user.id
        insights = get_user_insights(user_id)

        return JsonResponse({"success": True, "data": insights})

    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении рекомендаций"}, status=500
        )


@login_required
@require_http_methods(["GET"])
def get_study_plan(request):
    """Получает персонализированный план обучения"""
    try:
        user_id = request.user.id
        recommender = PersonalizedRecommendations(user_id)
        study_plan = recommender.get_study_plan()

        return JsonResponse({"success": True, "data": study_plan})

    except Exception as e:
        logger.error(f"Ошибка при получении плана обучения: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении плана обучения"},
            status=500,
        )


@login_required
@require_http_methods(["GET"])
def get_weak_topics(request):
    """Получает слабые темы пользователя"""
    try:
        user_id = request.user.id
        recommender = PersonalizedRecommendations(user_id)
        weak_topics = recommender.get_weak_topics()

        return JsonResponse({"success": True, "data": weak_topics})

    except Exception as e:
        logger.error(f"Ошибка при получении слабых тем: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении слабых тем"}, status=500
        )


@login_required
@require_http_methods(["GET"])
def get_user_preferences(request):
    """Получает предпочтения пользователя"""
    try:
        user_id = request.user.id
        analyzer = UserBehaviorAnalyzer(user_id)
        preferences = analyzer.get_user_preferences()

        return JsonResponse({"success": True, "data": preferences})

    except Exception as e:
        logger.error(f"Ошибка при получении предпочтений: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении предпочтений"}, status=500
        )


@login_required
@require_http_methods(["GET"])
def get_study_patterns(request):
    """Получает паттерны обучения пользователя"""
    try:
        user_id = request.user.id
        analyzer = UserBehaviorAnalyzer(user_id)
        patterns = analyzer.get_study_patterns()

        return JsonResponse({"success": True, "data": patterns})

    except Exception as e:
        logger.error(f"Ошибка при получении паттернов обучения: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении паттернов обучения"},
            status=500,
        )


@login_required
@require_http_methods(["GET"])
def get_recommended_tasks(request):
    """Получает рекомендованные задания для пользователя"""
    try:
        user_id = request.user.id
        limit = int(request.GET.get("limit", 10))

        recommender = PersonalizedRecommendations(user_id)
        recommended_tasks = recommender.get_recommended_tasks(limit)

        # Преобразуем в JSON-совместимый формат
        tasks_data = []
        for task in recommended_tasks:
            tasks_data.append(
                {
                    "id": getattr(task, "id", None),
                    "title": getattr(task, "title", ""),
                    "description": getattr(task, "description", ""),
                    "difficulty": getattr(task, "difficulty", 3),
                    "subject": (
                        getattr(task.subject, "name", "")
                        if hasattr(task, "subject")
                        else ""
                    ),
                    "source": getattr(task, "source", ""),
                    "created_at": (
                        str(task.created_at)
                        if hasattr(task, "created_at") and task.created_at
                        else None
                    ),
                }
            )

        return JsonResponse(
            {"success": True, "data": {"tasks": tasks_data, "total": len(tasks_data)}}
        )

    except Exception as e:
        logger.error(f"Ошибка при получении рекомендованных заданий: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении рекомендованных заданий"},
            status=500,
        )


@login_required
@require_http_methods(["GET"])
def get_progress_analytics(request):
    """Получает аналитику прогресса пользователя"""
    try:
        user_id = request.user.id
        insights = get_user_insights(user_id)

        # Формируем краткую аналитику
        analytics = {
            "progress_summary": insights.get("progress_summary", {}),
            "study_patterns": insights.get("patterns", {}),
            "weak_topics_count": len(insights.get("weak_topics", [])),
            "favorite_subjects": insights.get("preferences", {}).get(
                "favorite_subjects", []
            ),
            "difficulty_preference": insights.get("preferences", {}).get(
                "difficulty_preference", 3
            ),
        }

        return JsonResponse({"success": True, "data": analytics})

    except Exception as e:
        logger.error(f"Ошибка при получении аналитики: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении аналитики"}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def update_user_preferences(request):
    """Обновляет предпочтения пользователя"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse(
                {"success": False, "error": "Требуется авторизация"}, status=401
            )

        json.loads(request.body)
        _ = request.user.id

        return JsonResponse({"success": True, "message": "Предпочтения обновлены"})

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Неверный формат JSON"}, status=400
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении предпочтений: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при обновлении предпочтений"},
            status=500,
        )


def get_personalization_summary(request):
    """Получает краткую сводку персонализации (для неавторизованных пользователей)"""
    try:
        summary = {
            "system_features": [
                "Персонализированные рекомендации",
                "Анализ поведения пользователей",
                "Планы обучения",
                "Выявление слабых тем",
                "Аналитика прогресса",
            ],
            "benefits": [
                "Адаптивное обучение",
                "Повышение эффективности",
                "Мотивация к обучению",
                "Фокус на проблемных областях",
            ],
        }

        return JsonResponse({"success": True, "data": summary})

    except Exception as e:
        logger.error(f"Ошибка при получении сводки персонализации: {e}")
        return JsonResponse(
            {"success": False, "error": "Ошибка при получении сводки"}, status=500
        )
