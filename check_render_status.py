#!/usr/bin/env python3
"""
Скрипт для проверки статуса Render сервиса
"""

import requests
from datetime import datetime

def check_render_service():
    """Проверяет доступность сервиса на Render"""
    
    # URL вашего сервиса (замените на реальный)
    service_urls = [
        "https://examflow.onrender.com",
        "https://examflow-web.onrender.com", 
        "https://examflow-app.onrender.com"
    ]
    
    print("🔍 Проверка статуса Render сервисов...")
    print(f"⏰ Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    for url in service_urls:
        try:
            print(f"🌐 Проверяю: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ Статус: 200 OK - Сервис работает!")
                print(f"📄 Размер ответа: {len(response.text)} символов")
            elif response.status_code == 404:
                print("⚠️  Статус: 404 - Сервис не найден")
            else:
                print(f"⚠️  Статус: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ Таймаут - сервис не отвечает")
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка подключения - сервис недоступен")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 30)

def check_github_repo():
    """Проверяет последние коммиты в GitHub"""
    
    print("\n🔍 Проверка GitHub репозитория...")
    try:
        # Проверяем последний коммит через GitHub API
        api_url = "https://api.github.com/repos/gaus-1/ExamFlow/commits"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            commits = response.json()
            if commits:
                latest_commit = commits[0]
                print(f"✅ Последний коммит: {latest_commit['commit']['message']}")
                print(f"📅 Дата: {latest_commit['commit']['author']['date']}")
                print(f"🔗 SHA: {latest_commit['sha'][:8]}")
            else:
                print("⚠️  Коммиты не найдены")
        else:
            print(f"❌ Ошибка GitHub API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки GitHub: {e}")

if __name__ == "__main__":
    check_render_service()
    check_github_repo()
    
    print("\n💡 Рекомендации:")
    print("1. Проверьте Render Dashboard: https://dashboard.render.com")
    print("2. Убедитесь что сервис не приостановлен")
    print("3. Проверьте настройки репозитория")
    print("4. При необходимости создайте новый сервис")
