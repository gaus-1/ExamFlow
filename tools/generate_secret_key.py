#!/usr/bin/env python3
"""
Утилита для генерации безопасного SECRET_KEY для ExamFlow 2.0
"""

import secrets
import string

from django.core.management.utils import get_random_secret_key


def generate_django_secret_key():
    """Генерирует SECRET_KEY используя Django утилиту"""
    return get_random_secret_key()


def generate_custom_secret_key(length=64):
    """Генерирует кастомный SECRET_KEY заданной длины"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Убираем символы, которые могут вызвать проблемы в .env файле
    alphabet = alphabet.replace('"', "").replace("'", "").replace("\\", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    """Основная функция"""
    print("🔐 Генерация SECRET_KEY для ExamFlow 2.0")
    print("=" * 60)

    # Генерируем Django SECRET_KEY
    django_key = generate_django_secret_key()
    print("🎯 Django SECRET_KEY ({len(django_key)} символов):")
    print("SECRET_KEY={django_key}")
    print()

    # Генерируем кастомный SECRET_KEY
    custom_key = generate_custom_secret_key(64)
    print("🔑 Кастомный SECRET_KEY ({len(custom_key)} символов):")
    print("SECRET_KEY={custom_key}")
    print()

    # Проверяем безопасность
    print("✅ Проверка безопасности:")
    print("   Длина Django ключа: {len(django_key)} символов")
    print("   Длина кастомного ключа: {len(custom_key)} символов")
    print("   Минимальная длина: 50 символов")

    if len(django_key) >= 50 and len(custom_key) >= 50:
        print("   🎉 Все ключи соответствуют требованиям безопасности!")
    else:
        print("   ⚠️  Некоторые ключи слишком короткие!")

    print()
    print("📝 Инструкция по использованию:")
    print("1. Скопируйте один из ключей выше")
    print("2. Вставьте в переменную SECRET_KEY на Render")
    print("3. Или добавьте в .env файл локально")
    print()
    print("⚠️  ВАЖНО: Никогда не коммитьте реальные ключи в Git!")


if __name__ == "__main__":
    main()
