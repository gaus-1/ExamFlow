"""
Chat Session Service - управление сессиями чата
"""

import logging
from typing import Dict, Any, List
from django.utils import timezone

logger = logging.getLogger(__name__)


class ChatSessionService:
    """Сервис для работы с сессиями чата"""
    
    @staticmethod
    def get_or_create_chat_session(user_profile, session_type: str = "general"):
        """
        Получает или создает сессию чата
        
        Args:
            user_profile: Профиль пользователя
            session_type: Тип сессии (general, math, russian, etc.)
            
        Returns:
            Сессия чата
        """
        try:
            from core.models import ChatSession
            
            # Ищем активную сессию
            session = ChatSession.objects.filter(
                user_profile=user_profile,
                session_type=session_type,
                is_active=True
            ).first()
            
            if session:
                logger.debug(f"Найдена активная сессия {session.id} для пользователя {user_profile.telegram_id}")
                return session
            
            # Создаем новую сессию
            session = ChatSession.objects.create(
                user_profile=user_profile,
                session_type=session_type,
                is_active=True,
                created_at=timezone.now()
            )
            
            logger.info(f"Создана новая сессия {session.id} для пользователя {user_profile.telegram_id}")
            return session
            
        except Exception as e:
            logger.error(f"Ошибка создания сессии чата: {e}")
            # Возвращаем заглушку
            return ChatSessionService._create_mock_session(user_profile, session_type)

    # Методы, ожидаемые тестами unit (create/get/update/delete by user_id/session_id)
    @staticmethod
    def create_session(user_id: int, subject: str = ""):
        try:
            from django.contrib.auth import get_user_model
            from core.models import ChatSession
            import uuid
            User = get_user_model()
            user = User.objects.filter(id=user_id).first()
            if not user:
                return None
            session = ChatSession.objects.create(
                user=user,
                telegram_id=getattr(user, 'telegram_id', 0) or 0,
                session_id=str(uuid.uuid4()),
                context_messages=[{"role": "system", "content": f"Тема: {subject}"}]
            )
            return session
        except Exception as e:
            logger.error(f"Ошибка create_session: {e}")
            return None

    @staticmethod
    def get_session(user_id: int):
        try:
            from core.models import ChatSession
            return ChatSession.objects.filter(user_id=user_id).order_by('-last_activity').first()
        except Exception as e:
            logger.error(f"Ошибка get_session: {e}")
            return None

    @staticmethod
    def update_session(session_id: str, message_role: str, message_content: str) -> bool:
        try:
            from core.models import ChatSession
            session = ChatSession.objects.filter(session_id=session_id).first()
            if not session:
                return False
            session.add_message(message_role, message_content)
            session.last_activity = timezone.now()
            session.save()
            return True
        except Exception as e:
            logger.error(f"Ошибка update_session: {e}")
            return False

    @staticmethod
    def delete_session(session_id: str) -> bool:
        try:
            from core.models import ChatSession
            session = ChatSession.objects.filter(session_id=session_id).first()
            if not session:
                return False
            session.delete()
            return True
        except Exception as e:
            logger.error(f"Ошибка delete_session: {e}")
            return False
    
    @staticmethod
    def _create_mock_session(user_profile, session_type: str):
        """Создает объект-заглушку сессии"""
        class MockChatSession:
            def __init__(self):
                self.id = f"mock_{user_profile.telegram_id}_{session_type}"
                self.user_profile = user_profile
                self.session_type = session_type
                self.is_active = True
                self.created_at = timezone.now()
                self.messages = []
            
            def save(self):
                pass
        
        return MockChatSession()
    
    @staticmethod
    def add_user_message_to_session(session, message: str, message_type: str = "text"):
        """Добавляет сообщение пользователя в сессию"""
        try:
            from core.models import ChatMessage
            
            chat_message = ChatMessage.objects.create(
                session=session,
                message_type=message_type,
                content=message,
                is_from_user=True,
                timestamp=timezone.now()
            )
            
            logger.debug(f"Добавлено пользовательское сообщение в сессию {session.id}")
            return chat_message
            
        except Exception as e:
            logger.error(f"Ошибка добавления пользовательского сообщения: {e}")
            return None
    
    @staticmethod
    def add_assistant_message_to_session(session, message: str, metadata: Dict[str, Any] = None):
        """Добавляет сообщение ассистента в сессию"""
        try:
            from core.models import ChatMessage
            
            chat_message = ChatMessage.objects.create(
                session=session,
                message_type="assistant_response",
                content=message,
                is_from_user=False,
                metadata=metadata or {},
                timestamp=timezone.now()
            )
            
            logger.debug(f"Добавлено сообщение ассистента в сессию {session.id}")
            return chat_message
            
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения ассистента: {e}")
            return None
    
    @staticmethod
    def get_session_messages(session, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает сообщения сессии"""
        try:
            from core.models import ChatMessage
            
            messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-timestamp')[:limit]
            
            result = []
            for msg in reversed(messages):
                result.append({
                    'content': msg.content,
                    'is_from_user': msg.is_from_user,
                    'timestamp': msg.timestamp,
                    'message_type': msg.message_type,
                    'metadata': getattr(msg, 'metadata', {})
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений сессии: {e}")
            return []
    
    @staticmethod
    def clear_chat_session_context(session):
        """Очищает контекст сессии чата"""
        try:
            from core.models import ChatMessage
            
            # Помечаем старые сообщения как неактивные вместо удаления
            ChatMessage.objects.filter(session=session).update(is_active=False)
            
            logger.info(f"Очищен контекст сессии {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки контекста сессии: {e}")
            return False
    
    @staticmethod
    def create_enhanced_prompt(session, user_message: str, context_limit: int = 5) -> str:
        """Создает расширенный промпт с контекстом сессии"""
        try:
            # Получаем последние сообщения для контекста
            recent_messages = ChatSessionService.get_session_messages(session, context_limit)
            
            if not recent_messages:
                return user_message
            
            # Формируем контекст
            context_parts = []
            for msg in recent_messages[-context_limit:]:  # Берем последние N сообщений
                role = "Пользователь" if msg['is_from_user'] else "Ассистент"
                context_parts.append(f"{role}: {msg['content']}")
            
            # Объединяем контекст с новым сообщением
            context = "\n".join(context_parts)
            enhanced_prompt = f"Контекст беседы:\n{context}\n\nНовое сообщение пользователя: {user_message}"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Ошибка создания расширенного промпта: {e}")
            return user_message
