"""
Программное применение миграций без интерактива, чтобы обойти зависание shell.
Запуск (PowerShell, из корня проекта):
  ./venv/Scripts/Activate.ps1
  python scripts/apply_migrations.py
"""

import os


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
    try:
        import django
        from django.core.management import call_command
    except Exception as exc:  # type: ignore
        print(f"[apply_migrations] Ошибка импорта Django: {exc}")
        return 1

    django.setup()

    try:
        # Сначала локальная миграция для telegram_auth до 0002
        call_command("migrate", "telegram_auth", "0002", interactive=False, verbosity=1)
    except Exception as exc:  # type: ignore
        print(f"[apply_migrations] Предупреждение: migrate telegram_auth 0002: {exc}")

    try:
        # Затем все миграции целиком
        call_command("migrate", interactive=False, verbosity=1)
    except Exception as exc:  # type: ignore
        print(f"[apply_migrations] Ошибка общего migrate: {exc}")
        return 2

    print("[apply_migrations] Миграции применены успешно.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


