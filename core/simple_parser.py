"""
Простой парсер для тестирования
"""

import logging
from learning.models import Subject, Task
from django.utils import timezone

logger = logging.getLogger(__name__)

def create_sample_data():
    """Создает тестовые данные"""
    try:
        # Создаем тестовый предмет
        subject, created = Subject.objects.get_or_create(  # type: ignore
            name="Математика (ЕГЭ)",
            defaults={'exam_type': 'ЕГЭ'}
        )

        if created:
            logger.info("Создан тестовый предмет: Математика (ЕГЭ)")

        # Создаем тестовые задания
        sample_tasks = [
                'title': 'Решение квадратных уравнений',
                'description': 'Решите квадратное уравнение x² + 5x + 6 = 0',
                'difficulty': 3,
                'source': 'Тестовые данные'
            },
                'title': 'Логарифмические уравнения',
                'description': 'Решите уравнение log₂(x + 3) = 4',
                'difficulty': 4,
                'source': 'Тестовые данные'
            }
        ]

        created_tasks = 0
        for task_data in sample_tasks:
            task, created = Task.objects.get_or_create(  # type: ignore
                title=task_data['title'],
                subject=subject,
                defaults={
                    'description': task_data['description'],
                    'difficulty': task_data['difficulty'],
                    'source': task_data['source'],
                    'created_at': timezone.now()
                }
            )

            if created:
                created_tasks += 1
                logger.info("Создано задание: {task_data['title']}")

        logger.info("Создано {created_tasks} новых заданий")
        return True

    except Exception as e:
        logger.error("Ошибка создания тестовых данных: {e}")
        return False

def run_test():
    """Запускает тест"""
    return create_sample_data()
