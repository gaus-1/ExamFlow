"""
API для премиум-функций
"""

import logging
from typing import Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from core.premium.access_control import get_access_control, get_usage_tracker, premium_required
from core.models import FIPIData, DataChunk
from core.rag_system.orchestrator import get_ai_orchestrator

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
@login_required
def get_premium_status(request):
    """Получает статус премиум-подписки пользователя"""
    try:
        access_control = get_access_control()
        
        status = {
            'is_premium': access_control.is_premium_user(request.user),
            'has_active_subscription': access_control.has_active_subscription(request.user),
            'user_features': access_control.get_user_features(request.user),
            'usage_limits': access_control.get_usage_limits(request.user)
        }
        
        return JsonResponse({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения премиум статуса: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка получения статуса подписки'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required
def track_usage(request):
    """Отслеживает использование функций"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        count = data.get('count', 1)
        
        if not action:
            return JsonResponse({
                'success': False,
                'error': 'Не указано действие'
            }, status=400)
        
        usage_tracker = get_usage_tracker()
        success = usage_tracker.track_usage(request.user, action, count)
        
        if success:
            stats = usage_tracker.get_usage_stats(request.user, action)
            return JsonResponse({
                'success': True,
                'stats': stats
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Превышен лимит использования',
                'code': 'USAGE_LIMIT_EXCEEDED'
            }, status=429)
            
    except Exception as e:
        logger.error(f"Ошибка отслеживания использования: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка отслеживания использования'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_usage_stats(request):
    """Получает статистику использования"""
    try:
        usage_tracker = get_usage_tracker()
        actions = ['daily_requests', 'monthly_requests', 'pdf_exports', 'advanced_searches']
        
        stats = {}
        for action in actions:
            stats[action] = usage_tracker.get_usage_stats(request.user, action)
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики использования: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка получения статистики'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@premium_required('pdf_export')
def export_to_pdf(request):
    """Экспортирует контент в PDF"""
    try:
        data = json.loads(request.body)
        content_id = data.get('content_id')
        content_type = data.get('content_type', 'fipi_data')
        
        if not content_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указан ID контента'
            }, status=400)
        
        # Отслеживаем использование
        usage_tracker = get_usage_tracker()
        if not usage_tracker.track_usage(request.user, 'pdf_exports', 1):
            return JsonResponse({
                'success': False,
                'error': 'Превышен лимит экспорта в PDF',
                'code': 'PDF_EXPORT_LIMIT_EXCEEDED'
            }, status=429)
        
        # Получаем контент
        if content_type == 'fipi_data':
            try:
                fipi_data = FIPIData.objects.get(id=content_id)  # type: ignore
                content = {
                    'title': fipi_data.title,
                    'content': fipi_data.content,
                    'data_type': fipi_data.get_data_type_display(),  # type: ignore
                    'subject': fipi_data.subject,
                    'exam_type': fipi_data.exam_type,
                    'url': fipi_data.url
                }
            except FIPIData.DoesNotExist:  # type: ignore
                return JsonResponse({
                    'success': False,
                    'error': 'Контент не найден'
                }, status=404)
        
        # Здесь должна быть логика генерации PDF
        # Пока возвращаем заглушку
        pdf_url = f"/api/premium/pdf/{content_id}/download/"
        
        return JsonResponse({
            'success': True,
            'pdf_url': pdf_url,
            'message': 'PDF успешно сгенерирован'
        })
        
    except Exception as e:
        logger.error(f"Ошибка экспорта в PDF: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка генерации PDF'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@premium_required('advanced_search')
def advanced_search(request):
    """Расширенный поиск по контенту"""
    try:
        data = json.loads(request.body)
        query = data.get('query')
        filters = data.get('filters', {})
        limit = data.get('limit', 20)
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Не указан поисковый запрос'
            }, status=400)
        
        # Отслеживаем использование
        usage_tracker = get_usage_tracker()
        if not usage_tracker.track_usage(request.user, 'advanced_searches', 1):
            return JsonResponse({
                'success': False,
                'error': 'Превышен лимит расширенного поиска',
                'code': 'ADVANCED_SEARCH_LIMIT_EXCEEDED'
            }, status=429)
        
        # Выполняем расширенный поиск
        orchestrator = get_ai_orchestrator()
        results = orchestrator.search_content(
            query=query,
            user=request.user,
            filters=filters,
            limit=limit
        )
        
        return JsonResponse({
            'success': True,
            'results': results,
            'query': query,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Ошибка расширенного поиска: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка выполнения поиска'
        }, status=500)

@require_http_methods(["GET"])
@login_required
@premium_required('personalized_recommendations')
def get_personalized_recommendations(request):
    """Получает персональные рекомендации"""
    try:
        limit = int(request.GET.get('limit', 10))
        
        # Отслеживаем использование
        usage_tracker = get_usage_tracker()
        if not usage_tracker.track_usage(request.user, 'daily_requests', 1):
            return JsonResponse({
                'success': False,
                'error': 'Превышен дневной лимит запросов',
                'code': 'DAILY_LIMIT_EXCEEDED'
            }, status=429)
        
        # Получаем персональные рекомендации
        orchestrator = get_ai_orchestrator()
        recommendations = orchestrator.get_personalized_recommendations(
            user=request.user,
            limit=limit
        )
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения рекомендаций: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка получения рекомендаций'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@premium_required('version_comparison')
def compare_versions(request):
    """Сравнивает версии документов"""
    try:
        data = json.loads(request.body)
        version1_id = data.get('version1_id')
        version2_id = data.get('version2_id')
        
        if not version1_id or not version2_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны версии для сравнения'
            }, status=400)
        
        # Отслеживаем использование
        usage_tracker = get_usage_tracker()
        if not usage_tracker.track_usage(request.user, 'daily_requests', 1):
            return JsonResponse({
                'success': False,
                'error': 'Превышен дневной лимит запросов',
                'code': 'DAILY_LIMIT_EXCEEDED'
            }, status=429)
        
        # Получаем версии для сравнения
        try:
            version1 = FIPIData.objects.get(id=version1_id)  # type: ignore
            version2 = FIPIData.objects.get(id=version2_id)  # type: ignore
        except FIPIData.DoesNotExist:  # type: ignore
            return JsonResponse({
                'success': False,
                'error': 'Одна из версий не найдена'
            }, status=404)
        
        # Выполняем сравнение
        orchestrator = get_ai_orchestrator()
        comparison = orchestrator.compare_versions(version1, version2)
        
        return JsonResponse({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Ошибка сравнения версий: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка сравнения версий'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def get_premium_features(request):
    """Получает список доступных премиум-функций"""
    try:
        access_control = get_access_control()
        user_features = access_control.get_user_features(request.user)
        
        all_features = {
            'basic': {
                'name': 'Базовый доступ',
                'description': 'Основные функции платформы',
                'available': True
            },
            'premium_content': {
                'name': 'Премиум-контент',
                'description': 'Полный доступ ко всем материалам',
                'available': 'premium_content' in user_features
            },
            'pdf_export': {
                'name': 'Экспорт в PDF',
                'description': 'Скачивание материалов в формате PDF',
                'available': 'pdf_export' in user_features
            },
            'advanced_search': {
                'name': 'Расширенный поиск',
                'description': 'Интеллектуальный поиск по контенту',
                'available': 'advanced_search' in user_features
            },
            'personalized_recommendations': {
                'name': 'Персональные рекомендации',
                'description': 'Рекомендации на основе ваших предпочтений',
                'available': 'personalized_recommendations' in user_features
            },
            'version_comparison': {
                'name': 'Сравнение версий',
                'description': 'Сравнение разных версий документов',
                'available': 'version_comparison' in user_features
            },
            'unlimited_requests': {
                'name': 'Неограниченные запросы',
                'description': 'Без ограничений на количество запросов',
                'available': 'unlimited_requests' in user_features
            },
            'priority_support': {
                'name': 'Приоритетная поддержка',
                'description': 'Быстрая техническая поддержка',
                'available': 'priority_support' in user_features
            }
        }
        
        return JsonResponse({
            'success': True,
            'features': all_features,
            'user_features': user_features
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения премиум-функций: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка получения функций'
        }, status=500)
