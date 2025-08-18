"""
Модели для модуля обучения

Содержит основные модели для работы с образовательным контентом:
- Предметы (Subject)
- Темы (Topic) 
- Задания (Task)
- Прогресс пользователей (UserProgress)
- Достижения (Achievement)
- Рейтинги (UserRating)
"""

# Импортируем модели из core для обратной совместимости
from core.models import (
    ExamType, Subject, Topic, Task, 
    UserProgress, UserRating, Achievement
)

__all__ = [
    'ExamType', 'Subject', 'Topic', 'Task',
    'UserProgress', 'UserRating', 'Achievement'
]
