#!/usr/bin/env python
"""Скрипт для запуска тестов с покрытием"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Запускаем unit тесты
    failures = test_runner.run_tests(["tests.unit.test_learning_models"])
    
    if failures:
        print(f"Тесты завершились с {failures} ошибками")
        sys.exit(1)
    else:
        print("Все тесты прошли успешно!")
        sys.exit(0)