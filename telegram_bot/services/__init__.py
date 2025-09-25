"""
Сервисные классы для Telegram бота
Применяют принципы SOLID для разделения ответственности
"""

from .user_service import UserService
from .ai_service import AIService
from .progress_service import ProgressService

__all__ = [
    'UserService',
    'AIService', 
    'ProgressService'
]
