"""
Менеджер контекста для Telegram бота
Хранит историю сообщений пользователей для персонализированных ответов
"""

import json
import logging
from typing import List, Dict, Optional
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BotContextManager:
    """Управляет контекстом разговора с пользователями"""
    
    def __init__(self, max_messages: int = 10, ttl_hours: int = 24):
        self.max_messages = max_messages  # Максимум сообщений в контексте
        self.ttl_hours = ttl_hours  # Время жизни контекста в часах
    
    def _get_cache_key(self, user_id: int) -> str:
        """Генерирует ключ кэша для пользователя"""
        return f"bot_context_{user_id}"
    
    def add_message(self, user_id: int, message: str, is_user: bool = True) -> None:
        """Добавляет сообщение в контекст пользователя"""
        try:
            cache_key = self._get_cache_key(user_id)
            context = self.get_context(user_id)
            
            # Добавляем новое сообщение
            new_message = {
                'text': message[:500],  # Ограничиваем длину
                'is_user': is_user,
                'timestamp': datetime.now().isoformat(),
                'role': 'user' if is_user else 'assistant'
            }
            
            context.append(new_message)
            
            # Ограничиваем количество сообщений
            if len(context) > self.max_messages:
                context = context[-self.max_messages:]
            
            # Сохраняем в кэш
            cache.set(cache_key, context, timeout=self.ttl_hours * 3600)
            
            logger.info(f"Добавлено сообщение в контекст пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения в контекст: {e}")
    
    def get_context(self, user_id: int) -> List[Dict]:
        """Получает контекст пользователя"""
        try:
            cache_key = self._get_cache_key(user_id)
            context = cache.get(cache_key, [])
            
            # Фильтруем устаревшие сообщения
            cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)
            
            filtered_context = []
            for msg in context:
                try:
                    msg_time = datetime.fromisoformat(msg['timestamp'])
                    if msg_time > cutoff_time:
                        filtered_context.append(msg)
                except (KeyError, ValueError):
                    # Пропускаем сообщения с некорректными данными
                    continue
            
            return filtered_context
            
        except Exception as e:
            logger.error(f"Ошибка получения контекста: {e}")
            return []
    
    def format_context_for_ai(self, user_id: int, current_message: str) -> str:
        """Форматирует контекст для отправки в AI"""
        try:
            context = self.get_context(user_id)
            
            if not context:
                return current_message
            
            # Формируем историю диалога
            dialog_history = []
            for msg in context[-5:]:  # Берем последние 5 сообщений
                role = "Студент" if msg['is_user'] else "ExamFlow AI"
                dialog_history.append(f"{role}: {msg['text']}")
            
            # Добавляем текущее сообщение
            dialog_history.append(f"Студент: {current_message}")
            
            formatted_context = f"""ИСТОРИЯ ДИАЛОГА:
{chr(10).join(dialog_history)}

ИНСТРУКЦИЯ: Учитывай предыдущие сообщения студента. Если он продолжает тему - развивай её. Если задает уточняющие вопросы - отвечай с учетом контекста."""
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Ошибка форматирования контекста: {e}")
            return current_message
    
    def clear_context(self, user_id: int) -> bool:
        """Очищает контекст пользователя"""
        try:
            cache_key = self._get_cache_key(user_id)
            cache.delete(cache_key)
            logger.info(f"Контекст пользователя {user_id} очищен")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки контекста: {e}")
            return False
    
    def get_context_summary(self, user_id: int) -> Dict:
        """Получает краткую сводку контекста"""
        try:
            context = self.get_context(user_id)
            
            if not context:
                return {'messages_count': 0, 'last_activity': None}
            
            user_messages = [msg for msg in context if msg['is_user']]
            ai_messages = [msg for msg in context if not msg['is_user']]
            
            last_message = context[-1] if context else None
            last_activity = last_message['timestamp'] if last_message else None
            
            return {
                'messages_count': len(context),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'last_activity': last_activity,
                'has_context': len(context) > 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки контекста: {e}")
            return {'messages_count': 0, 'last_activity': None, 'has_context': False}
