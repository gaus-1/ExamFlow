"""
Утилиты для работы с базой данных на Render.com
Включает retry логику и обработку SSL соединений
"""

import logging
import time
from functools import wraps

from django.core.management.base import CommandError
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


def retry_database_operation(max_retries=3, delay=5, backoff=2):
    """
    Декоратор для retry операций с базой данных
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, CommandError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff**attempt)
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)

                        # Закрываем соединение перед повторной попыткой
                        connection.close()
                    else:
                        logger.error(
                            f"Database operation failed after {max_retries} attempts: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


def ensure_database_connection():
    """
    Обеспечивает стабильное подключение к базе данных
    """
    max_retries = 3
    delay = 5

    for attempt in range(max_retries):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                logger.info("Database connection established successfully")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                time.sleep(delay)
                connection.close()
            else:
                logger.error(
                    f"Database connection failed after {max_retries} attempts: {e}"
                )
                raise

    return False


def close_database_connections():
    """
    Закрывает все соединения с базой данных
    """
    try:
        connection.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")


def test_database_connectivity():
    """
    Тестирует подключение к базе данных - упрощенная версия для Render
    """
    try:
        with connection.cursor() as cursor:
            # Простая проверка
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("Database connectivity test passed")
                return True
            else:
                logger.error("Database connectivity test failed: unexpected result")
                return False

    except Exception as e:
        logger.error(f"Database connectivity test failed: {e}")
        return False
