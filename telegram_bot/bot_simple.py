#!/usr/bin/env python3
"""
Упрощенная версия ExamFlow Bot для быстрого запуска
Только основные функции без сложных зависимостей
"""

import os
import sys
import asyncio
import logging
import django

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
from core.container import Container

logger = logging.getLogger(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class SimpleExamFlowBot:
    """Упрощенная версия ExamFlow бота"""
    
    def __init__(self):
        self.token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        keyboard = [
            [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
            [InlineKeyboardButton("🤖 Спросить ИИ", callback_data="ai_help")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """🎯 **Добро пожаловать в ExamFlow!**

Я помогу вам подготовиться к ЕГЭ и ОГЭ:

📚 **Предметы** - выберите предмет для изучения
🤖 **ИИ-помощник** - задайте любой вопрос
📊 **Статистика** - отслеживайте прогресс

Выберите действие:"""
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def subjects_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик предметов"""
        try:
            from learning.models import Subject
            subjects = Subject.objects.filter(is_archived=False)[:6]  # type: ignore
            
            if not subjects:
                text = "📚 Предметы пока не загружены. Попробуйте позже."
                keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
            else:
                text = f"📚 **Доступные предметы ({subjects.count()}):**\n\nВыберите предмет для изучения:"
                keyboard = []
                for subject in subjects:
                    keyboard.append([InlineKeyboardButton(f"📖 {subject.name}", callback_data=f"subject_{subject.id}")])
                keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="start")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Ошибка в subjects_handler: {e}")
            await self.error_response(update, "Ошибка загрузки предметов")
    
    async def ai_help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик AI помощи"""
        try:
            ai_orchestrator = Container.ai_orchestrator()
            response = ai_orchestrator.ask("Привет! Я готов помочь с подготовкой к экзаменам.")
            
            text = f"🤖 **ИИ-Ассистент ExamFlow**\n\n{response.get('answer', 'Готов помочь!')}\n\n💡 Задайте любой вопрос или выберите действие:"
            
            keyboard = [
                [InlineKeyboardButton("❓ Задать вопрос", callback_data="ai_question")],
                [InlineKeyboardButton("📝 Объяснить тему", callback_data="ai_explain")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                await update.callback_query.answer()
                
        except Exception as e:
            logger.error(f"Ошибка в ai_help_handler: {e}")
            await self.error_response(update, "ИИ временно недоступен")
    
    async def stats_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик статистики"""
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

🎯 Система работает стабильно!"""
            
            keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                await update.callback_query.answer()
                
        except Exception as e:
            logger.error(f"Ошибка в stats_handler: {e}")
            await self.error_response(update, "Ошибка загрузки статистики")
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        if not update.message or not update.message.text:
            return
        
        text = update.message.text
        
        # Если это команда, игнорируем
        if text.startswith('/'):
            return
        
        # Обрабатываем как вопрос к ИИ
        try:
            ai_orchestrator = Container.ai_orchestrator()
            response = ai_orchestrator.ask(text)
            
            answer = response.get('answer', 'Извините, не могу ответить на этот вопрос.')
            
            # Ограничиваем длину ответа
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
            
            await update.message.reply_text(f"🤖 {answer}")
            
        except Exception as e:
            logger.error(f"Ошибка в text_message_handler: {e}")
            await update.message.reply_text("❌ ИИ временно недоступен. Попробуйте позже.")
    
    async def error_response(self, update: Update, message: str):
        """Отправка сообщения об ошибке"""
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"❌ {message}")
            elif update.message:
                await update.message.reply_text(f"❌ {message}")
        except Exception as e:
            logger.error(f"Ошибка отправки error_response: {e}")
    
    async def unknown_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных callback"""
        if update.callback_query:
            await update.callback_query.answer("❓ Неизвестная команда")
            await self.start_command(update, context)
    
    def setup_handlers(self, app: Application):
        """Настройка обработчиков"""
        # Команды
        app.add_handler(CommandHandler('start', self.start_command))
        app.add_handler(CommandHandler('help', self.start_command))
        
        # Callback queries
        app.add_handler(CallbackQueryHandler(self.start_command, pattern=r'^start$'))
        app.add_handler(CallbackQueryHandler(self.subjects_handler, pattern=r'^subjects$'))
        app.add_handler(CallbackQueryHandler(self.ai_help_handler, pattern=r'^ai_help$'))
        app.add_handler(CallbackQueryHandler(self.stats_handler, pattern=r'^stats$'))
        
        # Неизвестные callback
        app.add_handler(CallbackQueryHandler(self.unknown_callback_handler))
        
        # Текстовые сообщения
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message_handler))
        
        logger.info("Все обработчики настроены")
    
    async def run(self):
        """Запуск бота"""
        logger.info("Запуск Simple ExamFlow Bot...")
        
        # Создаем приложение
        app = Application.builder().token(self.token).build()
        
        # Настраиваем обработчики
        self.setup_handlers(app)
        
        # Проверяем подключение
        try:
            me = await app.bot.get_me()
            logger.info(f"Бот подключен: @{me.username} (ID: {me.id})")
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return
        
        # Запускаем polling
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            
            logger.info("Бот успешно запущен и работает!")
            
            # Ждем завершения
            import signal
            import asyncio
            
            # Создаем событие для graceful shutdown
            stop_event = asyncio.Event()
            
            def signal_handler(signum, frame):
                stop_event.set()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Ждем сигнала остановки
            await stop_event.wait()
            
        except Exception as e:
            logger.error(f"Ошибка работы бота: {e}")
        finally:
            await app.stop()
            await app.shutdown()

async def main():
    """Главная функция"""
    bot = SimpleExamFlowBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
