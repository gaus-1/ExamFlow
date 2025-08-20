"""
Система поддержания активности сайта для предотвращения засыпания на Render
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
import threading
import schedule

logger = logging.getLogger(__name__)


class KeepAliveService:
    """Сервис для поддержания активности сайта"""
    
    def __init__(self, site_url=None):
        self.site_url = site_url or getattr(settings, 'SITE_URL', 'https://examflow.ru')
        self.ping_interval = 10  # минут
        self.is_running = False
        self.thread = None
        
    def ping_site(self):
        """Пингует сайт для поддержания активности"""
        try:
            response = requests.get(
                f"{self.site_url}/api/statistics/",
                timeout=30,
                headers={
                    'User-Agent': 'ExamFlow-KeepAlive/1.0'
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Пинг успешен: {self.site_url} - {datetime.now()}")
                return True
            else:
                logger.warning(f"⚠️ Пинг вернул код {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка пинга: {str(e)}")
            return False
    
    def start_keepalive(self):
        """Запускает службу поддержания активности"""
        if self.is_running:
            logger.info("🔄 Служба keep-alive уже запущена")
            return
        
        self.is_running = True
        logger.info(f"🚀 Запуск keep-alive службы для {self.site_url}")
        logger.info(f"⏰ Интервал пинга: {self.ping_interval} минут")
        
        # Планируем регулярные пинги
        schedule.every(self.ping_interval).minutes.do(self.ping_site)
        # Раз в неделю — рассылка напоминаний неактивным (в воскресенье 10:00)
        try:
            from core.weekly_reminders import send_weekly_inactive_reminders
            schedule.every().sunday.at("10:00").do(send_weekly_inactive_reminders)
        except Exception as _:
            logger.warning("Не удалось подключить weekly_reminders, пропускаю планирование")
        
        # Запускаем в отдельном потоке
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        # Делаем первый пинг сразу
        self.ping_site()
    
    def stop_keepalive(self):
        """Останавливает службу"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 Keep-alive служба остановлена")
    
    def _run_scheduler(self):
        """Запускает планировщик в отдельном потоке"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту


class TelegramKeepAlive:
    """Поддержание активности через Telegram бота"""
    
    def __init__(self, bot_token=None, site_url=None):
        self.bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.site_url = site_url or getattr(settings, 'SITE_URL', 'https://examflow.ru')
        self.chat_id = getattr(settings, 'ADMIN_CHAT_ID', None)  # ID чата админа
        
    def send_ping_via_bot(self):
        """Отправляет пинг через Telegram бота"""
        if not self.bot_token:
            logger.warning("⚠️ Telegram bot token не настроен")
            return False
            
        try:
            # Отправляем запрос к боту, который в свою очередь пингует сайт
            bot_url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(bot_url, timeout=10)
            
            if response.status_code == 200:
                # Бот активен, теперь пингуем сайт
                site_response = requests.get(f"{self.site_url}/api/statistics/", timeout=30)
                
                if site_response.status_code == 200:
                    logger.info("✅ Пинг через Telegram бота успешен")
                    
                    # Отправляем уведомление админу (если настроен)
                    if self.chat_id:
                        self.send_admin_notification("🟢 Сайт активен")
                    
                    return True
                else:
                    logger.warning(f"⚠️ Сайт недоступен: код {site_response.status_code}")
                    if self.chat_id:
                        self.send_admin_notification(f"🔴 Сайт недоступен: {site_response.status_code}")
                    return False
            else:
                logger.error(f"❌ Telegram бот недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка пинга через бота: {str(e)}")
            return False
    
    def send_admin_notification(self, message):
        """Отправляет уведомление админу"""
        if not self.chat_id:
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': f"🤖 ExamFlow Status\n{message}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            }
            
            requests.post(url, data=data, timeout=10)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {str(e)}")


# Глобальный экземпляр сервиса
keepalive_service = KeepAliveService()
telegram_keepalive = TelegramKeepAlive()


def start_keepalive():
    """Запускает все системы поддержания активности"""
    logger.info("🚀 Инициализация систем keep-alive...")
    
    # Запускаем основной сервис
    keepalive_service.start_keepalive()
    
    # Настраиваем Telegram пинги (каждые 5 минут)
    schedule.every(5).minutes.do(telegram_keepalive.send_ping_via_bot)
    
    logger.info("✅ Системы keep-alive запущены")


def stop_keepalive():
    """Останавливает все системы"""
    keepalive_service.stop_keepalive()
    schedule.clear()
    logger.info("🛑 Все системы keep-alive остановлены")
