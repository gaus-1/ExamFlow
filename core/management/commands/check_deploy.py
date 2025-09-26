from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Проверка готовности к деплою"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Проверяем готовность к деплою...")

        # Проверяем настройки
        self.stdout.write(f"✅ DEBUG = {settings.DEBUG}")
        self.stdout.write(f"✅ ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}")
        self.stdout.write(f"✅ STATIC_URL = {settings.STATIC_URL}")
        self.stdout.write(f"✅ STATIC_ROOT = {settings.STATIC_ROOT}")

        # Проверяем переменные окружения
        self.stdout.write(
            "✅ SECRET_KEY установлен: {}".format(
                "Да"
                if not settings.SECRET_KEY.startswith("django-insecure")
                else "НЕТ!"
            )
        )

        # Проверяем базу данных
        try:
            from django.db import connection

            connection.cursor()
            self.stdout.write("✅ База данных доступна")
        except Exception as e:
            self.stdout.write(f"❌ Ошибка базы данных: {e}")

        self.stdout.write("🎉 Проверка завершена!")
