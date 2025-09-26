#!/usr/bin/env python3
"""
Скрипт для запуска тестов ExamFlow
"""

import os

import django

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
django.setup()

# Запуск тестов
from django.core.management import execute_from_command_line  # noqa: E402

if __name__ == "__main__":
    # Запускаем тесты
    execute_from_command_line(
        [
            "manage.py",
            "test",
            "tests.test_learning.TestLearning.test_subject_creation",
            "-v",
            "2",
        ]
    )
