"""
Views для Telegram Web App
"""

import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core.container import Container
from learning.models import Subject, Task

logger = logging.getLogger(__name__)


def webapp_home(request):
    """Главная страница Telegram Web App"""
    context = {
        'page_title': 'ExamFlow Bot',
        'is_webapp': True
    }
    return render(request, 'telegram_webapp/home.html', context)


def webapp_subjects(request):
    """Страница предметов в Web App"""
    subjects = Subject.objects.filter(is_archived=False)[:10]  # type: ignore
    
    context = {
        'page_title': 'Предметы',
        'subjects': subjects,
        'is_webapp': True
    }
    return render(request, 'telegram_webapp/subjects.html', context)


def webapp_ai_chat(request):
    """Страница ИИ-чата в Web App"""
    context = {
        'page_title': 'ИИ-помощник',
        'is_webapp': True
    }
    return render(request, 'telegram_webapp/ai_chat.html', context)


def webapp_stats(request):
    """Страница статистики в Web App"""
    try:
        subjects_count = Subject.objects.count()  # type: ignore
        tasks_count = Task.objects.count()  # type: ignore
        
        context = {
            'page_title': 'Статистика',
            'subjects_count': subjects_count,
            'tasks_count': tasks_count,
            'is_webapp': True
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
        context = {
            'page_title': 'Статистика',
            'subjects_count': 0,
            'tasks_count': 0,
            'is_webapp': True,
            'error': 'Ошибка загрузки данных'
        }
    
    return render(request, 'telegram_webapp/stats.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def webapp_ai_api(request):
    """API для ИИ в Web App"""
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({
                'success': False,
                'error': 'Пустой запрос'
            })
        
        # Ограничиваем длину запроса
        if len(prompt) > 1000:
            return JsonResponse({
                'success': False,
                'error': 'Слишком длинный вопрос (максимум 1000 символов)'
            })
        
        # Получаем ответ от ИИ
        ai_orchestrator = Container.ai_orchestrator()
        response_data = ai_orchestrator.ask(prompt)
        
        answer = response_data.get('answer', 'Не удалось получить ответ')
        
        # Ограничиваем длину ответа для Web App
        if len(answer) > 2000:
            answer = answer[:2000] + "..."
        
        return JsonResponse({
            'success': True,
            'answer': answer,
            'processing_time': response_data.get('processing_time', 0)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        })
    except Exception as e:
        logger.error(f"Ошибка в webapp_ai_api: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Ошибка сервера'
        })
