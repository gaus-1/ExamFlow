#!/usr/bin/env python3
"""
Скрипт для настройки UptimeRobot мониторинга ExamFlow 2.0
"""

import requests
import time
from typing import Dict, Any, Optional

class UptimeRobotSetup:
    """Настройка мониторинга через UptimeRobot API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.uptimerobot.com/v2"
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
    
    def create_monitor(self, name: str, url: str, monitor_type: int = 1) -> Optional[Dict[str, Any]]:
        """
        Создает монитор в UptimeRobot
        
        Args:
            name: Название монитора
            url: URL для мониторинга
            monitor_type: 1 = HTTP(s), 2 = Keyword, 3 = Ping, 4 = Port
        """
        data = {
            'api_key': self.api_key,
            'format': 'json',
            'type': monitor_type,
            'url': url,
            'friendly_name': name,
            'interval': 300,  # 5 минут
            'timeout': 30,
            'keyword_type': 1 if monitor_type == 2 else None,
            'keyword_value': 'healthy' if monitor_type == 2 else None,
            'http_username': '',
            'http_password': '',
            'port': 80 if monitor_type == 4 else None,
            'ignore_ssl_errors': 0
        }
        
        # Удаляем None значения
        data = {k: v for k, v in data.items() if v is not None}
        
        try:
            response = requests.post(
                f"{self.base_url}/newMonitor",
                data=data,
                headers=self.headers,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('stat') == 'ok':
                print(f"✅ Монитор '{name}' создан успешно")
                return result.get('monitor')
            else:
                print(f"❌ Ошибка создания монитора '{name}': {result.get('error', {}).get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при создании монитора '{name}': {e}")
            return None
    
    def get_monitors(self) -> Optional[Dict[str, Any]]:
        """Получает список всех мониторов"""
        data = {
            'api_key': self.api_key,
            'format': 'json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/getMonitors",
                data=data,
                headers=self.headers,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('stat') == 'ok':
                return result
            else:
                print(f"❌ Ошибка получения мониторов: {result.get('error', {}).get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при получении мониторов: {e}")
            return None
    
    def delete_monitor(self, monitor_id: str) -> bool:
        """Удаляет монитор"""
        data = {
            'api_key': self.api_key,
            'format': 'json',
            'id': monitor_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/deleteMonitor",
                data=data,
                headers=self.headers,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('stat') == 'ok':
                print(f"✅ Монитор {monitor_id} удален")
                return True
            else:
                print(f"❌ Ошибка удаления монитора {monitor_id}: {result.get('error', {}).get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при удалении монитора {monitor_id}: {e}")
            return False


def setup_examflow_monitoring(api_key: str):
    """Настраивает мониторинг для ExamFlow"""
    
    if not api_key:
        print("❌ API ключ UptimeRobot не предоставлен")
        print("Получите API ключ на https://uptimerobot.com/dashboard.php#mySettings")
        return False
    
    setup = UptimeRobotSetup(api_key)
    
    print("🚀 Настройка мониторинга ExamFlow 2.0...")
    
    # Список мониторов для создания
    monitors = [
        {
            'name': 'ExamFlow - Главная страница',
            'url': 'https://examflow.ru/',
            'type': 1  # HTTP
        },
        {
            'name': 'ExamFlow - Health Check',
            'url': 'https://examflow.ru/health/',
            'type': 1  # HTTP
        },
        {
            'name': 'ExamFlow - Simple Health',
            'url': 'https://examflow.ru/health/simple/',
            'type': 1  # HTTP
        },
        {
            'name': 'ExamFlow - Telegram Bot',
            'url': 'https://examflow.ru/bot/webhook/',
            'type': 1  # HTTP
        },
        {
            'name': 'ExamFlow - API Subjects',
            'url': 'https://examflow.ru/api/subjects/',
            'type': 1  # HTTP
        },
        {
            'name': 'ExamFlow - AI Chat',
            'url': 'https://examflow.ru/ai/chat/',
            'type': 1  # HTTP
        }
    ]
    
    created_monitors = []
    
    for monitor_config in monitors:
        print(f"\n📊 Создаем монитор: {monitor_config['name']}")
        monitor = setup.create_monitor(
            name=monitor_config['name'],
            url=monitor_config['url'],
            monitor_type=monitor_config['type']
        )
        
        if monitor:
            created_monitors.append(monitor)
            time.sleep(1)  # Пауза между запросами
    
    print(f"\n✅ Создано {len(created_monitors)} мониторов")
    
    # Показываем созданные мониторы
    print("\n📋 Созданные мониторы:")
    for monitor in created_monitors:
        print(f"   - {monitor.get('friendly_name')} (ID: {monitor.get('id')})")
    
    print("\n🔗 Управление мониторами:")
    print("   Dashboard: https://uptimerobot.com/dashboard")
    print("   Settings: https://uptimerobot.com/dashboard.php#mySettings")
    
    return True


def main():
    """Основная функция"""
    print("🤖 Настройка UptimeRobot для ExamFlow 2.0")
    print("=" * 50)
    
    # Получаем API ключ
    api_key = input("Введите API ключ UptimeRobot (или нажмите Enter для пропуска): ").strip()
    
    if not api_key:
        print("\n📝 Инструкции по получению API ключа:")
        print("1. Зарегистрируйтесь на https://uptimerobot.com")
        print("2. Перейдите в Settings: https://uptimerobot.com/dashboard.php#mySettings")
        print("3. Скопируйте API Key")
        print("4. Запустите скрипт снова с API ключом")
        return
    
    # Настраиваем мониторинг
    success = setup_examflow_monitoring(api_key)
    
    if success:
        print("\n🎉 Мониторинг настроен успешно!")
        print("\n📱 Уведомления:")
        print("   - Настройте уведомления в UptimeRobot Dashboard")
        print("   - Рекомендуется: Email + Telegram + Webhook")
        print("   - Интервал проверки: 5 минут")
        print("   - Timeout: 30 секунд")
    else:
        print("\n❌ Ошибка настройки мониторинга")


if __name__ == "__main__":
    main()
