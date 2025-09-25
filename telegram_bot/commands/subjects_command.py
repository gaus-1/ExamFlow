"""
Команда /subjects для Telegram бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base_command import BaseCommand


class SubjectsCommand(BaseCommand):
    """Обработчик команды /subjects"""
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Выполнить команду /subjects"""
        if not self.validate_update(update):
            return
            
        # Создаем клавиатуру с предметами
        keyboard = [
            [
                InlineKeyboardButton("📐 Математика", callback_data="subject_math"),
                InlineKeyboardButton("📝 Русский язык", callback_data="subject_russian")
            ],
            [
                InlineKeyboardButton("⚗️ Физика", callback_data="subject_physics"),
                InlineKeyboardButton("🧪 Химия", callback_data="subject_chemistry")
            ],
            [
                InlineKeyboardButton("🧬 Биология", callback_data="subject_biology"),
                InlineKeyboardButton("📜 История", callback_data="subject_history")
            ],
            [
                InlineKeyboardButton("🏛️ Обществознание", callback_data="subject_social"),
                InlineKeyboardButton("🌍 География", callback_data="subject_geography")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        subjects_text = """
📚 **Выберите предмет для изучения:**

Выберите предмет из списка ниже, и я помогу вам:
• Разобраться в теории
• Решить практические задачи
• Подготовиться к экзаменам
• Проанализировать слабые места

💡 **Совет:** После выбора предмета просто задавайте вопросы!
        """
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=subjects_text,
            reply_markup=reply_markup
        )
    
    def get_command_name(self) -> str:
        return "/subjects"
