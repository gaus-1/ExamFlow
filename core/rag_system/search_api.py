"""
API для семантического поиска в RAG системе
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
import json

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class FipiSearchAPIView(View):
    """
    API для семантического поиска по ФИПИ заданиям
    """
    
    def get(self, request):
        """GET запрос для поиска"""
        try:
            query = request.GET.get('q', '').strip()
            subject = request.GET.get('subject', '').strip()
            page = int(request.GET.get('page', 1))
            limit = min(int(request.GET.get('limit', 10)), 50)
            
            if not query:
                return JsonResponse({
                    'error': 'Параметр q (запрос) обязателен',
                    'results': [],
                    'total': 0,
                    'page': page,
                    'limit': limit
                }, status=400)
            
            # Используем RAG систему для поиска
            from .orchestrator import RAGOrchestrator
            
            rag = RAGOrchestrator()
            results = rag.process_query(
                prompt=query,
                subject=subject,
                limit=limit
            )
            
            # Форматируем результаты для API
            formatted_results = []
            for source in results.get('sources', []):
                formatted_results.append({
                    'id': source.get('id'),
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'subject': source.get('subject', ''),
                    'type': source.get('type', 'task'),
                    'relevance_score': source.get('score', 0.0)
                })
            
            # Пагинация
            paginator = Paginator(formatted_results, limit)
            page_obj = paginator.get_page(page)
            
            return JsonResponse({
                'results': list(page_obj.object_list),
                'total': paginator.count,
                'page': page,
                'limit': limit,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'context': results.get('context', ''),
                'query': query,
                'subject': subject
            })
            
        except Exception as e:
            logger.error(f"Ошибка в FipiSearchAPI: {e}")
            return JsonResponse({
                'error': 'Внутренняя ошибка сервера',
                'results': [],
                'total': 0
            }, status=500)
    
    def post(self, request):
        """POST запрос для расширенного поиска"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            subject = data.get('subject', '').strip()
            filters = data.get('filters', {})
            page = int(data.get('page', 1))
            limit = min(int(data.get('limit', 10)), 50)
            
            if not query:
                return JsonResponse({
                    'error': 'Поле query обязательно',
                    'results': [],
                    'total': 0
                }, status=400)
            
            # Используем RAG систему
            from .orchestrator import RAGOrchestrator
            
            rag = RAGOrchestrator()
            results = rag.process_query(
                prompt=query,
                subject=subject,
                limit=limit * 2  # Получаем больше для фильтрации
            )
            
            # Применяем фильтры
            filtered_results = []
            for source in results.get('sources', []):
                # Фильтр по типу
                if 'type' in filters and source.get('type') != filters['type']:
                    continue
                
                # Фильтр по предмету
                if 'subject' in filters and filters['subject'].lower() not in source.get('subject', '').lower():
                    continue
                
                # Фильтр по сложности
                if 'difficulty' in filters:
                    task_difficulty = source.get('difficulty', 'средний')
                    if task_difficulty != filters['difficulty']:
                        continue
                
                filtered_results.append({
                    'id': source.get('id'),
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'subject': source.get('subject', ''),
                    'type': source.get('type', 'task'),
                    'difficulty': source.get('difficulty', 'средний'),
                    'relevance_score': source.get('score', 0.0)
                })
                
                if len(filtered_results) >= limit:
                    break
            
            # Пагинация
            paginator = Paginator(filtered_results, limit)
            page_obj = paginator.get_page(page)
            
            return JsonResponse({
                'results': list(page_obj.object_list),
                'total': paginator.count,
                'page': page,
                'limit': limit,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'context': results.get('context', ''),
                'query': query,
                'subject': subject,
                'filters_applied': filters
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON в теле запроса',
                'results': [],
                'total': 0
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка в FipiSearchAPI POST: {e}")
            return JsonResponse({
                'error': 'Внутренняя ошибка сервера',
                'results': [],
                'total': 0
            }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def fipi_semantic_search(request):
    """
    Простая функция для семантического поиска (для обратной совместимости)
    """
    try:
        query = request.GET.get('q', '').strip()
        subject = request.GET.get('subject', '').strip()
        
        if not query:
            return JsonResponse({
                'error': 'Параметр q обязателен',
                'results': []
            }, status=400)
        
        # Используем RAG систему
        from .orchestrator import RAGOrchestrator
        
        rag = RAGOrchestrator()
        results = rag.process_query(
            prompt=query,
            subject=subject,
            limit=10
        )
        
        return JsonResponse({
            'results': results.get('sources', []),
            'context': results.get('context', ''),
            'query': query,
            'subject': subject
        })
        
    except Exception as e:
        logger.error(f"Ошибка в fipi_semantic_search: {e}")
        return JsonResponse({
            'error': 'Ошибка поиска',
            'results': []
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def search_suggestions(request):
    """
    API для получения предложений поиска
    """
    try:
        query = request.GET.get('q', '').strip().lower()
        
        if len(query) < 2:
            return JsonResponse({
                'suggestions': [],
                'query': query
            })
        
        # Получаем популярные запросы из кэша или базы
        suggestions = []
        
        # Простые предложения на основе ключевых слов
        math_keywords = ['математика', 'алгебра', 'геометрия', 'функция', 'уравнение', 'график']
        russian_keywords = ['русский', 'сочинение', 'изложение', 'орфография', 'пунктуация']
        
        all_keywords = math_keywords + russian_keywords
        
        for keyword in all_keywords:
            if keyword.startswith(query) and keyword not in suggestions:
                suggestions.append(keyword)
                if len(suggestions) >= 5:
                    break
        
        return JsonResponse({
            'suggestions': suggestions,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Ошибка в search_suggestions: {e}")
        return JsonResponse({
            'suggestions': [],
            'query': query or ''
        })
