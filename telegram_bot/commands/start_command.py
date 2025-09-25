"""
Команда /start для Telegram бота
"""

from telegram import Update
from telegram.ext import ContextTypes
from .base_command import BaseCommand


class StartCommand(BaseCommand):
    """Обработчик команды /start"""
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Выполнить команду /start"""
        if not self.validate_update(update):
            return
            
        user = update.effective_user
        
        welcome_text = f"""
🎯 **Добро пожаловать в ExamFlow, {user.first_name}!**

Я твой ИИ-помощник для подготовки к ЕГЭ и ОГЭ.

🚀 **Что я умею:**
• Отвечать на вопросы по любому предмету
• Решать задачи с подробными объяснениями
• Анализировать твои слабые места
• Создавать персональный план обучения

📚 **Доступные команды:**
/help - Получить помощь
/subjects - Выбрать предмет
/stats - Посмотреть статистику

💡 **Просто напиши мне вопрос**, например:
"Как решать квадратные уравнения?"
"Объясни теорию вероятности"
"Как писать сочинение ЕГЭ?"

Готов помочь тебе достичь высоких результатов! 🎓
        """
        
        await self.send_message(update, context, welcome_text)
    
    def get_command_name(self) -> str:
        return "/start"
