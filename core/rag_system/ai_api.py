"""
API для AI интеграции в RAG системе
"""

import logging
from typing import Dict, List, Any, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AIQueryView(View):
    """
    API для AI запросов с использованием RAG системы
    """
    
    def post(self, request):
        """POST запрос для AI обработки"""
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()
            subject = data.get('subject', '').strip()
            user_id = data.get('user_id')
            use_context = data.get('use_context', True)
            
            if not prompt:
                return JsonResponse({
                    'error': 'Поле prompt обязательно',
                    'answer': '',
                    'sources': []
                }, status=400)
            
            # Используем AI через Container
            from core.container import Container
            
            ai_orchestrator = Container.ai_orchestrator()
            
            # Получаем контекст через RAG если нужно
            context = ""
            sources = []
            
            if use_context:
                from .orchestrator import RAGOrchestrator
                rag = RAGOrchestrator()
                rag_results = rag.process_query(
                    prompt=prompt,
                    subject=subject,
                    user_id=user_id,
                    limit=5
                )
                context = rag_results.get('context', '')
                sources = rag_results.get('sources', [])
            
            # Формируем расширенный промпт с контекстом
            if context:
                enhanced_prompt = f"""
Контекст из базы знаний:
{context}

Вопрос пользователя: {prompt}
"""
            else:
                enhanced_prompt = prompt
            
            # Получаем ответ от AI
            ai_response = ai_orchestrator.ask(
                prompt=enhanced_prompt,
                user_id=user_id,
                subject=subject,
                use_context=use_context
            )
            
            # Форматируем источники
            formatted_sources = []
            for source in sources:
                formatted_sources.append({
                    'id': source.get('id'),
                    'title': source.get('title', ''),
                    'content': source.get('content', '')[:200] + '...' if len(source.get('content', '')) > 200 else source.get('content', ''),
                    'subject': source.get('subject', ''),
                    'type': source.get('type', 'task'),
                    'relevance_score': source.get('score', 0.0)
                })
            
            return JsonResponse({
                'answer': ai_response.get('answer', ''),
                'sources': formatted_sources,
                'context_used': bool(context),
                'subject': subject,
                'query': prompt,
                'timestamp': ai_response.get('timestamp'),
                'model_used': ai_response.get('model', 'unknown')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON в теле запроса',
                'answer': '',
                'sources': []
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка в AIQueryView: {e}")
            return JsonResponse({
                'error': 'Ошибка обработки AI запроса',
                'answer': '',
                'sources': []
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AIConversationView(View):
    """
    API для ведения диалога с AI
    """
    
    def post(self, request):
        """POST запрос для продолжения диалога"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
            user_id = data.get('user_id')
            subject = data.get('subject', '').strip()
            
            if not message:
                return JsonResponse({
                    'error': 'Поле message обязательно',
                    'response': '',
                    'conversation_id': conversation_id
                }, status=400)
            
            # Используем AI через Container
            from core.container import Container
            
            ai_orchestrator = Container.ai_orchestrator()
            
            # Получаем историю диалога если есть
            conversation_history = []
            if conversation_id:
                # Здесь можно реализовать получение истории из базы/кэша
                # Пока используем простую реализацию
                conversation_history = self._get_conversation_history(conversation_id)
            
            # Формируем контекст диалога
            context_prompt = self._build_conversation_context(
                message, conversation_history, subject
            )
            
            # Получаем ответ от AI
            ai_response = ai_orchestrator.ask(
                prompt=context_prompt,
                user_id=user_id,
                subject=subject,
                use_context=True
            )
            
            # Сохраняем диалог
            if not conversation_id:
                conversation_id = self._generate_conversation_id()
            
            self._save_conversation_turn(
                conversation_id, user_id, message, ai_response.get('answer', '')
            )
            
            return JsonResponse({
                'response': ai_response.get('answer', ''),
                'conversation_id': conversation_id,
                'timestamp': ai_response.get('timestamp'),
                'subject': subject
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON в теле запроса',
                'response': '',
                'conversation_id': None
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка в AIConversationView: {e}")
            return JsonResponse({
                'error': 'Ошибка обработки диалога',
                'response': '',
                'conversation_id': None
            }, status=500)
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Получение истории диалога"""
        # Простая реализация - в реальном проекте использовать Redis/БД
        return []
    
    def _build_conversation_context(self, message: str, history: List[Dict[str, str]], subject: str) -> str:
        """Построение контекста диалога"""
        context_parts = []
        
        # Добавляем предмет если указан
        if subject:
            context_parts.append(f"Предмет: {subject}")
        
        # Добавляем историю диалога
        if history:
            context_parts.append("Предыдущий диалог:")
            for turn in history[-5:]:  # Последние 5 реплик
                context_parts.append(f"Пользователь: {turn.get('user_message', '')}")
                context_parts.append(f"AI: {turn.get('ai_response', '')}")
        
        # Добавляем текущее сообщение
        context_parts.append(f"Текущий вопрос: {message}")
        
        return "\n".join(context_parts)
    
    def _generate_conversation_id(self) -> str:
        """Генерация ID диалога"""
        import uuid
        return str(uuid.uuid4())
    
    def _save_conversation_turn(self, conversation_id: str, user_id: int, message: str, response: str):
        """Сохранение реплики диалога"""
        # Простая реализация - в реальном проекте сохранять в Redis/БД
        logger.info(f"Диалог {conversation_id}: {message} -> {response[:50]}...")


@require_http_methods(["GET"])
@csrf_exempt
def ai_health_check(request):
    """
    Проверка состояния AI системы
    """
    try:
        from core.container import Container
        
        ai_orchestrator = Container.ai_orchestrator()
        
        # Проверяем доступность AI
        test_response = ai_orchestrator.ask(
            prompt="Тест",
            user_id=None,
            subject="",
            use_context=False
        )
        
        is_healthy = bool(test_response.get('answer'))
        
        return JsonResponse({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'ai_available': is_healthy,
            'model': test_response.get('model', 'unknown'),
            'timestamp': test_response.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Ошибка в ai_health_check: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'ai_available': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def ai_capabilities(request):
    """
    Получение информации о возможностях AI
    """
    try:
        capabilities = {
            'subjects': ['математика', 'русский язык'],
            'exam_types': ['ЕГЭ', 'ОГЭ'],
            'features': [
                'Решение задач',
                'Объяснение тем',
                'Проверка ответов',
                'Генерация заданий',
                'Анализ ошибок'
            ],
            'supported_formats': [
                'Текстовые вопросы',
                'Математические выражения',
                'Графики и схемы'
            ],
            'context_awareness': True,
            'conversation_mode': True
        }
        
        return JsonResponse({
            'capabilities': capabilities,
            'version': '1.0.0',
            'last_updated': '2024-01-01'
        })
        
    except Exception as e:
        logger.error(f"Ошибка в ai_capabilities: {e}")
        return JsonResponse({
            'error': 'Ошибка получения информации о возможностях'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def ai_ask(request):
    """
    Простой AI запрос (для обратной совместимости)
    """
    view = AIQueryView()
    return view.post(request)


@require_http_methods(["GET"])
@csrf_exempt
def ai_subjects(request):
    """
    Получение списка доступных предметов для AI
    """
    try:
        subjects = [
            {
                'id': 'math',
                'name': 'Математика',
                'exam_types': ['ЕГЭ', 'ОГЭ'],
                'description': 'Математика профильная и базовая'
            },
            {
                'id': 'russian',
                'name': 'Русский язык',
                'exam_types': ['ЕГЭ', 'ОГЭ'],
                'description': 'Русский язык с сочинением'
            }
        ]
        
        return JsonResponse({
            'subjects': subjects,
            'total': len(subjects)
        })
        
    except Exception as e:
        logger.error(f"Ошибка в ai_subjects: {e}")
        return JsonResponse({
            'error': 'Ошибка получения предметов'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def ai_user_profile(request):
    """
    Получение профиля пользователя для AI
    """
    try:
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'error': 'user_id обязателен'
            }, status=400)
        
        # Здесь можно получить реальный профиль пользователя
        profile = {
            'user_id': user_id,
            'subjects': ['математика', 'русский язык'],
            'preferred_exam_type': 'ЕГЭ',
            'difficulty_level': 'средний',
            'last_activity': '2024-01-01T00:00:00Z'
        }
        
        return JsonResponse({
            'profile': profile
        })
        
    except Exception as e:
        logger.error(f"Ошибка в ai_user_profile: {e}")
        return JsonResponse({
            'error': 'Ошибка получения профиля'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def ai_problem_submit(request):
    """
    Отправка задачи для решения AI
    """
    try:
        data = json.loads(request.body)
        problem_text = data.get('problem', '').strip()
        subject = data.get('subject', '').strip()
        user_id = data.get('user_id')
        
        if not problem_text:
            return JsonResponse({
                'error': 'Поле problem обязательно',
                'solution': '',
                'steps': []
            }, status=400)
        
        # Используем AI для решения задачи
        from core.container import Container
        
        ai_orchestrator = Container.ai_orchestrator()
        
        prompt = f"""
Реши задачу по предмету {subject}:

{problem_text}

Дай пошаговое решение с объяснениями.
"""
        
        ai_response = ai_orchestrator.ask(
            prompt=prompt,
            user_id=user_id,
            subject=subject,
            use_context=True
        )
        
        return JsonResponse({
            'solution': ai_response.get('answer', ''),
            'steps': [],  # Можно разбить ответ на шаги
            'subject': subject,
            'problem': problem_text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Неверный JSON в теле запроса',
            'solution': '',
            'steps': []
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка в ai_problem_submit: {e}")
        return JsonResponse({
            'error': 'Ошибка решения задачи',
            'solution': '',
            'steps': []
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def ai_statistics(request):
    """
    Получение статистики использования AI
    """
    try:
        stats = {
            'total_queries': 0,
            'queries_by_subject': {
                'математика': 0,
                'русский язык': 0
            },
            'queries_by_exam_type': {
                'ЕГЭ': 0,
                'ОГЭ': 0
            },
            'average_response_time': 0.0,
            'success_rate': 100.0
        }
        
        return JsonResponse({
            'statistics': stats,
            'period': 'all_time'
        })
        
    except Exception as e:
        logger.error(f"Ошибка в ai_statistics: {e}")
        return JsonResponse({
            'error': 'Ошибка получения статистики'
        }, status=500)
