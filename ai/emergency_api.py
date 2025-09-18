"""
Экстренный AI API - работает БЕЗ базы данных
Используется когда основная система недоступна
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def emergency_ai_api(request):
    """
    Экстренный AI API - прямое подключение к Gemini
    Работает БЕЗ базы данных, БЕЗ Container, БЕЗ сложных зависимостей
    """
    try:
        logger.info("🚨 ЭКСТРЕННЫЙ AI API активирован")
        
        # Получаем данные
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({
                'answer': 'Пожалуйста, введите вопрос',
                'sources': []
            })
        
        if len(prompt) > 1000:
            return JsonResponse({
                'answer': 'Вопрос слишком длинный. Максимум 1000 символов.',
                'sources': []
            })
        
        # Прямое подключение к Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return JsonResponse({
                'answer': 'Сервис ИИ временно недоступен. Попробуйте позже.',
                'sources': [
                    {'title': 'ФИПИ - Русский язык', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-1'},
                    {'title': 'ФИПИ - Математика', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-4'}
                ]
            })
        
        # Настраиваем Gemini
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
        
        # Создаем промпт с ролью
        system_prompt = """Ты - ExamFlow AI, дружелюбный помощник для подготовки к ЕГЭ и ОГЭ.

Специализируешься на:
📐 Математике (профильная и базовая, ОГЭ) 
📝 Русском языке (ЕГЭ и ОГЭ)

Стиль общения:
- Дружелюбный и поддерживающий
- Иногда добавляй уместные шутки
- Представляйся как "ExamFlow AI"
- Помогай конкретными примерами
- Если вопрос не по твоим предметам - вежливо перенаправь на математику или русский

Отвечай кратко и по делу, максимум 300 слов."""

        full_prompt = f"{system_prompt}\n\nВопрос студента: {prompt}"
        
        # Получаем ответ
        response = model.generate_content(full_prompt)
        
        if response.text:
            answer = response.text.strip()
            
            # Ограничиваем длину ответа
            if len(answer) > 1500:
                answer = answer[:1500] + "..."
            
            logger.info(f"✅ Экстренный AI ответ получен: {answer[:50]}...")
            
            return JsonResponse({
                'answer': answer,
                'sources': [
                    {'title': 'ФИПИ - Русский язык', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-1'},
                    {'title': 'ФИПИ - Математика', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-4'}
                ]
            })
        else:
            return JsonResponse({
                'answer': 'Не удалось получить ответ от ИИ. Попробуйте переформулировать вопрос.',
                'sources': []
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'answer': 'Ошибка формата запроса',
            'sources': []
        })
    except Exception as e:
        logger.error(f"Экстренный AI API ошибка: {e}")
        return JsonResponse({
            'answer': 'Извините, произошла техническая ошибка. Попробуйте позже или воспользуйтесь материалами ФИПИ.',
            'sources': [
                {'title': 'ФИПИ - Русский язык', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-1'},
                {'title': 'ФИПИ - Математика', 'url': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory#!/tab/151883967-4'},
                {'title': 'Решу ЕГЭ - Русский', 'url': 'https://rus-ege.sdamgia.ru/'},
                {'title': 'Решу ЕГЭ - Математика', 'url': 'https://ege.sdamgia.ru/'}
            ]
        })
