"""
Команда Django для настройки Telegram webhook
"""

import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Настройка Telegram webhook для бота'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['set', 'delete', 'info'],
            help='Действие: set (установить), delete (удалить) или info (информация)',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='URL для webhook (по умолчанию из SITE_URL)',
        )

    def handle(self, *args, **options):
        action = options['action']
        
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            self.stdout.write(
                self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не настроен в settings')
            )
            return
        
        if action == 'set':
            self.set_webhook(bot_token, options.get('url'))
        elif action == 'delete':
            self.delete_webhook(bot_token)
        elif action == 'info':
            self.get_webhook_info(bot_token)

    def set_webhook(self, bot_token, custom_url=None):
        """Устанавливает webhook"""
        site_url = getattr(settings, 'SITE_URL', 'https://examflow.ru')
        webhook_url = custom_url or f"{site_url}/bot/webhook/"
        
        self.stdout.write(f'🔧 Настройка webhook: {webhook_url}')
        
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query'],
            'drop_pending_updates': True
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook успешно установлен!')
                )
                self.stdout.write(f'   URL: {webhook_url}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка установки webhook: {result.get("description", "Unknown")}')
                )
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка сети: {str(e)}')
            )

    def delete_webhook(self, bot_token):
        """Удаляет webhook"""
        self.stdout.write('🗑️ Удаление webhook...')
        
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        data = {'drop_pending_updates': True}
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook успешно удален!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка удаления webhook: {result.get("description", "Unknown")}')
                )
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка сети: {str(e)}')
            )

    def get_webhook_info(self, bot_token):
        """Получает информацию о webhook"""
        self.stdout.write('🔍 Получение информации о webhook...')
        
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        
        try:
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                webhook_info = result['result']
                
                self.stdout.write(
                    self.style.SUCCESS('📋 Информация о webhook:')
                )
                self.stdout.write(f'   URL: {webhook_info.get("url", "Не установлен")}')
                self.stdout.write(f'   Статус: {"Активен" if webhook_info.get("url") else "Не активен"}')
                self.stdout.write(f'   Ожидающие обновления: {webhook_info.get("pending_update_count", 0)}')
                
                if webhook_info.get('last_error_date'):
                    self.stdout.write(
                        self.style.WARNING(f'   Последняя ошибка: {webhook_info.get("last_error_message", "Unknown")}')
                    )
                
                allowed_updates = webhook_info.get('allowed_updates', [])
                if allowed_updates:
                    self.stdout.write(f'   Разрешенные обновления: {", ".join(allowed_updates)}')
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка получения информации: {result.get("description", "Unknown")}')
                )
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка сети: {str(e)}')
            )
