"""
API эндпоинты для AI запросов через RAG оркестратор
"""

import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.premium.decorators import free_tier_allowed, premium_required, rate_limited
from drf_spectacular.utils import extend_schema
import json

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@free_tier_allowed
@extend_schema(tags=['AI'],
               summary='AI-помощник',
               description='Основной эндпоинт для AI запросов через RAG систему',
               request={'application/json': {'type': 'object',
                                             'properties': {'query': {'type': 'string',
                                                                      'description': 'Вопрос пользователя'},
                                                            'subject': {'type': 'string',
                                                                        'description': 'Предмет (Математика, Русский язык)'},
                                                            'document_type': {'type': 'string',
                                                                              'description': 'Тип документа ФИПИ'}},
                                             'required': ['query']}},
               responses={200: {'description': 'Успешный ответ',
                                'content': {'application/json': {'example': {'answer': 'Ответ AI-помощника',
                                                                             'sources': [{'title': 'Источник',
                                                                                          'url': 'https://...'}],
                                                                             'context_chunks': 3,
                                                                             'processing_time': 1.5,
                                                                             'cached': False}}}},
               400: {'description': 'Неверный запрос'},
               429: {'description': 'Превышен лимит запросов'},
               500: {'description': 'Внутренняя ошибка сервера'}})
def ai_ask(request: HttpRequest) -> JsonResponse:
    """
    Основной эндпоинт для AI запросов через RAG систему

    POST /api/ai/ask
        "query": "Как решать квадратные уравнения?",
        "subject": "Математика",
        "document_type": "demo_variant"
    }
    """
    try:
        # Парсим JSON данные
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        query = data.get("query", "").strip()
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)

        subject = data.get("subject", "").strip()
        document_type = data.get("document_type", "").strip()
        # Получаем user_id если пользователь авторизован
        user_id = request.user.id if request.user.is_authenticated else None  # type: ignore

        # Инициализируем оркестратор
        from core.rag_system.orchestrator import RAGOrchestrator
        orchestrator = RAGOrchestrator()

        # Обрабатываем запрос
        result = orchestrator.process_query(
            query=query,
            subject=subject,
            document_type=document_type,
            user_id=user_id
        )

        return JsonResponse(result)

    except Exception as e:
        logger.error("Ошибка в ai_ask: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@rate_limited(max_requests_per_hour=30, max_requests_per_day=100)
def ai_subjects(request: HttpRequest) -> JsonResponse:
    """
    Возвращает список доступных предметов

    GET /api/ai/subjects
    """
    try:
        from core.models import Subject

        subjects = Subject.objects.all().values(
            'id', 'name', 'code', 'exam_type')  # type: ignore

        return JsonResponse({
            "subjects": list(subjects),
            "count": len(subjects)
        })

    except Exception as e:
        logger.error("Ошибка в ai_subjects: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@rate_limited(max_requests_per_hour=20, max_requests_per_day=50)
def ai_user_profile(request: HttpRequest) -> JsonResponse:
    """
    Возвращает профиль пользователя

    GET /api/ai/user/profile
    """
    try:
        if not request.user.is_authenticated:  # type: ignore
            return JsonResponse({"error": "Authentication required"}, status=401)

        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(
            user=request.user)  # type: ignore

        return JsonResponse({
            "profile": {
                "id": profile.id,
                "username": request.user.username,  # type: ignore
                "email": request.user.email,  # type: ignore
                "subscription_type": profile.subscription_type,
                "is_premium": profile.is_premium,
                "total_queries": profile.total_queries,
                "query_stats": profile.query_stats,
                "preferred_subjects": profile.preferred_subjects,
                "difficulty_preference": profile.difficulty_preference,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            },
            "created": created
        })

    except Exception as e:
        logger.error("Ошибка в ai_user_profile: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@rate_limited(max_requests_per_hour=15, max_requests_per_day=30)
def ai_problem_submit(request: HttpRequest) -> JsonResponse:
    """
    Отправляет решение задачи для проверки

    POST /api/ai/problem/submit
        "task_id": 123,
        "solution": "Мое решение...",
        "answer": "42"
    }
    """
    try:
        if not request.user.is_authenticated:  # type: ignore
            return JsonResponse({"error": "Authentication required"}, status=401)

        # Парсим JSON данные
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        task_id = data.get("task_id")
        solution = data.get("solution", "").strip()
        answer = data.get("answer", "").strip()

        if not task_id or not solution:
            return JsonResponse(

        from core.models import Task, UserProfile

        try:
            task = Task.objects.get(id=task_id)  # type: ignore
        except Task.DoesNotExist:  # type: ignore
            return JsonResponse({"error": "Task not found"}, status=404)

        # Получаем профиль пользователя
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user)  # type: ignore

        # Простая проверка ответа (в будущем можно добавить AI проверку)
        is_correct = False
        if answer and task.answer:
            is_correct = answer.lower().strip() == task.answer.lower().strip()

        # Обновляем статистику пользователя
        subject_key = task.subject.name
        if subject_key not in profile.query_stats:
            profile.query_stats[subject_key] = 0
        profile.query_stats[subject_key] += 1
        profile.save()

        return JsonResponse({
            "task_id": task_id,
            "is_correct": is_correct,
            "correct_answer": task.answer if is_correct else None,
            "feedback": "Правильно!" if is_correct else "Попробуйте еще раз",
            "solution": solution,
            "user_answer": answer
        })

    except Exception as e:
        logger.error("Ошибка в ai_problem_submit: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@premium_required
def ai_statistics(request: HttpRequest) -> JsonResponse:
    """
    Возвращает статистику RAG системы

    GET /api/ai/statistics
    """
    try:
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()
        stats = orchestrator.get_statistics()

        return JsonResponse(stats)

    except Exception as e:
        logger.error("Ошибка в ai_statistics: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
