"""
Команда для поддержания сайта активным
Предотвращает "засыпание" сайта на Render
"""

import requests
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Поддерживает сайт активным, предотвращая "засыпание" на Render'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=600,  # 10 минут по умолчанию
            help='Интервал проверки в секундах (по умолчанию 600 = 10 минут)'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Запустить в непрерывном режиме'
        )
        parser.add_argument(
            '--url',
            type=str,
            default='https://examflow.ru',
            help='URL сайта для keep-alive'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        continuous = options['continuous']
        site_url = options['url']
        
        self.stdout.write(
            f'🔄 Запуск keep-alive для сайта {site_url} (интервал: {interval}с)'
        )
        
        while True:
            try:
                # Делаем запрос к сайту, чтобы "разбудить" его
                response = requests.get(
                    site_url, 
                    timeout=30,
                    headers={
                        'User-Agent': 'ExamFlow-KeepAlive/1.0'
                    }
                )
                
                timestamp = time.strftime('%H:%M:%S')
                if response.status_code == 200:
                    self.stdout.write(f"✅ {timestamp} - Сайт активен (HTTP {response.status_code})")
                    logger.info(f"Сайт активен: {timestamp} - HTTP {response.status_code}")
                else:
                    self.stdout.write(f"⚠️ {timestamp} - Сайт отвечает, но статус {response.status_code}")
                    logger.warning(f"Сайт отвечает со статусом {response.status_code}: {timestamp}")
                
            except requests.exceptions.Timeout:
                timestamp = time.strftime('%H:%M:%S')
                self.stdout.write(f"⏰ {timestamp} - Таймаут запроса к сайту")
                logger.warning(f"Таймаут запроса к сайту: {timestamp}")
                
            except requests.exceptions.ConnectionError as e:
                timestamp = time.strftime('%H:%M:%S')
                self.stdout.write(f"🔌 {timestamp} - Ошибка соединения: {e}")
                logger.error(f"Ошибка соединения с сайтом: {e}")
                
            except Exception as e:
                timestamp = time.strftime('%H:%M:%S')
                self.stdout.write(f"❌ {timestamp} - Неожиданная ошибка: {e}")
                logger.error(f"Неожиданная ошибка keep-alive сайта: {e}")
            
            if not continuous:
                break
                
            time.sleep(interval)
        
        self.stdout.write('🏁 Keep-alive сайта завершен')
