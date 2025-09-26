"""
Сервисные классы для Telegram бота
Применяют принципы SOLID для разделения ответственности
"""

from .ai_service import AIService
from .progress_service import ProgressService
from .user_service import UserService

__all__ = ["UserService", "AIService", "ProgressService"]
