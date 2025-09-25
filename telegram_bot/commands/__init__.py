"""
Модуль команд Telegram бота
Применяет принципы SOLID для декомпозиции bot_handlers.py
"""

from .base_command import BaseCommand
from .start_command import StartCommand
from .help_command import HelpCommand
from .subjects_command import SubjectsCommand

__all__ = [
    'BaseCommand',
    'StartCommand', 
    'HelpCommand',
    'SubjectsCommand'
]
