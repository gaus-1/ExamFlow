"""
Команда для полной диагностики Telegram бота
Проверяет все аспекты работы бота
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import requests

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Полная диагностика Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write('🔍 ПОЛНАЯ ДИАГНОСТИКА TELEGRAM БОТА')
        self.stdout.write('=' * 60)

        # 1. Проверяем переменные окружения
        self.stdout.write('\n📋 1. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:')
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if token:
            self.stdout.write('   ✅ TELEGRAM_BOT_TOKEN: {token[:10]}...')
        else:
            self.stdout.write('   ❌ TELEGRAM_BOT_TOKEN: НЕ НАЙДЕН')
            return

        site_url = getattr(settings, 'SITE_URL', None)
        if site_url:
            self.stdout.write('   ✅ SITE_URL: {site_url}')
        else:
            self.stdout.write('   ❌ SITE_URL: НЕ НАЙДЕН')
            return

        # 2. Проверяем базу данных
        self.stdout.write('\n🗄️ 2. БАЗА ДАННЫХ:')
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write('   ✅ База данных доступна')
        except Exception as e:
            self.stdout.write('   ❌ Ошибка базы данных: {e}')
            return

        # 3. Проверяем создание бота
        self.stdout.write('\n🤖 3. СОЗДАНИЕ БОТА:')
        try:
            from telegram_bot.bot_main import get_bot
            bot = get_bot()
            if bot:
                self.stdout.write('   ✅ Экземпляр бота создан')
            else:
                self.stdout.write('   ❌ Бот не создан')
                return
        except Exception as e:
            self.stdout.write('   ❌ Ошибка создания бота: {e}')
            return

        # 4. Проверяем API бота
        self.stdout.write('\n🌐 4. API БОТА:')
        try:
            import asyncio
            bot_info = asyncio.run(bot.get_me())
            self.stdout.write(
                '   ✅ Бот доступен: @{bot_info.username} (ID: {bot_info.id})')
        except Exception as e:
            self.stdout.write('   ❌ Ошибка API бота: {e}')
            return

        # 5. Проверяем webhook
        self.stdout.write('\n🔗 5. WEBHOOK:')
        webhook_url = "{site_url}/bot/webhook/"
        self.stdout.write('   Webhook URL: {webhook_url}')

        try:
            # Проверяем текущий webhook
            response = requests.get(
                "https://api.telegram.org/bot{token}/getWebhookInfo")
            webhook_info = response.json()

            if webhook_info.get('ok'):
                current_url = webhook_info.get('result', {}).get('url', '')
                if current_url:
                    self.stdout.write('   ✅ Текущий webhook: {current_url}')
                    if current_url == webhook_url:
                        self.stdout.write('   ✅ Webhook настроен правильно')
                    else:
                        self.stdout.write('   ⚠️  Webhook настроен на другой URL')
                else:
                    self.stdout.write('   ❌ Webhook не настроен')
            else:
                self.stdout.write('   ❌ Ошибка получения webhook: {webhook_info}')

        except Exception as e:
            self.stdout.write('   ❌ Ошибка проверки webhook: {e}')

        # 6. Проверяем доступность webhook endpoint
        self.stdout.write('\n🌐 6. ДОСТУПНОСТЬ WEBHOOK ENDPOINT:')
        try:
            # Тестируем webhook endpoint
            test_url = "{site_url}/bot/test/"
            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                self.stdout.write(
                    '   ✅ Webhook endpoint доступен: HTTP {response.status_code}')
                try:
                    data = response.json()
                    self.stdout.write(
                        '   📊 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}')
                except BaseException:
                    self.stdout.write('   📊 Ответ: {response.text[:200]}')
            else:
                self.stdout.write(
                    '   ❌ Webhook endpoint недоступен: HTTP {response.status_code}')

        except requests.exceptions.ConnectionError:
            self.stdout.write('   ❌ Ошибка соединения с webhook endpoint')
        except Exception as e:
            self.stdout.write('   ❌ Ошибка проверки webhook endpoint: {e}')

        # 7. Тестируем отправку сообщения
        self.stdout.write('\n📤 7. ТЕСТ ОТПРАВКИ СООБЩЕНИЯ:')
        try:
            # Пытаемся отправить тестовое сообщение
            test_message = "🧪 Тестовое сообщение от ExamFlow"
            response = requests.post(
                "https://api.telegram.org/bot{token}/sendMessage",
                json={
                    'chat_id': 123456789,  # Несуществующий chat_id для теста
                    'text': test_message
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.stdout.write('   ✅ API отправки сообщений работает')
                else:
                    error_code = result.get('error_code', 'unknown')
                    if error_code == 400:  # Bad Request - нормально для несуществующего chat_id
                        self.stdout.write(
                            '   ✅ API отправки сообщений работает (ошибка 400 ожидаема)')
                    else:
                        self.stdout.write('   ⚠️  API работает, но ошибка: {result}')
            else:
                self.stdout.write('   ❌ Ошибка API: HTTP {response.status_code}')

        except Exception as e:
            self.stdout.write('   ❌ Ошибка тестирования API: {e}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('🏁 ДИАГНОСТИКА ЗАВЕРШЕНА')

        # Рекомендации
        self.stdout.write('\n💡 РЕКОМЕНДАЦИИ:')
        if site_url and not site_url.startswith('https://'):
            self.stdout.write(
                '   ⚠️  SITE_URL должен начинаться с https:// для webhook')
        if not token:
            self.stdout.write(
                '   ❌ Установите TELEGRAM_BOT_TOKEN в Environment Variables')
        else:
            self.stdout.write('   ✅ TELEGRAM_BOT_TOKEN настроен')
