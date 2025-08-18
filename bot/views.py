import json
import asyncio
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from telegram import Update
from telegram.ext import Application

logger = logging.getLogger(__name__)

def bot_control_panel(request):
    """Панель управления ботом"""
    return render(request, 'bot/panel.html', {
        'status': 'webhook',
        'mode': 'Webhook режим'
    })

def bot_api_status(request):
    """API для получения статуса бота"""
    return JsonResponse({
        'status': 'webhook',
        'mode': 'Webhook режим',
        'url': f"{settings.SITE_URL}/bot/webhook/"
    })


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Webhook для обработки обновлений от Telegram"""
    try:
        # Получаем данные из запроса
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f"Получено обновление от Telegram: {data}")
        
        # Получаем экземпляр бота
        from bot.bot_instance import get_bot
        bot = get_bot()
        if not bot:
            logger.error("Не удалось получить экземпляр бота")
            return HttpResponse("bot error", status=500)
        
        # Создаем объект Update
        update = Update.de_json(data, bot)
        
        if update:
            # Запускаем обработку в асинхронном режиме
            asyncio.run(handle_telegram_update(update))
        
        return HttpResponse("ok")
        
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON от Telegram")
        return HttpResponse("error", status=400)
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {str(e)}")
        return HttpResponse("error", status=500)


async def handle_telegram_update(update: Update):
    """Асинхронная обработка обновления от Telegram"""
    try:
        # Импортируем обработчики из bot.py
        from bot.bot import (
            start, subjects_menu, subject_detail, solve_subject_tasks,
            random_task, random_subject_task, show_answer, mark_correct,
            mark_incorrect, mark_understood, mark_not_understood, about,
            progress, rating, subscription_menu, voice_hint, handle_unknown_callback
        )
        
        # Получаем экземпляр бота для контекста
        from bot.bot_instance import get_bot
        bot = get_bot()
        
        # Создаем контекст (заглушка для совместимости)
        class MockContext:
            def __init__(self, bot):
                self.bot = bot
                self.user_data = {}
                self.bot_data = {}
                self.chat_data = {}
        
        context = MockContext(bot)
        
        # Обрабатываем команды
        if update.message:
            if update.message.text == '/start':
                start(update, context)
                return
        
        # Обрабатываем callback queries
        if update.callback_query:
            callback_data = update.callback_query.data
            
            handlers = {
                'subjects': subjects_menu,
                'main_menu': start,
                'about': about,
                'progress': progress,
                'rating': rating,
                'subscription': subscription_menu,
                'voice_hint': voice_hint,
                'random_task': random_task,
            }
            
            # Обработчики с параметрами
            if callback_data.startswith('subject_'):
                subject_detail(update, context)
            elif callback_data.startswith('solve_'):
                solve_subject_tasks(update, context)
            elif callback_data.startswith('random_subject_'):
                random_subject_task(update, context)
            elif callback_data.startswith('answer_'):
                show_answer(update, context)
            elif callback_data.startswith('correct_'):
                mark_correct(update, context)
            elif callback_data.startswith('incorrect_'):
                mark_incorrect(update, context)
            elif callback_data.startswith('understood_'):
                mark_understood(update, context)
            elif callback_data.startswith('not_understood_'):
                mark_not_understood(update, context)
            elif callback_data in handlers:
                handlers[callback_data](update, context)
            else:
                handle_unknown_callback(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_telegram_update: {str(e)}")
        
        # Отправляем сообщение об ошибке пользователю
        try:
            if update.callback_query:
                asyncio.run(update.callback_query.edit_message_text(
                    "❌ Произошла ошибка. Попробуйте позже или обратитесь в поддержку."
                ))
            elif update.message:
                asyncio.run(update.message.reply_text(
                    "❌ Произошла ошибка. Попробуйте позже или обратитесь в поддержку."
                ))
        except:
            pass
