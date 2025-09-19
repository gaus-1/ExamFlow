"""
Locust конфигурация для ExamFlow load тестирования
"""

from locust import HttpUser, task, between
from .test_performance import ExamFlowUser, ExamFlowAPIUser, ExamFlowHeavyUser


# Конфигурация для разных сценариев тестирования
class WebsiteUser(ExamFlowUser):
    """Обычный пользователь веб-сайта"""
    pass


class APIUser(ExamFlowAPIUser):
    """API пользователь"""
    pass


class HeavyUser(ExamFlowHeavyUser):
    """Тяжелый пользователь для стресс-тестирования"""
    pass
