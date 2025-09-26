"""
Команда для проверки webhook на Render
"""

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Проверяет webhook на Render"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Проверка webhook на Render")
        self.stdout.write("=" * 50)

        # Получаем токен
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not token:
            self.stdout.write("❌ TELEGRAM_BOT_TOKEN не настроен!")
            return

        # Получаем SITE_URL
        site_url = getattr(settings, "SITE_URL", None)
        if not site_url:
            self.stdout.write("❌ SITE_URL не настроен!")
            return

        self.stdout.write("🌐 SITE_URL: {site_url}")

        # Проверяем текущий webhook
        try:
            response = requests.get(
                "https://api.telegram.org/bot{token}/getWebhookInfo"
            )
            webhook_info = response.json()

            if webhook_info.get("ok"):
                current_url = webhook_info.get("result", {}).get("url", "")
                if current_url:
                    self.stdout.write("✅ Текущий webhook: {current_url}")

                    # Проверяем, правильно ли настроен
                    expected_url = "{site_url}/bot/webhook/"
                    if current_url == expected_url:
                        self.stdout.write("✅ Webhook настроен правильно!")
                    else:
                        self.stdout.write("⚠️  Webhook настроен на другой URL")
                        self.stdout.write("   Ожидается: {expected_url}")
                        self.stdout.write("   Текущий:  {current_url}")
                else:
                    self.stdout.write("❌ Webhook не настроен")
            else:
                self.stdout.write("❌ Ошибка получения webhook: {webhook_info}")

        except Exception:
            self.stdout.write("❌ Ошибка проверки webhook: {e}")

        # Пытаемся настроить webhook
        self.stdout.write("\n🔄 Настройка webhook...")
        try:
            webhook_url = "{site_url}/bot/webhook/"
            response = requests.post(
                "https://api.telegram.org/bot{token}/setWebhook",
                json={"url": webhook_url},
            )

            result = response.json()
            if result.get("ok"):
                self.stdout.write("✅ Webhook успешно настроен!")
                self.stdout.write("   URL: {webhook_url}")
            else:
                self.stdout.write("❌ Ошибка настройки webhook: {result}")

        except Exception:
            self.stdout.write("❌ Ошибка настройки webhook: {e}")

        # Проверяем доступность webhook endpoint
        self.stdout.write("\n🌐 Проверка доступности webhook endpoint...")
        try:
            test_url = "{site_url}/bot/test/"
            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                self.stdout.write(
                    "✅ Webhook endpoint доступен: HTTP {response.status_code}"
                )
                try:
                    data = response.json()
                    self.stdout.write(
                        "📊 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}"
                    )
                except BaseException:
                    self.stdout.write("📊 Ответ: {response.text[:200]}")
            else:
                self.stdout.write(
                    "❌ Webhook endpoint недоступен: HTTP {response.status_code}"
                )

        except requests.exceptions.ConnectionError:
            self.stdout.write("❌ Ошибка соединения с webhook endpoint")
            self.stdout.write("   Возможно, сайт еще не запущен на Render")
        except Exception:
            self.stdout.write("❌ Ошибка проверки webhook endpoint: {e}")

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("🏁 Проверка webhook завершена")
