#!/usr/bin/env python3
"""
Прямой запуск ExamFlow Bot для Windows Service
"""

import os
import sys
import asyncio
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

# Импортируем бота
from telegram_bot.bot_simple import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)
