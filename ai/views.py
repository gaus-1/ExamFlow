from .models import AiLimit  # для получения лимитов
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging
from django_ratelimit.decorators import ratelimit
import re

logger = logging.getLogger(__name__)

# Сервис ИИ: провайдеры, кэш и лимиты
ai_service = None


def get_ai_service():
    """Получает или создает экземпляр AiService"""
    global ai_service
    if ai_service is None:
        try:
            from .services import AiService
            ai_service = AiService()
            logger.info("AiService успешно создан")
        except Exception as e:
            logger.error(f"Ошибка создания AiService: {e}")
            return None
    return ai_service


# ========================================
# ОСНОВНЫЕ СТРАНИЦЫ ИИ
# ========================================

def ai_dashboard(request):
    """Главная страница ИИ-ассистента"""
    context = {
        'title': 'ИИ-ассистент ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/dashboard.html', context)


def ai_chat(request):
    """Страница чата с ИИ"""
    try:
        context = {
            'title': 'Чат с ИИ - ExamFlow',
            'user': request.user,
        }
        return render(request, 'ai/chat.html', context)
    except Exception as e:  # type: ignore
        # Мягкий fallback: не отдаём 500, показываем информативную страницу
        logger.error(f"Ошибка рендера страницы чата: {e}")
        context = {
            'title': 'Чат с ИИ - ExamFlow',
            'user': request.user,
            'error_message': 'Временная ошибка загрузки чата ИИ. Повторите попытку через минуту.',
        }
        return render(request, 'ai/chat.html', context)


def ai_explain(request):
    """Страница объяснения тем ИИ"""
    context = {
        'title': 'Объяснение тем - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/explain.html', context)


def ai_search(request):
    """Страница поиска заданий ИИ"""
    context = {
        'title': 'Поиск заданий - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/search.html', context)


def ai_generate(request):
    """Страница генерации заданий ИИ"""
    context = {
        'title': 'Генерация заданий - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/generate.html', context)


# ========================================
# API ДЛЯ ИИ
# ========================================

@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='20/m', block=True)
def api_chat(request):
    """API для чата с ИИ"""
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return JsonResponse({'error': 'Пустой запрос'}, status=400)

        # Гарантируем наличие session_id для гостей
        if not request.session.session_key:
            request.session.save()
        session_id = request.session.session_key

        ai_service_instance = get_ai_service()
        if ai_service_instance is None:
            return JsonResponse({'error': 'ИИ временно недоступен'}, status=503)

        result = ai_service_instance.ask(
            prompt=prompt,
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id)
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=429)

        text = result.get('response', '') or ''
        # Источники: извлекаем URL из текста ответа (если присутствуют)
        url_pattern = re.compile(r"https?://\S+", re.IGNORECASE)
        found_urls = url_pattern.findall(text)
        sources = []
        seen = set()
        for idx, url in enumerate(found_urls, start=1):
            if url in seen:
                continue
            seen.add(url)
            sources.append({
                'id': idx,
                'title': url,
                'url': url
            })

        # Follow-ups: простые действия в экосистеме
        followups = [
            {
                'label': 'Показать задания по предметам',
                'href': '/learning/subjects/'
            },
            {
                'label': 'Случайное задание',
                'href': '/learning/random/'
            },
            {
                'label': 'Задать уточняющий вопрос',
                'action': 'refocus-input'
            }
        ]

        return JsonResponse({
            'response': text,
            'provider': result.get('provider', 'local'),
            'cached': result.get('cached', False),
            'tokens_used': result.get('tokens_used', 0),
            'cost': 0.0,
            'sources': sources,
            'followups': followups
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка в API чата: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='30/m', block=True)
def api_explain(request):
    """API для объяснения тем ИИ"""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '')

        if not topic:
            return JsonResponse({'error': 'Не указана тема'}, status=400)

        # TODO: Реализовать логику объяснения
        explanation = f"Объяснение темы '{topic}' находится в разработке. Скоро здесь будет подробное объяснение с примерами."

        return JsonResponse({
            'explanation': explanation,
            'tokens_used': len(topic.split()),
            'cost': 0.0
        })

    except Exception as e:
        logger.error(f"Ошибка в API объяснения: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='30/m', block=True)
def api_search(request):
    """API для поиска заданий ИИ"""
    try:
        data = json.loads(request.body)
        query = data.get('query', '')

        if not query:
            return JsonResponse({'error': 'Пустой поисковый запрос'}, status=400)

        # TODO: Реализовать логику поиска
        results = [
            {
                'id': 1,
                'title': f'Задание по запросу "{query}"',
                'description': 'Описание задания находится в разработке',
                'subject': 'Математика',
                'difficulty': 'Средний'
            }
        ]

        return JsonResponse({
            'results': results,
            'total': len(results),
            'tokens_used': len(query.split()),
            'cost': 0.0
        })

    except Exception as e:
        logger.error(f"Ошибка в API поиска: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='15/m', block=True)
def api_generate(request):
    """API для генерации заданий ИИ"""
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '')
        difficulty = data.get('difficulty', 'medium')

        if not topic:
            return JsonResponse({'error': 'Не указана тема'}, status=400)

        # TODO: Реализовать логику генерации
        generated_task = {
            'title': f'Сгенерированное задание по теме "{topic}"',
            'content': f'Содержание задания по теме "{topic}" с уровнем сложности "{difficulty}" находится в разработке.',
            'answer': 'Ответ будет доступен после реализации функционала',
            'explanation': 'Подробное объяснение решения будет добавлено позже'}

        return JsonResponse({
            'task': generated_task,
            'tokens_used': len(topic.split()),
            'cost': 0.0
        })

    except Exception as e:
        logger.error(f"Ошибка в API генерации: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


# ========================================
# УПРАВЛЕНИЕ ЛИМИТАМИ
# ========================================

def ai_limits(request):
    """Страница управления лимитами ИИ"""
    context = {
        'title': 'Лимиты ИИ - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/limits.html', context)


@csrf_exempt
@require_http_methods(["GET"])
@ratelimit(key='ip', rate='60/m', block=True)
def api_limits(request):
    """API для получения лимитов пользователя"""
    try:
        # Показываем лимиты и гостям (10/день), авторизованным (30/день)
        is_auth = request.user.is_authenticated
        if not request.session.session_key:
            request.session.save()
        session_id = None if is_auth else request.session.session_key

        max_daily = 30 if is_auth else 10
        limit, _ = AiLimit.objects.get_or_create(  # type: ignore
            user=request.user if is_auth else None,
            session_id=session_id,
            limit_type='daily',
            defaults={
                'current_usage': 0,
                'max_limit': max_daily,
                'reset_date': timezone.now().date(),  # type: ignore
            }
        )
        # Синхронизируем максимальный лимит на случай смены статуса
        if limit.max_limit != max_daily:
            limit.max_limit = max_daily
            limit.save()

        remaining = max(0, limit.max_limit - limit.current_usage)
        return JsonResponse({
            'daily': {
                'used': limit.current_usage,
                'max': limit.max_limit,
                'remaining': remaining
            }
        })

    except Exception as e:
        logger.error(f"Ошибка в API лимитов: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


# ========================================
# ГОЛОСОВОЙ ПОМОЩНИК
# ========================================

def voice_assistant(request):
    """Страница голосового помощника"""
    context = {
        'title': 'Голосовой помощник - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/voice.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_voice(request):
    """API для голосового помощника"""
    try:
        data = json.loads(request.body)
        audio_data = data.get('audio', '')
        command = data.get('command', '')

        if not audio_data and not command:
            return JsonResponse(
                {'error': 'Не переданы аудио данные или команда'}, status=400)

        # TODO: Реализовать логику голосового помощника
        response = {
            'text': f'Голосовой помощник получил команду: "{command}". Функционал находится в разработке.',
            'audio_url': None}

        return JsonResponse(response)

    except Exception as e:
        logger.error(f"Ошибка в API голосового помощника: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


# ========================================
# АДМИНИСТРАТИВНЫЕ ФУНКЦИИ
# ========================================

@staff_member_required
def admin_providers(request):
    """Административная страница управления провайдерами ИИ"""
    context = {
        'title': 'Управление провайдерами ИИ - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/admin/providers.html', context)


@staff_member_required
def admin_templates(request):
    """Административная страница управления шаблонами промптов"""
    context = {
        'title': 'Управление шаблонами промптов - ExamFlow',
        'user': request.user,
    }
    return render(request, 'ai/admin/templates.html', context)
