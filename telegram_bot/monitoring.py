#!/usr/bin/env python3
"""
Система мониторинга для ExamFlow Telegram Bot
Проверяет состояние бота и отправляет уведомления
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
import json

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram import Bot
from core.container import Container

logger = logging.getLogger(__name__)


class BotMonitor:
    """Мониторинг состояния Telegram бота"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.admin_chat_id = getattr(settings, 'ADMIN_TELEGRAM_ID', None)
        self.check_interval = 300  # 5 минут
        self.last_check = None
        self.failures_count = 0
        self.max_failures = 3
        
    async def check_bot_health(self) -> Dict[str, Any]:
        """Проверка здоровья бота"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'bot_online': False,
            'api_responsive': False,
            'database_connected': False,
            'ai_working': False,
            'errors': []
        }
        
        try:
            # 1. Проверка Telegram Bot API
            bot = Bot(token=self.bot_token)
            me = await bot.get_me()
            health_status['bot_online'] = True
            health_status['bot_info'] = {
                'username': me.username,
                'id': me.id,
                'first_name': me.first_name
            }
            logger.info(f"✅ Bot API: @{me.username}")
            
        except Exception as e:
            health_status['errors'].append(f"Bot API error: {str(e)}")
            logger.error(f"❌ Bot API: {e}")
        
        try:
            # 2. Проверка базы данных
            from learning.models import Subject
            subjects_count = Subject.objects.count()  # type: ignore
            health_status['database_connected'] = True
            health_status['database_info'] = {
                'subjects_count': subjects_count
            }
            logger.info(f"✅ Database: {subjects_count} subjects")
            
        except Exception as e:
            health_status['errors'].append(f"Database error: {str(e)}")
            logger.error(f"❌ Database: {e}")
        
        try:
            # 3. Проверка AI системы
            ai_orchestrator = Container.ai_orchestrator()
            test_response = ai_orchestrator.ask("Тест")
            if isinstance(test_response, dict) and 'answer' in test_response:
                health_status['ai_working'] = True
                health_status['ai_info'] = {
                    'response_length': len(test_response['answer'])
                }
                logger.info("✅ AI System: Working")
            else:
                health_status['errors'].append("AI returned unexpected format")
                
        except Exception as e:
            health_status['errors'].append(f"AI error: {str(e)}")
            logger.error(f"❌ AI System: {e}")
        
        # 4. Общий статус
        health_status['overall_healthy'] = (
            health_status['bot_online'] and
            health_status['database_connected'] and
            health_status['ai_working']
        )
        
        return health_status
    
    async def send_alert(self, message: str, priority: str = "warning"):
        """Отправка уведомления администратору"""
        if not self.admin_chat_id:
            logger.warning("ADMIN_TELEGRAM_ID не настроен, уведомление не отправлено")
            return
        
        try:
            bot = Bot(token=self.bot_token)
            
            # Эмодзи в зависимости от приоритета
            emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '🚨',
                'success': '✅'
            }.get(priority, 'ℹ️')
            
            formatted_message = f"{emoji} **ExamFlow Bot Alert**\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await bot.send_message(
                chat_id=self.admin_chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление: {e}")
    
    async def run_monitoring(self):
        """Основной цикл мониторинга"""
        logger.info("🔍 Запуск мониторинга ExamFlow Bot")
        
        while True:
            try:
                # Проверяем здоровье
                health_status = await self.check_bot_health()
                self.last_check = datetime.now()
                
                if health_status['overall_healthy']:
                    if self.failures_count > 0:
                        # Восстановление после сбоев
                        await self.send_alert(
                            f"🎉 Бот восстановлен после {self.failures_count} сбоев",
                            "success"
                        )
                        self.failures_count = 0
                    
                    logger.info("✅ Все системы работают нормально")
                    
                else:
                    self.failures_count += 1
                    error_summary = "; ".join(health_status['errors'])
                    
                    if self.failures_count >= self.max_failures:
                        await self.send_alert(
                            f"🚨 Критические проблемы с ботом!\n\nОшибки: {error_summary}\n\nПроверок с ошибками: {self.failures_count}",
                            "error"
                        )
                    else:
                        logger.warning(f"⚠️ Проблемы с ботом: {error_summary}")
                
                # Сохраняем статус в файл для внешнего мониторинга
                status_file = 'logs/bot_health_status.json'
                os.makedirs(os.path.dirname(status_file), exist_ok=True)
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(health_status, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга: {e}")
                await self.send_alert(f"Ошибка системы мониторинга: {str(e)}", "error")
            
            # Ждем до следующей проверки
            await asyncio.sleep(self.check_interval)


class UptimeRobotIntegration:
    """Интеграция с UptimeRobot для внешнего мониторинга"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'UPTIMEROBOT_API_KEY', '')
        self.monitor_url = getattr(settings, 'SITE_URL', 'https://examflow.ru') + '/healthz'
    
    async def create_monitor(self):
        """Создание монитора в UptimeRobot"""
        if not self.api_key:
            logger.warning("UPTIMEROBOT_API_KEY не настроен")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'api_key': self.api_key,
                    'format': 'json',
                    'type': 1,  # HTTP(s)
                    'url': self.monitor_url,
                    'friendly_name': 'ExamFlow Website',
                    'interval': 300,  # 5 минут
                    'timeout': 30
                }
                
                async with session.post('https://api.uptimerobot.com/v2/newMonitor', data=data) as resp:
                    result = await resp.json()
                    if result.get('stat') == 'ok':
                        logger.info("✅ UptimeRobot монитор создан")
                    else:
                        logger.error(f"❌ Ошибка создания монитора: {result}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка UptimeRobot API: {e}")


async def main():
    """Главная функция мониторинга"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot_monitoring.log'),
            logging.StreamHandler()
        ]
    )
    
    # Создаем директорию логов
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем мониторинг
    monitor = BotMonitor()
    
    # Интеграция с UptimeRobot
    uptime_robot = UptimeRobotIntegration()
    await uptime_robot.create_monitor()
    
    # Основной цикл мониторинга
    await monitor.run_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка мониторинга: {e}")
        sys.exit(1)
