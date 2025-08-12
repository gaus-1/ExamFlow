import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение"""

    site_url = "https://ExamFlowBot1.pythonanywhere.com"
    
    keyboard = [
        [InlineKeyboardButton("Получить задание", callback_data='get_task')],
        [InlineKeyboardButton("Мой прогресс", callback_data='progress')],
        [InlineKeyboardButton("Перейти на сайт", url=site_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать в ExamFlow! 🎓\n\n"
        "Я помогу вам подготовиться к экзаменам. "
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает справку"""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Справка\n"
        "/exam - Получить задание"
    )

async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет случайное задание"""
    await update.message.reply_text(
        "Ваше задание:\n"
        "Решите уравнение: 2x + 5 = 15\n\n"
        "Введите ответ в формате /answer <ваш ответ>"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_task':
        await query.message.reply_text(
            "Ваше задание:\n"
            "Решите уравнение: 2x + 5 = 15\n\n"
            "Введите ответ в формате /answer <ваш ответ>"
        )
    elif query.data == 'progress':
        await query.message.reply_text("Ваш прогресс: 0 заданий выполнено")
    
    # Вставляем ваш URL от ngrok
    site_url = "https://88a59fcd666a.ngrok-free.app"
    
    # Восстанавливаем кнопки после нажатия
    keyboard = [
        [InlineKeyboardButton("Получить задание", callback_data='get_task')],
        [InlineKeyboardButton("Мой прогресс", callback_data='progress')],
        [InlineKeyboardButton("Перейти на сайт", url=site_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_reply_markup(reply_markup=reply_markup)

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("exam", exam_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling()

if __name__ == '__main__':
    main()
