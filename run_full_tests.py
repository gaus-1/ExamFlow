#!/usr/bin/env python
"""Скрипт для запуска полного набора тестов с покрытием"""
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, keepdb=True)

    # Запускаем все unit тесты
    print("🚀 Запуск полного набора unit тестов...")
    failures = test_runner.run_tests(["tests.unit"])

    if failures:
        print(f"❌ Тесты завершились с {failures} ошибками")
        sys.exit(1)
    else:
        print("✅ Все тесты прошли успешно!")
        sys.exit(0)
