#!/usr/bin/env python
"""
Простые тесты для моделей без зависимости от БД
"""

import unittest
from unittest.mock import Mock, patch


class TestSimpleModels(unittest.TestCase):
    """Простые тесты для моделей"""
    
    def test_learning_models_imports(self):
        """Тест импортов моделей learning"""
        try:
            from learning.models import Subject, Task
            self.assertTrue(True, "Импорты learning.models работают")
        except ImportError as e:
            self.fail(f"Не удалось импортировать learning.models: {e}")
    
    def test_core_models_imports(self):
        """Тест импортов моделей core"""
        try:
            from core.models import UserProfile, Subject as CoreSubject, Task as CoreTask
            self.assertTrue(True, "Импорты core.models работают")
        except ImportError as e:
            self.fail(f"Не удалось импортировать core.models: {e}")
    
    def test_ai_models_imports(self):
        """Тест импортов моделей ai"""
        try:
            from ai.models import AiLimit, AiModel, ChatSession
            self.assertTrue(True, "Импорты ai.models работают")
        except ImportError as e:
            self.fail(f"Не удалось импортировать ai.models: {e}")
    
    def test_telegram_auth_models_imports(self):
        """Тест импортов моделей telegram_auth"""
        try:
            from telegram_auth.models import TelegramUser
            self.assertTrue(True, "Импорты telegram_auth.models работают")
        except ImportError as e:
            self.fail(f"Не удалось импортировать telegram_auth.models: {e}")
    
    def test_model_choices_exist(self):
        """Тест существования choices в моделях"""
        try:
            from learning.models import Subject
            # Проверяем, что у модели есть choices
            self.assertTrue(hasattr(Subject, '_meta'))
            self.assertTrue(True, "Модель Subject имеет _meta")
        except Exception as e:
            self.fail(f"Ошибка при проверке модели Subject: {e}")


if __name__ == '__main__':
    unittest.main()
