"""
Сервис для управления сессиями чата пользователей с ботом
"""

import uuid
from typing import Optional, Dict, Any
from django.utils import timezone
from datetime import timedelta
from core.models import ChatSession


class ChatSessionService:
    """Сервис для управления сессиями чата"""
    
    @staticmethod
    def get_or_create_session(telegram_id: int, user=None) -> ChatSession:
        """Получает или создает сессию чата для пользователя"""
        # Ищем активную сессию (не старше 24 часов)
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        session = ChatSession.objects.filter( # type: ignore
            telegram_id=telegram_id,
            last_activity__gte=cutoff_time
        ).first()
        
        if session:
            # Обновляем время последней активности
            session.last_activity = timezone.now()
            session.save()
            return session
        
        # Создаем новую сессию
        session_id = f"session_{telegram_id}_{uuid.uuid4().hex[:8]}"
        
        session = ChatSession.objects.create( # type: ignore
            user=user,
            telegram_id=telegram_id,
            session_id=session_id,
            context_messages=[],
            max_context_length=10
        )
        
        return session
    
    @staticmethod
    def add_user_message(session: ChatSession, message: str):
        """Добавляет сообщение пользователя в контекст"""
        session.add_message('user', message)
    
    @staticmethod
    def add_assistant_message(session: ChatSession, message: str):
        """Добавляет ответ ассистента в контекст"""
        session.add_message('assistant', message)
    
    @staticmethod
    def get_context_for_ai(session: ChatSession) -> str:
        """Возвращает контекст в формате для ИИ"""
        return session.get_context_for_ai()
    
    @staticmethod
    def clear_session_context(session: ChatSession):
        """Очищает контекст сессии"""
        session.clear_context()
    
    @staticmethod
    def create_enhanced_prompt(user_message: str, session: ChatSession) -> str:
        """Создает расширенный промпт с контекстом"""
        context = session.get_context_for_ai()
        
        if context:
            enhanced_prompt = f"""Контекст предыдущего разговора:
{context}

Текущий вопрос пользователя: {user_message}

Пожалуйста, ответь на текущий вопрос, учитывая контекст предыдущего разговора."""
        else:
            enhanced_prompt = user_message
        
        return enhanced_prompt
    
    @staticmethod
    def cleanup_old_sessions():
        """Очищает старые сессии (старше 7 дней)"""
        cutoff_time = timezone.now() - timedelta(days=7)
        ChatSession.objects.filter(last_activity__lt=cutoff_time).delete() # type: ignore   
