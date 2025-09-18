#!/usr/bin/env python3
"""
УЛЬТРА ПРОСТОЙ ExamFlow Bot - БЕЗ ПРОБЛЕМ
Работает ГАРАНТИРОВАННО
"""

import os
import sys
import logging

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')

import django
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.conf import settings

# Простое логирование без эмодзи
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен
BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("Предметы", callback_data="subjects")],
        [InlineKeyboardButton("ИИ помощь", callback_data="ai_help")],
        [InlineKeyboardButton("Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "ExamFlow Bot готов помочь!\n\nВыберите действие:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()

async def subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предметы"""
    try:
        from learning.models import Subject
        subjects_list = list(Subject.objects.all()[:5])  # type: ignore
        
        text = f"Предметов в базе: {len(subjects_list)}\n\n"
        for s in subjects_list:
            text += f"- {s.name}\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()
    except Exception as e:
        await update.callback_query.answer("Ошибка загрузки предметов")

async def ai_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ИИ помощь"""
    try:
        from core.container import Container
        ai = Container.ai_orchestrator()
        response = ai.ask("Привет!")
        
        answer = response.get('answer', 'ИИ работает!')
        text = f"ИИ ответ: {answer[:200]}...\n\nНапишите любой вопрос!"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()
    except Exception as e:
        await update.callback_query.answer("ИИ недоступен")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    try:
        from learning.models import Subject, Task
        
        subjects_count = Subject.objects.count()  # type: ignore
        tasks_count = Task.objects.count()  # type: ignore
        
        text = f"Статистика:\n\nПредметов: {subjects_count}\nЗадач: {tasks_count}"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()
    except Exception as e:
        await update.callback_query.answer("Ошибка статистики")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текстовые сообщения"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    if text.startswith('/'):
        return
    
    try:
        from core.container import Container
        ai = Container.ai_orchestrator()
        response = ai.ask(text)
        answer = response.get('answer', 'Не понимаю')
        await update.message.reply_text(f"ИИ: {answer[:500]}...")
    except:
        await update.message.reply_text("ИИ недоступен")

def main():
    """Запуск бота"""
    print("Запуск ExamFlow Bot...")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(start, pattern=r'^start$'))
    app.add_handler(CallbackQueryHandler(subjects, pattern=r'^subjects$'))
    app.add_handler(CallbackQueryHandler(ai_help, pattern=r'^ai_help$'))
    app.add_handler(CallbackQueryHandler(stats, pattern=r'^stats$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    
    # Проверяем подключение
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        me = loop.run_until_complete(app.bot.get_me())
        print(f"Бот подключен: @{me.username}")
        loop.close()
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return
    
    # Запускаем
    try:
        print("Запуск polling...")
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
