from __future__ import annotations

from core.container import Container

try:
    from telegram_bot.bot_handlers import (
        db_create_enhanced_prompt as _legacy_create_enhanced_prompt,  # type: ignore
        db_add_user_message_to_session as _legacy_add_user_message,  # type: ignore
        db_add_assistant_message_to_session as _legacy_add_assistant_message,  # type: ignore
        db_get_or_create_chat_session as _legacy_get_or_create_chat_session,  # type: ignore
    )
except Exception:
    def _legacy_create_enhanced_prompt(user_message: str, session) -> str:  # type: ignore
        return user_message

    def _legacy_add_user_message(session, message):  # type: ignore
        return None

    def _legacy_add_assistant_message(session, message):  # type: ignore
        return None

    def _legacy_get_or_create_chat_session(telegram_user, django_user=None):  # type: ignore
        return None


# Фасадные функции (тонкие обёртки)

def get_or_create_chat_session(telegram_user, django_user=None):  # type: ignore
    return _legacy_get_or_create_chat_session(telegram_user, django_user)


def create_enhanced_prompt(user_message: str, session) -> str:
    return _legacy_create_enhanced_prompt(user_message, session)


def add_user_message_to_session(session, message) -> None:
    _legacy_add_user_message(session, message)


def add_assistant_message_to_session(session, message) -> None:
    _legacy_add_assistant_message(session, message)


def get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:
    """Получает ответ от AI с памятью контекста."""
    try:
        # Импортируем менеджер контекста
        from telegram_bot.memory import BotContextManager
        
        # Используем экстренный AI API для бота (прямой Gemini)
        import google.generativeai as genai
        from django.conf import settings
        
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return 'Сервис ИИ временно недоступен'
        
        # Настраиваем Gemini
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
        
        # Инициализируем менеджер контекста
        context_manager = BotContextManager()
        
        # Получаем ID пользователя
        user_id = getattr(user, 'telegram_id', None) if user else None
        if not user_id and hasattr(user, 'id'):
            user_id = user.id
        
        # Формируем промпт с контекстом
        if user_id:
            prompt_with_context = context_manager.format_context_for_ai(user_id, prompt)
        else:
            prompt_with_context = prompt
        
        # Создаем промпт с ролью ExamFlow
        system_prompt = """Ты - ExamFlow AI, дружелюбный помощник для подготовки к ЕГЭ и ОГЭ.

Специализируешься на:
📐 Математике (профильная и базовая, ОГЭ) - уравнения, функции, геометрия, алгебра
📝 Русском языке (ЕГЭ и ОГЭ) - грамматика, орфография, сочинения, литература

Стиль общения:
- Дружелюбный и поддерживающий
- Иногда добавляй уместные шутки по теме
- Представляйся как "ExamFlow AI" 
- Помогай конкретными примерами и пошаговыми решениями
- ВАЖНО: Учитывай предыдущие сообщения студента для персонализации
- Если студент продолжает тему - развивай её дальше
- Если вопрос не по твоим предметам - вежливо перенаправь на математику или русский

Отвечай кратко и по делу, максимум 400 слов."""

        full_prompt = f"{system_prompt}\n\n{prompt_with_context}"
        
        # Получаем ответ
        response = model.generate_content(full_prompt)
        
        if response.text:
            answer = response.text.strip()
            
            # Сохраняем сообщения в контекст
            if user_id:
                context_manager.add_message(user_id, prompt, is_user=True)
                context_manager.add_message(user_id, answer, is_user=False)
            
            # Ограничиваем длину для Telegram
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
            return answer
        else:
            return 'Не удалось получить ответ от ИИ. Попробуйте переформулировать вопрос.'
    except Exception as e:
        # type: ignore
        import logging  # Импортируем логгер, если не был импортирован ранее
        logging.error(f"Ошибка AI сервиса с контекстом: {e}")
        return f'Ошибка AI сервиса: попробуйте позже'
