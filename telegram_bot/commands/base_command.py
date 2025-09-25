"""
Базовый класс для команд Telegram бота
Применяет принцип Open/Closed Principle (OCP)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Базовый класс для всех команд бота"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Выполнить команду"""
        pass
    
    @abstractmethod
    def get_command_name(self) -> str:
        """Получить название команды"""
        pass
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
        """Обработать ошибку команды"""
        self.logger.error(f"Ошибка в команде {self.get_command_name()}: {error}")
        
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при выполнении команды. Попробуйте позже."
            )
    
    def validate_update(self, update: Update) -> bool:
        """Проверить валидность update"""
        return (
            update.effective_chat is not None and 
            update.effective_user is not None
        )
    
    async def send_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          text: str, **kwargs) -> None:
        """Отправить сообщение пользователю"""
        if not self.validate_update(update):
            self.logger.error("Invalid update for sending message")
            return
            
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            **kwargs
        )
