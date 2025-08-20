"""
Представления для модуля Telegram бота

Обрабатывает:
- Webhook от Telegram
- Панель управления ботом
- API статус бота
"""

import json
import asyncio
import logging
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from telegram import Update
from .bot_main import setup_bot_application
from bot.bot_instance import get_bot
from django.conf import settings

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """
    Обрабатывает webhook от Telegram
    
    Принимает JSON с обновлениями от Telegram API
    и передает их в обработчики бота
    """
    try:
        # Парсим JSON данные
        data = json.loads(request.body.decode('utf-8'))
        
        # Получаем экземпляр бота
        bot = get_bot()
        
        # Создаем объект Update
        update = Update.de_json(data, bot)
        
        if update:
            # Обрабатываем обновление асинхронно
            asyncio.run(handle_telegram_update(update))
            
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return HttpResponse("ERROR", status=500)


async def handle_telegram_update(update: Update):
    """
    Асинхронно обрабатывает обновление от Telegram
    
    Создает mock-контекст и вызывает соответствующие обработчики
    """
    try:
        # Импортируем обработчики
        from .bot_handlers import (
            start, subjects_menu, show_subject_topics, show_task,
            handle_answer, show_stats, voice_hint, handle_unknown_callback
        )
        
        # Создаем mock-контекст
        bot = get_bot()
        context = MockContext(bot)
        
        # Обрабатываем команды
        if update.message:
            if update.message.text:
                if update.message.text.startswith('/start'):
                    await start(update, context)
                elif update.message.text.startswith('/help'):
                    await start(update, context)
                else:
                    # Обрабатываем как ответ на задание
                    await handle_answer(update, context)
        
        # Обрабатываем callback-запросы
        elif update.callback_query:
            callback_data = update.callback_query.data
            
            if callback_data == "subjects":
                await subjects_menu(update, context)
            elif callback_data == "stats":
                await show_stats(update, context)
            elif callback_data == "random_task":
                await show_task(update, context)
            elif callback_data == "main_menu":
                await start(update, context)
            elif callback_data.startswith("subject_"):
                await show_subject_topics(update, context)
            elif callback_data.startswith("topic_"):
                await show_task(update, context)
            elif callback_data.startswith("random_subject_"):
                await show_task(update, context)
            elif callback_data.startswith("voice_"):
                await voice_hint(update, context)
            elif callback_data.startswith("answer_"):
                await show_task(update, context)
            else:
                await handle_unknown_callback(update, context)
                
    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")


class MockContext:
    """
    Mock-класс для контекста бота
    
    Имитирует ContextTypes.DEFAULT_TYPE для webhook-режима
    """
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.chat_data = {}


def is_superuser(user):
    """Проверяет, является ли пользователь суперпользователем"""
    return user.is_superuser


@user_passes_test(is_superuser)
def bot_control_panel(request):
    """
    Панель управления ботом для администраторов
    
    Показывает статус бота и позволяет управлять им
    """
    return render(request, 'telegram_bot/control_panel.html', {
        'bot_status': 'Webhook режим',
        'bot_mode': 'webhook'
    })


def bot_api_status(request):
    """
    API для проверки статуса бота
    
    Возвращает JSON с информацией о состоянии бота
    """
    token_set = bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))
    try:
        bot = get_bot()
        ok = bot is not None
    except Exception:
        ok = False
    return JsonResponse({
        'status': 'active' if ok else 'error',
        'mode': 'webhook',
        'token_configured': token_set,
        'message': 'Бот работает в режиме webhook' if ok else 'Бот недоступен, проверьте токен и webhook'
    })
