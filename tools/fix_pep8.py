#!/usr/bin/env python3
"""
Скрипт для автоматического исправления основных PEP 8 ошибок
"""

import os
import subprocess


def fix_pep8_issues():
    """Исправляет основные PEP 8 проблемы"""

    # Директории для обработки
    dirs_to_fix = [
        "ai",
        "core",
        "authentication",
        "learning",
        "telegram_bot",
        "analytics",
        "themes",
    ]

    print("🔧 Начинаем исправление PEP 8 ошибок...")

    for dir_name in dirs_to_fix:
        if os.path.exists(dir_name):
            print("📁 Обрабатываем {dir_name}/")

            # Запускаем autopep8 для автоматического исправления
            try:
                result = subprocess.run(
                    [
                        "autopep8",
                        "--in-place",
                        "--aggressive",
                        "--aggressive",
                        "--max-line-length=88",
                        "--recursive",
                        dir_name,
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("✅ {dir_name}/ - исправлено")
                else:
                    print("⚠️ {dir_name}/ - ошибки: {result.stderr}")

            except FileNotFoundError:
                print("❌ autopep8 не установлен. Устанавливаем...")
                subprocess.run(["pip", "install", "autopep8"])
                continue

    print("🎉 Исправление завершено!")


def remove_unused_imports():
    """Удаляет неиспользуемые импорты"""

    print("🧹 Удаляем неиспользуемые импорты...")

    try:
        # Устанавливаем autoflake если не установлен
        subprocess.run(["pip", "install", "autoflake"], check=True)

        # Удаляем неиспользуемые импорты
        result = subprocess.run(
            [
                "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-unused-variables",
                "--recursive",
                "ai",
                "core",
                "authentication",
                "learning",
                "telegram_bot",
                "analytics",
                "themes",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Неиспользуемые импорты удалены")
        else:
            print("⚠️ Ошибки при удалении импортов: {result.stderr}")

    except Exception:
        print("❌ Ошибка: {e}")


if __name__ == "__main__":
    fix_pep8_issues()
    remove_unused_imports()

    print("\n📊 Проверяем результат...")
    subprocess.run(["flake8", "--max-line-length=88", "--statistics", "."])
