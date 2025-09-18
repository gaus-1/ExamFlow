"""
Форматтеры сообщений для Telegram бота.
Современные утилиты для форматирования текста.
"""

from ..utils.text_utils import (
    clean_markdown_text,
    create_error_message,
)


def create_main_message(text: str) -> str:
    """
    Создает основное сообщение бота.
    
    Args:
        text: Текст сообщения
        
    Returns:
        Отформатированное сообщение
    """
    return clean_markdown_text(text)


def create_warning_message(text: str) -> str:
    """
    Создает предупреждающее сообщение.
    
    Args:
        text: Текст предупреждения
        
    Returns:
        Отформатированное предупреждение
    """
    return create_error_message(text, "Проверьте ввод и попробуйте снова")
