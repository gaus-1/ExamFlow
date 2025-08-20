import json
import logging
from django.shortcuts import render  # type: ignore
from django.http import JsonResponse, HttpResponse  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from django.views.decorators.http import require_POST  # type: ignore
from django.conf import settings  # type: ignore
from telegram import Update  # type: ignore

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
            # Обрабатываем обновление синхронно
            handle_telegram_update_sync(update, bot)
        
        return HttpResponse("ok")
        
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON от Telegram")
        return HttpResponse("error", status=400)
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {str(e)}")
        return HttpResponse("error", status=500)


def handle_telegram_update_sync(update: Update, bot):
    """Синхронная обработка обновления от Telegram"""
    try:
        # Импортируем синхронные обработчики
        from bot.sync_handlers import (
            start_sync, subjects_menu_sync, about_sync, progress_sync,
            rating_sync, random_task_sync, handle_unknown_callback_sync
        )
        
        # Обрабатываем команды и текст
        if update.message:
            text = (update.message.text or '').strip()
            if text == '/start':
                start_sync(update, bot)
                return
            if text in ('📚 Предметы',):
                subjects_menu_sync(update, bot)
                return
            if text in ('🎯 Случайное',):
                random_task_sync(update, bot)
                return
            if text in ('📊 Прогресс',):
                progress_sync(update, bot)
                return
            if text in ('🏆 Рейтинг',):
                rating_sync(update, bot)
                return
            if text in ('ℹ️ О боте',):
                about_sync(update, bot)
                return
        
        # Обрабатываем callback queries
        if update.callback_query:
            callback_data = update.callback_query.data
            logger.info(f"Обрабатываю callback: {callback_data}")
            logger.info(f"Тип обновления: callback_query")
            logger.info(f"Пользователь: {update.effective_user.username or update.effective_user.id}")
            
            # Простые обработчики
            if callback_data == 'subjects':
                subjects_menu_sync(update, bot)
            elif callback_data == 'main_menu':
                start_sync(update, bot)
            elif callback_data == 'about':
                about_sync(update, bot)
            elif callback_data == 'progress':
                progress_sync(update, bot)
            elif callback_data == 'rating':
                rating_sync(update, bot)
            elif callback_data == 'random_task':
                random_task_sync(update, bot)
            elif callback_data.startswith('subject_'):
                # Пока что просто возвращаем в главное меню
                # TODO: Добавить обработку предметов
                logger.info(f"Callback для предмета: {callback_data}")
                start_sync(update, bot)
            else:
                # Неизвестный callback - логируем и возвращаем в главное меню
                logger.warning(f"Неизвестный callback: {callback_data}")
                handle_unknown_callback_sync(update, bot)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_telegram_update_sync: {str(e)}")
        # В случае ошибки пытаемся отправить сообщение об ошибке
        try:
            if update.message:
                bot.send_message(
                    chat_id=update.message.chat_id,
                    text="❌ Произошла ошибка. Попробуйте команду /start"
                )
            elif update.callback_query:
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="❌ Произошла ошибка. Попробуйте команду /start"
                )
        except:
            pass



