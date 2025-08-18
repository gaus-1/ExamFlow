"""
Модели для модуля аутентификации

В данный момент используем модели из core:
- User (встроенная модель Django)
- UserProfile (из core.models)
- Subscription (из core.models)

В будущем можно перенести сюда специфичные для аутентификации модели.
"""

# Импортируем модели из core для обратной совместимости
from core.models import UserProfile, Subscription

__all__ = ['UserProfile', 'Subscription']
