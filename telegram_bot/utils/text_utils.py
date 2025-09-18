"""
Утилиты для работы с текстом в Telegram боте.
Единый модуль для всех текстовых операций.
"""

import re
from typing import Optional


def clean_markdown_text(text: str) -> str:
    """
    Очищает текст от проблемных символов Markdown для безопасной отправки в Telegram.
    
    Args:
        text: Исходный текст с возможными Markdown символами
        
    Returns:
        Очищенный текст без Markdown символов
    """
    if not text:
        return ""

    # Удаляем все Markdown символы одним regex
    cleaned = re.sub(r'[*_`~\[\]()#]', '', text)

    # Удаляем множественные пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()


def clean_log_text(text: str, max_length: int = 50) -> str:
    """
    Очищает текст для безопасного логирования.
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        
    Returns:
        Очищенный текст для логов
    """
    if not text:
        return ""

    # Удаляем эмодзи и специальные символы
    cleaned = re.sub(r'[^\w\s\-., !?]', '', text)

    # Обрезаем до нужной длины
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."

    return cleaned.strip()


def format_ai_response(response: str, max_length: int = 4000) -> str:
    """
    Форматирует ответ AI для отправки в Telegram.
    
    Args:
        response: Ответ от AI
        max_length: Максимальная длина сообщения Telegram
        
    Returns:
        Отформатированный ответ
    """
    if not response:
        return "❌ Пустой ответ от ИИ"

    # Очищаем от проблемных символов
    cleaned = clean_markdown_text(response)

    # Обрезаем если слишком длинный
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length - 50] + "\n\n... (ответ обрезан)"

    return cleaned


def create_error_message(error: str, context: Optional[str] = None) -> str:
    """
    Создает стандартизированное сообщение об ошибке.
    
    Args:
        error: Описание ошибки
        context: Дополнительный контекст
        
    Returns:
        Форматированное сообщение об ошибке
    """
    base_message = f"❌ {error}"

    if context:
        base_message += f"\n\n💡 {context}"

    return base_message


def create_success_message(message: str, action: Optional[str] = None) -> str:
    """
    Создает стандартизированное сообщение об успехе.
    
    Args:
        message: Основное сообщение
        action: Предлагаемое действие
        
    Returns:
        Форматированное сообщение об успехе
    """
    base_message = f"✅ {message}"

    if action:
        base_message += f"\n\n➡️ {action}"

    return base_message


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины с добавлением суффикса.
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        Обрезанный текст
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_numbers(text: str) -> list[int]:
    """
    Извлекает все числа из текста.
    
    Args:
        text: Исходный текст
        
    Returns:
        Список найденных чисел
    """
    return [int(match) for match in re.findall(r'\d+', text)]


def is_valid_telegram_message(text: str) -> bool:
    """
    Проверяет, валидно ли сообщение для отправки в Telegram.
    
    Args:
        text: Текст сообщения
        
    Returns:
        True если сообщение валидно
    """
    if not text or not text.strip():
        return False

    if len(text) > 4096:  # Лимит Telegram
        return False

    # Проверяем на наличие только пробелов/символов
    if not re.search(r'[a-zA-Zа-яА-Я0-9]', text):
        return False

    return True
