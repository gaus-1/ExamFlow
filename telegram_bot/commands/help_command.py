"""
Команда /help для Telegram бота
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base_command import BaseCommand


class HelpCommand(BaseCommand):
    """Обработчик команды /help"""

    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Выполнить команду /help"""
        if not self.validate_update(update):
            return

        help_text = """
🤖 **ExamFlow Bot - Справка**

**📚 Основные команды:**
/start - Начать работу с ботом
/help - Показать эту справку
/subjects - Выбрать предмет для изучения
/stats - Посмотреть свою статистику

**💡 Как пользоваться:**
1. Просто напишите мне вопрос по любому предмету
2. Я отвечу с подробными объяснениями
3. Могу решить задачи и объяснить решения
4. Анализирую ваши слабые места

**📖 Примеры вопросов:**
• "Как решать квадратные уравнения?"
• "Объясни теорию вероятности"
• "Как писать сочинение ЕГЭ?"
• "Найди производную функции x³ + 2x"

**🎯 Предметы:**
• Математика (ЕГЭ/ОГЭ)
• Русский язык
• Физика
• Химия
• Биология
• История
• Обществознание

**❓ Нужна помощь?**
Напишите @examflow_support или используйте команду /start
        """

        await self.send_message(update, context, help_text)

    def get_command_name(self) -> str:
        return "/help"
