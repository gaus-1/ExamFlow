"""
Формы для legacy функциональности core модуля

ВНИМАНИЕ: Основные формы аутентификации перенесены в authentication.forms
Этот файл содержит только legacy формы для обратной совместимости.
"""

# Импортируем формы из нового модуля для обратной совместимости
try:
    from authentication.forms import TechRegisterForm, TechLoginForm, ProfileUpdateForm  # type: ignore
    __all__ = ['TechRegisterForm', 'TechLoginForm', 'ProfileUpdateForm']
except ImportError:
    # Если модуль authentication недоступен, создаем заглушки
    class TechRegisterForm:
        pass

    class TechLoginForm:
        pass

    class ProfileUpdateForm:
        pass

    __all__ = []
