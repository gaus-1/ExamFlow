"""
Команда для установки webhook Telegram бота
"""

import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Устанавливает webhook для Telegram бота"

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Удалить webhook")
        parser.add_argument("--url", type=str, help="Кастомный URL для webhook")

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")

        if not token:
            self.stdout.write(self.style.ERROR("❌ TELEGRAM_BOT_TOKEN не настроен"))  # type: ignore
            return

        # Определяем URL
        if options.get("delete"):
            webhook_url = ""
            self.stdout.write("🗑️ Удаляем webhook...")
        elif options.get("url"):
            webhook_url = options["url"]
        else:
            # Автоматически определяем правильный URL
            site_url = getattr(settings, "SITE_URL", "https://examflow.ru")
            if "localhost" in site_url or "127.0.0.1" in site_url:
                # Для локальной разработки - удаляем webhook
                webhook_url = ""
                self.stdout.write(
                    "🏠 Локальная разработка - удаляем webhook для polling режима"
                )
            else:
                webhook_url = f"{site_url}/bot/webhook/"

        self.stdout.write(f"🔗 Устанавливаем webhook: {webhook_url}")

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={"url": webhook_url},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.stdout.write(self.style.SUCCESS("✅ Webhook установлен успешно!"))  # type: ignore
                    self.stdout.write(f"📍 URL: {webhook_url}")
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Ошибка: {data.get("description")}'))  # type: ignore
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP {response.status_code}: {response.text}"))  # type: ignore

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка установки webhook: {e}"))  # type: ignore
