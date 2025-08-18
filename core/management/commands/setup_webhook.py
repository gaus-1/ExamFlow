"""
Команда для настройки Telegram webhook
"""

import requests  # type: ignore
from django.core.management.base import BaseCommand  # type: ignore
from django.conf import settings  # type: ignore


class Command(BaseCommand):
    """Команда настройки webhook для Telegram бота"""
    help = 'Настраивает webhook для Telegram бота'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['set', 'delete', 'info'],
            help='Действие: set (установить), delete (удалить), info (информация)'
        )
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help='URL для webhook (по умолчанию из SITE_URL)'
        )

    def handle(self, *args, **options):
        """Выполняет команду"""
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            self.stdout.write(
                self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не настроен в переменных окружения')
            )
            return

        action = options['action']
        
        if action == 'set':
            self._set_webhook(token, options.get('url'))
        elif action == 'delete':
            self._delete_webhook(token)
        elif action == 'info':
            self._get_webhook_info(token)

    def _set_webhook(self, token, custom_url=None):
        """Устанавливает webhook"""
        site_url = getattr(settings, 'SITE_URL', 'https://examflow.ru')
        webhook_url = custom_url or f"{site_url}/bot/webhook/"
        
        self.stdout.write(f"🔧 Настройка webhook: {webhook_url}")
        
        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query']
        }
        
        try:
            response = requests.post(api_url, json=data, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook успешно установлен!')
                )
                self.stdout.write(f"📍 URL: {webhook_url}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка установки webhook: {result.get("description", "Неизвестная ошибка")}')
                )
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка запроса: {str(e)}')
            )

    def _delete_webhook(self, token):
        """Удаляет webhook"""
        self.stdout.write("🗑️  Удаление webhook...")
        
        api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        
        try:
            response = requests.post(api_url, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook успешно удален!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка удаления webhook: {result.get("description", "Неизвестная ошибка")}')
                )
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка запроса: {str(e)}')
            )

    def _get_webhook_info(self, token):
        """Получает информацию о webhook"""
        self.stdout.write("ℹ️  Получение информации о webhook...")
        
        api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        
        try:
            response = requests.get(api_url, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                info = result.get('result', {})
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Информация о webhook:')
                )
                self.stdout.write(f"📍 URL: {info.get('url', 'Не установлен')}")
                self.stdout.write(f"🔄 Pending updates: {info.get('pending_update_count', 0)}")
                self.stdout.write(f"⏰ Last error date: {info.get('last_error_date', 'Нет')}")
                self.stdout.write(f"❌ Last error message: {info.get('last_error_message', 'Нет')}")
                
                if info.get('url'):
                    self.stdout.write("✅ Webhook активен")
                else:
                    self.stdout.write("⚠️  Webhook не настроен")
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка получения информации: {result.get("description", "Неизвестная ошибка")}')
                )
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка запроса: {str(e)}')
            )