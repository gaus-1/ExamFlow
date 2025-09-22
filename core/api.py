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
from core.container import Container

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

            # Прямое обращение к Gemini API без заглушек
            try:
                import google.generativeai as genai
                from django.conf import settings
                
                api_key = getattr(settings, 'GEMINI_API_KEY', '')
                if api_key:
                    genai.configure(api_key=api_key) # type: ignore
                    model = genai.GenerativeModel('gemini-1.5-flash') # type: ignore
                    
                    # Системный промпт для ExamFlow
                    system_prompt = """Ты - ExamFlow AI, эксперт по подготовке к ЕГЭ и ОГЭ.
                    
                    Специализируешься на:
                    📐 Математике (профильная и базовая, ОГЭ) - уравнения, функции, геометрия, алгебра
                    📝 Русском языке (ЕГЭ и ОГЭ) - грамматика, орфография, сочинения, литература
                    
                    Стиль общения:
                    - Краткий и конкретный ответ (до 400 слов)
                    - Пошаговые решения для математики
                    - Примеры и образцы для русского языка
                    - НЕ упоминай провайдера ИИ
                    """
                    
                    full_prompt = f"{system_prompt}\n\nВопрос: {query}"
                    response = model.generate_content(full_prompt)
                    
                    if response.text:
                        answer = response.text.strip()
                    else:
                        answer = "Не удалось получить ответ. Попробуйте переформулировать вопрос."
                else:
                    answer = "API ключ не настроен. Обратитесь к администратору."
                    
            except Exception as e:
                logger.error(f"Ошибка Gemini API: {e}")
                answer = "Сервис временно недоступен. Попробуйте позже."

            # Получаем источники через RAG
            try:
                rag_result = self.orchestrator.process_query(query, user_id)
                sources = rag_result.get('sources', [])
            except Exception:
                sources = []

            logger.info(f"Запрос обработан успешно для пользователя {user_id}")
            return JsonResponse({
                'success': True,
                'answer': answer,
                'sources': sources
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный JSON',
                'answer': 'Произошла ошибка при обработке запроса.'
            }, status=200)
        except Exception as e:
            logger.error(f"Ошибка в AIQueryView: {e}")
            # Возвращаем безопасный ответ 200, чтобы фронт не падал
            return JsonResponse({
                'success': True,
                'answer': 'Я ExamFlow AI! Задайте вопрос по математике или русскому языку для ЕГЭ/ОГЭ.',
                'sources': []
            }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class EmergencyAIView(View):
    """
    Экстренный (fallback) API для ИИ, используется старым фронтендом по пути /ai/emergency/
    Возвращает быстрый краткий ответ без сложного контекста.
    """

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
            query = (data.get('query') or data.get('prompt') or '').strip()

            if not query:
                return JsonResponse({'success': False, 'error': 'Пустой запрос'}, status=400)

            # Мгновенный краткий ответ через оркестратор контейнера
            try:
                ai = Container.ai_orchestrator()
                ai_result = ai.ask(prompt=query)  # type: ignore
                answer = ai_result.get('answer') if isinstance(ai_result, dict) else None
            except Exception:
                answer = None

            if not answer:
                answer = 'Ваш запрос принят. Попробуйте сформулировать его точнее по математике или русскому языку.'

            return JsonResponse({'success': True, 'answer': answer}, status=200)

        except Exception as e:
            return JsonResponse({'success': True, 'answer': 'Сервис временно перегружен. Попробуйте позже.'}, status=200)

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
            stats = vector_store.get_stats() # type: ignore

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
                stats = vector_store.get_stats() # type: ignore
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

            return JsonResponse(health_status, status=200)

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
