from __future__ import annotations


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


def detect_subject_from_prompt(prompt: str) -> str:
    """Определяет предмет по тексту промпта"""
    prompt_lower = prompt.lower()
    
    # Ключевые слова для математики
    math_keywords = [
        'математика', 'матем', 'уравнение', 'функция', 'производная', 'интеграл',
        'геометрия', 'алгебра', 'тригонометрия', 'логарифм', 'степень', 'корень',
        'система уравнений', 'неравенство', 'график', 'координаты', 'вектор',
        'площадь', 'объем', 'угол', 'треугольник', 'круг', 'окружность',
        'егэ математика', 'огэ математика', 'профильная математика', 'базовая математика'
    ]
    
    # Ключевые слова для русского языка
    russian_keywords = [
        'русский язык', 'русский', 'сочинение', 'изложение', 'орфография', 'пунктуация',
        'грамматика', 'морфология', 'синтаксис', 'лексика', 'фонетика', 'стилистика',
        'причастие', 'деепричастие', 'существительное', 'прилагательное', 'глагол',
        'подлежащее', 'сказуемое', 'определение', 'дополнение', 'обстоятельство',
        'егэ русский', 'огэ русский', 'егэ сочинение', 'огэ изложение'
    ]
    
    # Подсчитываем совпадения
    math_score = sum(1 for keyword in math_keywords if keyword in prompt_lower)
    russian_score = sum(1 for keyword in russian_keywords if keyword in prompt_lower)
    
    if math_score > russian_score:
        return 'math'
    elif russian_score > math_score:
        return 'russian'
    else:
        return 'chat'  # Если не удалось определить


def get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:
    """Получает ответ от AI с памятью контекста."""
    try:
        # Определяем предмет по промпту
        detected_subject = detect_subject_from_prompt(prompt)
        
        # Импортируем менеджер контекста
        from telegram_bot.memory import BotContextManager
        
        # Используем экстренный AI API для бота (прямой Gemini)
        import google.generativeai as genai
        from django.conf import settings
        
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return 'Сервис ИИ временно недоступен'
        
        # Получаем конфигурацию для определенного предмета
        task_configs = getattr(settings, 'GEMINI_TASK_CONFIGS', {})
        config = task_configs.get(detected_subject, task_configs.get('chat', {}))
        
        # Настраиваем Gemini с правильной конфигурацией
        genai.configure(api_key=api_key)  # type: ignore
        model_name = config.get('model', 'gemini-1.5-flash')
        model = genai.GenerativeModel(model_name)  # type: ignore
        
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
        
        # Создаем промпт с ролью ExamFlow на основе определенного предмета
        base_prompt = config.get('system_prompt', 'Ты - ExamFlow AI, эксперт по подготовке к ЕГЭ и ОГЭ.')
        
        if detected_subject == 'math':
            system_prompt = f"""{base_prompt}

📐 МАТЕМАТИКА (ЕГЭ/ОГЭ):
- Давай пошаговые решения
- Объясняй каждый шаг
- Показывай альтернативные методы
- Указывай типичные ошибки
- Отвечай кратко (до 400 слов)

🚫 НЕ упоминай провайдера ИИ"""
        
        elif detected_subject == 'russian':
            system_prompt = f"""{base_prompt}

📝 РУССКИЙ ЯЗЫК (ЕГЭ/ОГЭ):
- Помогай с грамматикой и орфографией
- Давай образцы сочинений
- Объясняй правила простыми словами
- Показывай примеры
- Отвечай кратко (до 350 слов)

🚫 НЕ упоминай провайдера ИИ"""
        
        else:
            system_prompt = f"""{base_prompt}

🎯 СПЕЦИАЛИЗАЦИЯ: Математика и Русский язык (ЕГЭ/ОГЭ)
📐 МАТЕМАТИКА: уравнения, функции, геометрия, алгебра
📝 РУССКИЙ ЯЗЫК: грамматика, сочинения, орфография

💬 СТИЛЬ: Кратко и по делу (до 300 слов)
🚫 НЕ упоминай провайдера ИИ
🚫 Если вопрос не по твоим предметам - скажи: "Я специализируюсь на математике и русском языке!"""

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
        return 'Ошибка AI сервиса: попробуйте позже'
