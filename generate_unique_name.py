#!/usr/bin/env python3
"""
Генератор уникальных имен для Render сервиса
"""

import random
import string
from datetime import datetime


def generate_unique_name():
    """Генерирует уникальное имя для Render сервиса"""

    # Базовое имя
    base_name = "examflow"

    # Варианты суффиксов
    suffixes = [
        # С датой
        f"-{datetime.now().strftime('%Y-%m-%d')}",
        f"-{datetime.now().strftime('%m%d')}",
        f"-{datetime.now().year}",
        # С случайными символами
        f"-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}",
        f"-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}",
        # С версиями
        "-v2",
        "-v3",
        "-new",
        "-backup",
        "-main",
        # С описанием
        "-platform",
        "-service",
        "-web-app",
        "-learning-hub",
        "-edu-system",
    ]

    # Генерируем несколько вариантов
    names = []
    for suffix in suffixes:
        names.append(base_name + suffix)

    # Добавляем варианты с цифрами
    for i in range(1, 10):
        names.append(f"{base_name}-{i}")
        names.append(f"{base_name}-{i:02d}")

    # Добавляем варианты с префиксами
    prefixes = ["my-", "new-", "app-", "web-"]
    for prefix in prefixes:
        names.append(f"{prefix}{base_name}")
        names.append(f"{prefix}{base_name}-{datetime.now().strftime('%m%d')}")

    return names


def main():
    """Главная функция"""
    print("🎯 Генератор уникальных имен для Render сервиса")
    print("=" * 50)

    names = generate_unique_name()

    print("📝 Попробуйте эти имена (по порядку):")
    print()

    for i, name in enumerate(names[:20], 1):  # Показываем первые 20
        print(f"{i:2d}. {name}")

    print()
    print("💡 Если все заняты, запустите скрипт еще раз для новых вариантов!")
    print()

    # Показываем случайный вариант
    random_name = random.choice(names)
    print(f"🎲 Случайный вариант: {random_name}")

    print()
    print("🔗 Создавайте сервис на: https://dashboard.render.com")


if __name__ == "__main__":
    main()
