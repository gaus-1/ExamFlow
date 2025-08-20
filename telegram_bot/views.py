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
import threading
import requests  # type: ignore
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from telegram import Update
from .bot_main import setup_bot_application, get_bot
from django.conf import settings

logger = logging.getLogger(__name__)


def test_webhook(request):
    """
    Тестовая функция для проверки доступности webhook
    """
    return JsonResponse({
        'status': 'ok',
        'message': 'Webhook endpoint доступен',
        'timestamp': datetime.now().isoformat(),
        'token_exists': bool(settings.TELEGRAM_BOT_TOKEN),
        'token_preview': settings.TELEGRAM_BOT_TOKEN[:10] + '...' if settings.TELEGRAM_BOT_TOKEN else None
    })


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """
    Обрабатывает webhook от Telegram
    
    Принимает JSON с обновлениями от Telegram API
    и передает их в обработчики бота
    """
    logger.info(f"=== НАЧАЛО ОБРАБОТКИ WEBHOOK ===")
    logger.info(f"Время: {datetime.now()}")
    logger.info(f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    logger.info(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")
    
    try:
        # Детальное логирование входящего webhook
        logger.info(f"Webhook получен: {request.method} {request.path}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body length: {len(request.body)} bytes")
        
        # Парсим JSON данные
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f"Webhook data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Получаем экземпляр бота
        bot = get_bot()
        logger.info(f"Bot instance получен: {bot is not None}")
        
        # Создаем объект Update
        update = Update.de_json(data, bot)
        logger.info(f"Update создан: {update is not None}")
        
        if update:
            # Быстрая реакция на /start в синхронном режиме (диагностика отклика)
            try:
                if update.message and (update.message.text or '').strip().lower().startswith('/start'):
                    chat_id = update.message.chat_id
                    logger.info(f"Обрабатываем /start для chat_id: {chat_id}")
                    
                    # Пытаемся отправить через Bot API (http), чтобы исключить проблемы клиента
                    try:
                        # Используем inline-клавиатуру, чтобы приходили callback-запросы,
                        # а не текстовые сообщения, которые попадают в обработчик ответов
                        reply_kb = {
                            'inline_keyboard': [[
                                { 'text': "📚 Предметы", 'callback_data': 'subjects' },
                                { 'text': "🎯 Случайное", 'callback_data': 'random_task' }
                            ], [
                                { 'text': "📊 Статистика", 'callback_data': 'stats' }
                            ]]
                        }
                        token = settings.TELEGRAM_BOT_TOKEN
                        if not token:
                            logger.error("TELEGRAM_BOT_TOKEN не настроен в settings!")
                            return HttpResponse(b"ERROR: No token", status=500)
                        logger.info(f"Отправляем HTTP-ответ через Bot API для токена: {token[:10]}...")
                        
                        response = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={
                                'chat_id': chat_id,
                                'text': 'Добро пожаловать в ExamFlow! Выберите действие:',
                                'reply_markup': reply_kb
                            },
                            timeout=8,
                        )
                        logger.info(f"HTTP-ответ отправлен, статус: {response.status_code}, ответ: {response.text}")
                    except Exception as http_ex:
                        logger.warning(f"HTTP-ответ на /start не удался: {http_ex}")
                        # Резерв: пробуем через python-telegram-bot
                        logger.info("Пробуем резервный способ через python-telegram-bot")
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
                        kb = InlineKeyboardMarkup([
                            [InlineKeyboardButton("📚 Предметы", callback_data="subjects"), InlineKeyboardButton("🎯 Случайное", callback_data="random_task")],
                            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                        ])
                        bot.send_message(chat_id=chat_id, text="Добро пожаловать в ExamFlow! Выберите действие:", reply_markup=kb)
                        logger.info("Быстрый ответ на /start отправлен через PTB")
            except Exception as ex:
                logger.warning(f"Не удалось отправить быстрый ответ на /start: {ex}")

            # Обрабатываем обновление в отдельном потоке, чтобы мгновенно отвечать Telegram
            def _run_async(u: Update):
                try:
                    asyncio.run(handle_telegram_update(u))
                except Exception as ex:
                    logger.error(f"Ошибка фоновой обработки обновления: {ex}")

            threading.Thread(target=_run_async, args=(update,), daemon=True).start()

        # Немедленно подтверждаем приём, чтобы избежать таймаута Telegram
        logger.info("Webhook успешно обработан, возвращаем OK")
        logger.info(f"=== КОНЕЦ ОБРАБОТКИ WEBHOOK ===")
        return HttpResponse(b"OK")
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return HttpResponse(b"ERROR", status=500)


async def handle_telegram_update(update: Update):
    """
    Асинхронно обрабатывает обновление от Telegram
    
    Создает mock-контекст и вызывает соответствующие обработчики
    """
    try:
        # Быстрый ответ на /start через прямой вызов API — минимизируем риски парсинга
        if update.message and (update.message.text or '').strip().lower().startswith('/start'):
            try:
                await update.effective_chat.send_action('typing')  # type: ignore
            except Exception:
                pass
            try:
                await update.effective_chat.send_message(  # type: ignore
                    text=(
                        "Добро пожаловать в ExamFlow!\n\n"
                        "Нажмите кнопки ниже: Предметы, Случайное, Статистика."
                    )
                )
            except Exception as e:
                logger.error(f"Ошибка быстрой отправки /start: {e}")

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
                text = update.message.text.strip()
                if text.startswith('/start') or text.lower() in ('меню','start'):
                    await start(update, context)  # type: ignore
                elif text.startswith('/help'):
                    await start(update, context)  # type: ignore
                else:
                    # Обрабатываем как ответ на задание
                    await handle_answer(update, context)  # type: ignore
        
        # Обрабатываем callback-запросы
        elif update.callback_query:
            callback_data = update.callback_query.data
            
            if callback_data == "subjects":
                await subjects_menu(update, context)  # type: ignore
            elif callback_data == "stats":
                await show_stats(update, context)  # type: ignore
            elif callback_data == "random_task":
                await show_task(update, context)  # type: ignore
            elif callback_data == "main_menu":
                await start(update, context)  # type: ignore
            elif callback_data.startswith("subject_"):
                await show_subject_topics(update, context)  # type: ignore
            elif callback_data.startswith("topic_"):
                await show_task(update, context)  # type: ignore
            elif callback_data.startswith("random_subject_"):
                await show_task(update, context)  # type: ignore
            elif callback_data.startswith("voice_"):
                await voice_hint(update, context)  # type: ignore
            elif callback_data.startswith("answer_"):
                await show_task(update, context)  # type: ignore
            else:
                await handle_unknown_callback(update, context)  # type: ignore
                
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
