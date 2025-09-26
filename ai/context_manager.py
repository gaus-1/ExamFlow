"""
Менеджер контекста для веб-сайта
Хранит историю диалогов пользователей с AI
"""

import logging
from typing import List, Dict
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WebContextManager:
    """Управляет контекстом AI диалогов на веб-сайте"""
    
    def __init__(self, max_messages: int = 8, ttl_hours: int = 2):
        self.max_messages = max_messages  # Максимум сообщений в контексте
        self.ttl_hours = ttl_hours  # Время жизни контекста (короче чем в боте)
    
    def _get_cache_key(self, session_id: str) -> str:
        """Генерирует ключ кэша для сессии"""
        return f"web_ai_context_{session_id}"
    
    def add_message(self, session_id: str, message: str, is_user: bool = True) -> None:
        """Добавляет сообщение в контекст сессии"""
        try:
            cache_key = self._get_cache_key(session_id)
            context = self.get_context(session_id)
            
            # Добавляем новое сообщение
            new_message = {
                'text': message[:800],  # Ограничиваем длину для веба
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
            
            logger.info(f"Добавлено сообщение в веб-контекст сессии {session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения в веб-контекст: {e}")
    
    def get_context(self, session_id: str) -> List[Dict]:
        """Получает контекст сессии"""
        try:
            cache_key = self._get_cache_key(session_id)
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
                    continue
            
            return filtered_context
            
        except Exception as e:
            logger.error(f"Ошибка получения веб-контекста: {e}")
            return []
    
    def format_context_for_ai(self, session_id: str, current_message: str) -> str:
        """Форматирует контекст для отправки в AI"""
        try:
            context = self.get_context(session_id)
            
            if not context:
                return current_message
            
            # Формируем краткую историю диалога (последние 4 сообщения)
            dialog_history = []
            for msg in context[-4:]:
                role = "Студент" if msg['is_user'] else "ExamFlow AI"
                dialog_history.append(f"{role}: {msg['text']}")
            
            # Добавляем текущее сообщение
            dialog_history.append(f"Студент: {current_message}")
            
            formatted_context = f"""ПРЕДЫДУЩИЙ ДИАЛОГ:
{chr(10).join(dialog_history)}

ИНСТРУКЦИЯ: Учитывай предыдущие сообщения. Если студент продолжает тему - развивай её. Если уточняет - отвечай с учетом контекста."""
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Ошибка форматирования веб-контекста: {e}")
            return current_message
    
    def clear_context(self, session_id: str) -> bool:
        """Очищает контекст сессии"""
        try:
            cache_key = self._get_cache_key(session_id)
            cache.delete(cache_key)
            logger.info(f"Веб-контекст сессии {session_id[:8]}... очищен")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки веб-контекста: {e}")
            return False
    
    def get_context_info(self, session_id: str) -> Dict:
        """Получает информацию о контексте"""
        try:
            context = self.get_context(session_id)
            
            return {
                'messages_count': len(context),
                'has_context': len(context) > 0,
                'last_activity': context[-1]['timestamp'] if context else None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о веб-контексте: {e}")
            return {'messages_count': 0, 'has_context': False}
