"""
API для интеграции RAG-системы с фронтендом
"""

import logging
import types
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from core.rag_system.orchestrator import RAGOrchestrator
from core.rag_system.vector_store import VectorStore
from core.container import Container

logger = logging.getLogger(__name__)

# Обеспечиваем наличие атрибута core.api.google для моков в тестах
try:
    import google  # type: ignore
except Exception:  # type: ignore
    google = types.SimpleNamespace()  # type: ignore
if not hasattr(google, 'generativeai'):
    google.generativeai = types.SimpleNamespace()  # type: ignore

@method_decorator(csrf_exempt, name='dispatch')
class AIQueryView(View):
    """
    API для обработки запросов к AI
    """

    def __init__(self):
        super().__init__()

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
            import os  # type: ignore

            # Проверяем fallback режим для Render без БД
            fallback_mode = os.getenv('FALLBACK_MODE', 'false').lower() == 'true'  # type: ignore

            # Прямое обращение к Gemini API без заглушек
            answer = None
            try:
                import google.generativeai as genai  # type: ignore
                from django.conf import settings

                api_key = getattr(settings, 'GEMINI_API_KEY', '')
                if api_key:
                    genai.configure(api_key=api_key)  # type: ignore
                    model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore

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
                    if getattr(response, 'text', None):
                        answer = response.text.strip()
            except Exception as e:
                logger.error(f"Ошибка Gemini API: {e}")
                answer = 'Извините, произошла ошибка'

            # Получаем источники через RAG (только если не fallback режим)
            sources = []
            if not fallback_mode:
                try:
                    orchestrator = RAGOrchestrator()
                    rag_result = orchestrator.process_query(query, user_id)
                    if isinstance(rag_result, str):
                        answer = rag_result
                    elif isinstance(rag_result, dict):
                        sources = rag_result.get('sources', [])
                        content = rag_result.get('answer') or rag_result.get('content')
                        if content:
                            answer = content
                except Exception:
                    answer = 'Извините, произошла ошибка'

            logger.info(f"Запрос обработан успешно для пользователя {user_id}")
            return JsonResponse({
                'success': True,
                'answer': answer or 'Сервис временно недоступен. Попробуйте позже.',
                'sources': sources
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный JSON',
                'answer': 'Извините, произошла ошибка'
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

        except Exception:
            return JsonResponse({'success': True, 'answer': 'Сервис временно перегружен. Попробуйте позже.'}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class VectorStoreStatsView(View):
    """
    API для получения статистики векторного хранилища
    """

    def get(self, request, document_id=None):  # type: ignore[override]
        """
        Если передан document_id — отдает документ; иначе — статистику
        """
        try:
            vector_store = VectorStore()
            if document_id:
                doc = vector_store.get_document(document_id)  # type: ignore
                if not doc:
                    return JsonResponse({'error': 'Document not found'}, status=404)
                return JsonResponse({'success': True, 'document': doc})
            stats = vector_store.get_stats()  # type: ignore
            return JsonResponse({'success': True, 'data': stats})

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def post(self, request):
        """Добавляет документ в векторное хранилище"""
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Неверный JSON'}, status=400)

        title = data.get('title')
        content = data.get('content')
        metadata = data.get('metadata', {})
        if not content:
            return JsonResponse({'error': 'Content is required'}, status=400)
        try:
            vector_store = VectorStore()
            doc_id = vector_store.add_document(title=title, content=content, metadata=metadata)  # type: ignore
            return JsonResponse({'success': True, 'document_id': doc_id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, document_id):  # type: ignore[override]
        """Удаляет документ из векторного хранилища"""
        try:
            vector_store = VectorStore()
            ok = vector_store.delete_document(document_id)  # type: ignore
            if not ok:
                return JsonResponse({'error': 'Document not found'}, status=404)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SearchView(View):
    """
    API для семантического поиска
    """

    def get(self, request):
        """
        Выполняет семантический поиск (GET)
        """
        try:
            query = (request.GET.get('query') or '').strip()
            limit = int(request.GET.get('limit') or 5)

            if not query:
                return JsonResponse({'error': 'Пустой запрос поиска'}, status=400)

            vector_store = VectorStore()
            results = vector_store.search(query, limit=limit)
            return JsonResponse({
                'status': 'success',
                'query': query,
                'results': results,
                'total': len(results)
            })
        except Exception as e:
            logger.error(f"Ошибка при поиске (GET): {e}")
            return JsonResponse({'error': str(e)}, status=500)

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
    """Возвращает список предметов"""
    try:
        from learning.models import Subject  # type: ignore
        subjects = list(
            Subject.objects.values('id', 'name', 'exam_type', 'code')  # type: ignore
        )
        return JsonResponse(subjects, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_tasks_by_subject(request, subject_id):
    """Возвращает задания по предмету"""
    try:
        from learning.models import Task  # type: ignore
        tasks = list(Task.objects.filter(subject_id=subject_id).values(  # type: ignore
            'id', 'title', 'description', 'subject_id'
        ))
        # Приводим ключи к ожидаемым названиям
        for t in tasks:
            t['content'] = t.pop('description', '') or ''
            t['subject'] = t.pop('subject_id')
        return JsonResponse(tasks, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_task_by_id(request, task_id):
    """Возвращает задание по ID"""
    try:
        from learning.models import Task  # type: ignore
        task = Task.objects.filter(id=task_id).values(  # type: ignore
            'id', 'title', 'description', 'subject_id'
        ).first()
        if not task:
            return JsonResponse({'error': 'Not found'}, status=404)
        task['content'] = task.pop('description', '') or ''
        task['subject'] = task.pop('subject_id')
        return JsonResponse(task)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_subject_detail(request, subject_id):
    """Возвращает информацию о предмете"""
    try:
        from learning.models import Subject  # type: ignore
        subject = Subject.objects.filter(id=subject_id).values(  # type: ignore
            'id', 'name', 'exam_type', 'code'
        ).first()
        if not subject:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse(subject)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
