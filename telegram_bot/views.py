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
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

# 🔒 БЕЗОПАСНОСТЬ: Разрешенные IP для webhook (опционально)
ALLOWED_IPS = [
    '149.154.160.0/20',  # Telegram IP range
    '91.108.4.0/22',     # Telegram IP range
    '127.0.0.1',         # Localhost для разработки
]

def is_allowed_ip(ip):
    """Проверяет, разрешен ли IP для webhook"""
    if not ALLOWED_IPS:  # Если список пустой - разрешаем все
        return True
    
    for allowed_ip in ALLOWED_IPS:
        if '/' in allowed_ip:  # CIDR notation
            # Простая проверка CIDR (для продакшена лучше использовать ipaddress)
            if ip.startswith(allowed_ip.split('/')[0]):
                return True
        elif ip == allowed_ip:
            return True
    return False

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
        # 🔒 БЕЗОПАСНОСТЬ: Проверка IP
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if not is_allowed_ip(client_ip):
            logger.warning(f"Webhook заблокирован с IP: {client_ip}")
            return HttpResponse(b"Forbidden", status=403)  # type: ignore
        
        # 🔒 БЕЗОПАСНОСТЬ: Проверка размера данных
        if request.content_length and request.content_length > 1024 * 1024:  # 1MB limit
            logger.warning(f"Webhook заблокирован - слишком большой размер: {request.content_length}")
            return HttpResponse(b"Payload too large", status=413)  # type: ignore

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
                        # Убираем await, так как мы находимся в синхронном контексте
                        # Используем синхронный запуск event loop с локальным импортом,
                        # чтобы не затенять asyncio во внешнем скоупе
                        import asyncio as _aio
                        loop = _aio.new_event_loop()
                        _aio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(bot.send_message(chat_id=chat_id, text="Добро пожаловать в ExamFlow! Выберите действие:", reply_markup=kb))
                            logger.info("Быстрый ответ на /start отправлен через PTB")
                        finally:
                            loop.close()
            except Exception as ex:
                logger.warning(f"Не удалось отправить быстрый ответ на /start: {ex}")

            # Обрабатываем обновление в отдельном потоке, чтобы мгновенно отвечать Telegram
            def _run_async(u: Update):
                try:
                    import asyncio as _aio
                    _aio.run(handle_telegram_update(u))
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
            # Всегда подтверждаем callback, чтобы убрать "часики" в Telegram
            try:
                await update.callback_query.answer()
            except Exception as ack_err:
                logger.warning(f"Не удалось ответить на callback_query: {ack_err}")

            callback_data = update.callback_query.data or ""
            chat_id = None
            try:
                chat_id = update.effective_chat.id  # type: ignore
            except Exception:
                try:
                    chat_id = update.callback_query.message.chat_id  # type: ignore
                except Exception:
                    chat_id = None

            try:
                # Импортируем обработчики здесь, чтобы исключить циклические импорты при холодном старте
                from .bot_handlers import (
                    start as h_start,
                    subjects_menu as h_subjects_menu,
                    show_subject_topics as h_show_subject_topics,
                    show_task as h_show_task,
                    handle_answer as h_handle_answer,
                    show_stats as h_show_stats,
                    voice_hint as h_voice_hint,
                    learning_plan_menu as h_learning_plan_menu,
                    ai_help_handler as h_ai_help,
                    ai_hint_handler as h_ai_hint,
                    similar_tasks_handler as h_similar_tasks,
                    handle_unknown_callback as h_unknown
                )

                if callback_data == "subjects":
                    await h_subjects_menu(update, context)  # type: ignore
                elif callback_data == "stats":
                    await h_show_stats(update, context)  # type: ignore
                elif callback_data == "learning_plan":
                    await h_learning_plan_menu(update, context)  # type: ignore
                elif callback_data == "random_task":
                    await h_show_task(update, context)  # type: ignore
                elif callback_data == "main_menu":
                    await h_start(update, context)  # type: ignore
                elif callback_data.startswith("subject_"):
                    await h_show_subject_topics(update, context)  # type: ignore
                elif callback_data.startswith("topic_"):
                    await h_show_task(update, context)  # type: ignore
                elif callback_data.startswith("random_subject_"):
                    await h_show_task(update, context)  # type: ignore
                elif callback_data.startswith("voice_"):
                    await h_voice_hint(update, context)  # type: ignore
                elif callback_data.startswith("ai_help_"):
                    await h_ai_help(update, context)  # type: ignore
                elif callback_data.startswith("ai_hint_"):
                    await h_ai_hint(update, context)  # type: ignore
                elif callback_data.startswith("similar_"):
                    await h_similar_tasks(update, context)  # type: ignore
                elif callback_data.startswith("show_task_"):
                    await h_show_task(update, context)  # type: ignore
                elif callback_data.startswith("answer_"):
                    await h_show_task(update, context)  # type: ignore
                else:
                    await h_unknown(update, context)  # type: ignore
            except Exception as cb_err:
                logger.error(f"Ошибка обработки callback '{callback_data}': {cb_err}")
                # Отправим аккуратное сообщение пользователю, чтобы он не остался без ответа
                try:
                    if chat_id is not None:
                        await context.bot.send_message(chat_id=chat_id, text="❌ Временная ошибка. Попробуйте ещё раз или отправьте /start")  # type: ignore
                except Exception as send_err:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_err}")
                
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
