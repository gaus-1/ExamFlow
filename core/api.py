"""
API для интеграции RAG-системы с фронтендом
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from core.rag_system.orchestrator import RAGOrchestrator
from core.rag_system.vector_store import VectorStore

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AIQueryView(View):
    """
    API для обработки запросов к AI
    """

    def __init__(self):
        super().__init__()
        self.orchestrator = RAGOrchestrator()

    def post(self, request):
        """
        Обрабатывает запрос пользователя
        """
        try:
            # Парсим JSON данные
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            user_id = data.get('user_id')

            if not query:
                return JsonResponse({
                    'error': 'Пустой запрос',
                    'answer': 'Пожалуйста, задайте вопрос по подготовке к ЕГЭ.'
                }, status=400)

            logger.info(f"Получен запрос от пользователя {user_id}: {query[:100]}...")

            # Обрабатываем запрос через оркестратор
            response = self.orchestrator.process_query(query, user_id)

            logger.info(f"Запрос обработан успешно для пользователя {user_id}")
            return JsonResponse(response)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON',
                'answer': 'Произошла ошибка при обработке запроса.'
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка в AIQueryView: {e}")
            return JsonResponse({
                'error': str(e),
                'answer': 'Произошла ошибка при обработке запроса. Попробуйте позже.'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VectorStoreStatsView(View):
    """
    API для получения статистики векторного хранилища
    """

    def get(self, request):
        """
        Возвращает статистику векторного хранилища
        """
        try:
            vector_store = VectorStore()
            stats = vector_store.get_statistics()

            return JsonResponse({
                'status': 'success',
                'data': stats
            })

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SearchView(View):
    """
    API для семантического поиска
    """

    def post(self, request):
        """
        Выполняет семантический поиск
        """
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            limit = data.get('limit', 5)

            if not query:
                return JsonResponse({
                    'error': 'Пустой запрос поиска'
                }, status=400)

            vector_store = VectorStore()
            results = vector_store.search(query, limit=limit)

            return JsonResponse({
                'status': 'success',
                'query': query,
                'results': results,
                'total': len(results)
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """
    API для проверки состояния системы
    """

    def get(self, request):
        """
        Проверяет состояние всех компонентов системы
        """
        try:
            health_status = {
                'status': 'healthy',
                'components': {},
                'timestamp': None
            }

            # Проверяем векторное хранилище
            try:
                vector_store = VectorStore()
                stats = vector_store.get_statistics()
                health_status['components']['vector_store'] = {
                    'status': 'healthy',
                    'stats': stats
                }
            except Exception as e:
                health_status['components']['vector_store'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'

            # Проверяем оркестратор
            try:
                RAGOrchestrator()
                health_status['components']['orchestrator'] = {
                    'status': 'healthy'
                }
            except Exception as e:
                health_status['components']['orchestrator'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'

            from django.utils import timezone
            health_status['timestamp'] = timezone.now().isoformat()

            return JsonResponse(health_status)

        except Exception as e:
            logger.error(f"Ошибка при проверке состояния: {e}")
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e)
            }, status=500)


# Legacy API functions for backward compatibility
def get_random_task(request):
    """Legacy API - returns random task"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def get_subjects(request):
    """Legacy API - returns subjects"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def get_tasks_by_subject(request, subject_id):
    """Legacy API - returns tasks by subject"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def get_task_by_id(request, task_id):
    """Legacy API - returns task by ID"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def search_tasks(request):
    """Legacy API - searches tasks"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def get_topics(request):
    """Legacy API - returns topics"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def get_statistics(request):
    """Legacy API - returns statistics"""
    return JsonResponse({'error': 'API deprecated'}, status=410)


def create_subscription(request):
    """Legacy API - creates subscription"""
    return JsonResponse({'error': 'API deprecated'}, status=410)
