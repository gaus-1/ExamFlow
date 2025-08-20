"""
Singleton экземпляр Telegram бота для webhook режима
"""

import os
import django
from telegram import Bot, BotCommand  # type: ignore
from django.conf import settings
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

logger = logging.getLogger(__name__)

class BotInstance:
    """Singleton для экземпляра Telegram бота"""
    _instance = None
    _bot = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_bot(self):
        """Получить экземпляр бота"""
        if self._bot is None:
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN не найден в настройках")
                return None
            
            try:
                self._bot = Bot(token=bot_token)
                logger.info("Экземпляр бота создан успешно")
                try:
                    # Настроим команды бота (меню снизу)
                    self._bot.set_my_commands([
                        BotCommand("start", "Главное меню"),
                        BotCommand("ai", "Открыть ИИ на сайте"),
                    ])
                except Exception as e:
                    logger.warning(f"Не удалось установить команды бота: {e}")
            except Exception as e:
                logger.error(f"Ошибка создания экземпляра бота: {str(e)}")
                return None
        
        return self._bot

# Глобальный экземпляр
bot_instance = BotInstance()

def get_bot():
    """Получить экземпляр бота"""
    return bot_instance.get_bot()
