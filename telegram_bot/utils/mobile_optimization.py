"""
Утилиты для оптимизации работы бота на мобильных устройствах
"""

import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def is_mobile_device(user_agent: str | None = None) -> bool:
    """
    Определяет, является ли устройство мобильным
    """
    if not user_agent:
        return False

    mobile_keywords = [
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
        "opera mini",
        "mobile safari",
        "mobile chrome",
    ]

    user_agent_lower = user_agent.lower()
    return any(keyword in user_agent_lower for keyword in mobile_keywords)


def get_mobile_optimized_timeout() -> int:
    """
    Возвращает оптимизированный timeout для мобильных устройств
    """
    return getattr(settings, "TELEGRAM_BOT_CONFIG", {}).get("MOBILE_TIMEOUT", 15)


def get_mobile_optimized_ai_timeout() -> int:
    """
    Возвращает оптимизированный timeout для AI ответов на мобильных
    """
    return getattr(settings, "GEMINI_MOBILE_TIMEOUT", 5)


def get_mobile_optimized_max_tokens() -> int:
    """
    Возвращает ограничение токенов для мобильных устройств
    """
    return getattr(settings, "GEMINI_MAX_TOKENS", 512)


def cache_ai_response(prompt_hash: str, response: str, timeout: int = 300) -> None:
    """
    Кэширует AI ответ для быстрого доступа
    """
    try:
        cache_key = f"ai_response_{prompt_hash}"
        cache.set(cache_key, response, timeout)
        logger.debug(f"AI ответ закэширован: {cache_key}")
    except Exception as e:
        logger.error(f"Ошибка кэширования AI ответа: {e}")


def get_cached_ai_response(prompt_hash: str) -> str | None:
    """
    Получает закэшированный AI ответ
    """
    try:
        cache_key = f"ai_response_{prompt_hash}"
        response = cache.get(cache_key)
        if response:
            logger.debug(f"AI ответ получен из кэша: {cache_key}")
        return response
    except Exception as e:
        logger.error(f"Ошибка получения AI ответа из кэша: {e}")
        return None


def generate_prompt_hash(prompt: str, user_id: int) -> str:
    """
    Генерирует хэш для промпта для кэширования
    """
    import hashlib

    content = f"{prompt}_{user_id}".encode()
    return hashlib.md5(content).hexdigest()


def optimize_response_for_mobile(response: str, max_length: int = 2000) -> str:
    """
    Оптимизирует ответ для мобильных устройств
    """
    if len(response) > max_length:
        # Сокращаем ответ для мобильных
        response = response[: max_length - 3] + "..."

    # Убираем лишние переносы строк
    response = response.replace("\n\n\n", "\n\n")

    return response


def get_mobile_optimized_config() -> dict[str, Any]:
    """
    Возвращает конфигурацию, оптимизированную для мобильных устройств
    """
    return {
        "timeout": get_mobile_optimized_timeout(),
        "ai_timeout": get_mobile_optimized_ai_timeout(),
        "max_tokens": get_mobile_optimized_max_tokens(),
        "cache_enabled": getattr(settings, "TELEGRAM_BOT_CONFIG", {}).get(
            "CACHE_AI_RESPONSES", True
        ),
        "max_response_length": 2000,
    }
