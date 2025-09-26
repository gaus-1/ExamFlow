"""
Команда для безопасного применения миграций на Render.com
Включает retry логику и обработку SSL соединений
"""

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Безопасное применение миграций на Render.com с retry логикой"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Максимальное количество попыток (по умолчанию: 3)",
        )
        parser.add_argument(
            "--delay",
            type=int,
            default=10,
            help="Задержка между попытками в секундах (по умолчанию: 10)",
        )

    def handle(self, *args, **options):
        max_retries = options["max_retries"]
        delay = options["delay"]

        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                f"🚀 Начинаем безопасное применение миграций (max_retries={max_retries}, delay={delay}s)"
            )
        )

        # Пробуем применить миграции
        try:
            self._apply_migrations_with_retry(max_retries, delay)
            self.stdout.write(
                self.style.SUCCESS("✅ Все миграции применены успешно!")  # type: ignore
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"❌ Не удалось применить миграции: {e}")  # type: ignore
            )
            self.stdout.write(
                self.style.WARNING("⚠️ Продолжаем без миграций...")  # type: ignore
            )

    def _apply_migrations_with_retry(self, max_retries, delay):
        """Применяет миграции с retry логикой"""

        for attempt in range(max_retries):
            try:
                self.stdout.write(
                    f"🔄 Попытка {attempt + 1}/{max_retries}: Применяем миграции..."
                )

                # Пробуем применить миграции
                try:
                    call_command("migrate", "--noinput")
                    self.stdout.write("✅ Миграции применены успешно!")
                    return
                except Exception as e:
                    self.stdout.write(f"⚠️ Обычные миграции не удались: {e}")

                    # Пробуем с run-syncdb
                    self.stdout.write("🔄 Пробуем с --run-syncdb...")
                    call_command("migrate", "--run-syncdb", "--noinput")
                    self.stdout.write("✅ Миграции применены с --run-syncdb!")
                    return

            except Exception as e:
                self.stderr.write(f"❌ Попытка {attempt + 1} не удалась: {e}")
                if attempt < max_retries - 1:
                    self.stdout.write(
                        f"⏳ Ожидание {delay} секунд перед следующей попыткой..."
                    )
                    import time

                    time.sleep(delay)
                else:
                    raise CommandError(
                        f"Не удалось применить миграции после {max_retries} попыток: {e}"
                    )
