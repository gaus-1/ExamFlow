#!/usr/bin/env python3
"""
Прямой запуск ExamFlow Bot для Windows Service
"""

import os
import sys

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')

import django
django.setup()

# Импортируем рабочего бота
from bot_working import main

if __name__ == "__main__":
    try:
        main()  # Без asyncio.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)
