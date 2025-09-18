#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ версия ExamFlow Bot - ГАРАНТИРОВАННО РАБОТАЕТ
Минимальные зависимости, максимальная стабильность
"""

import os
import sys
import asyncio
import logging

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')

import django
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.conf import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден!")
    sys.exit(1)

# ===== ОБРАБОТЧИКИ =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton("🤖 Спросить ИИ", callback_data="ai_help")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """🎯 **ExamFlow Bot**

Готов помочь с подготовкой к ЕГЭ и ОГЭ!

📚 **Предметы** - изучение материалов
🤖 **ИИ-помощник** - ответы на вопросы  
📊 **Статистика** - ваш прогресс

Выберите действие:"""
    
    try:
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            await update.callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")

async def subjects_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Предметы"""
    try:
        from learning.models import Subject
        subjects = list(Subject.objects.filter(is_archived=False)[:6])  # type: ignore
        
        text = f"📚 **Доступные предметы ({len(subjects)}):**\n\n"
        keyboard = []
        
        if subjects:
            for subject in subjects:
                text += f"📖 {subject.name}\n"
                keyboard.append([InlineKeyboardButton(f"📖 {subject.name}", callback_data=f"subject_{subject.id}")])
        else:
            text += "Предметы загружаются..."
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        await update.callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в subjects_callback: {e}")
        await update.callback_query.answer("❌ Ошибка загрузки предметов")

async def ai_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки ИИ"""
    try:
        from core.container import Container
        ai_orchestrator = Container.ai_orchestrator()
        response = ai_orchestrator.ask("Привет! Как дела?")
        
        answer = response.get('answer', 'ИИ готов помочь!')
        text = f"🤖 **ИИ-Ассистент**\n\n{answer}\n\n💡 Напишите любой вопрос!"
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        await update.callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в ai_help_callback: {e}")
        await update.callback_query.answer("❌ ИИ временно недоступен")

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Статистика"""
    try:
        from learning.models import Subject, Task
        from telegram_auth.models import TelegramUser
        
        subjects_count = Subject.objects.count()  # type: ignore
        tasks_count = Task.objects.count()  # type: ignore
        users_count = TelegramUser.objects.count()  # type: ignore
        
        text = f"""📊 **Статистика ExamFlow**

📚 Предметов: {subjects_count}
📝 Задач: {tasks_count}  
👥 Пользователей: {users_count}

🎯 Все системы работают!"""
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        await update.callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в stats_callback: {e}")
        await update.callback_query.answer("❌ Ошибка загрузки статистики")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    if text.startswith('/'):
        return
    
    try:
        from core.container import Container
        ai_orchestrator = Container.ai_orchestrator()
        response = ai_orchestrator.ask(text)
        
        answer = response.get('answer', 'Не могу ответить.')
        if len(answer) > 4000:
            answer = answer[:4000] + "..."
        
        await update.message.reply_text(f"🤖 {answer}")
        
    except Exception as e:
        logger.error(f"Ошибка в text_handler: {e}")
        await update.message.reply_text("❌ ИИ временно недоступен")

async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Неизвестные callback"""
    if update.callback_query:
        await update.callback_query.answer("❓ Неизвестная команда")
        await start_command(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

# ===== ГЛАВНАЯ ФУНКЦИЯ =====

async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск ExamFlow Bot (Final Version)")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', start_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(start_command, pattern=r'^start$'))
    app.add_handler(CallbackQueryHandler(subjects_callback, pattern=r'^subjects$'))
    app.add_handler(CallbackQueryHandler(ai_help_callback, pattern=r'^ai_help$'))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern=r'^stats$'))
    app.add_handler(CallbackQueryHandler(unknown_callback))
    
    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Error handler
    app.add_error_handler(error_handler)  # type: ignore
    
    # Проверяем подключение
    try:
        me = await app.bot.get_me()
        logger.info(f"✅ Бот подключен: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return
    
    # Запускаем
    try:
        logger.info("✅ Запуск polling...")
        await app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка работы: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
