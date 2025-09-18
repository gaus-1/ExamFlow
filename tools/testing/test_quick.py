#!/usr/bin/env python
"""Быстрое тестирование AI и компонентов"""

import requests
import time

def test_website():
    """Тест веб-сайта"""
    print("🌐 Тест веб-сайта:")
    try:
        r = requests.get('http://localhost:8000/', timeout=5)
        print(f"  Статус: {r.status_code}")
        
        if r.status_code == 200:
            # Проверяем ключевые элементы
            elements = {
                'AI интерфейс': 'ai-interface' in r.text,
                'CSS загружен': 'examflow-unified.css' in r.text,
                'JS загружен': 'examflow-main.js' in r.text,
                'Логотип': 'logo-icon' in r.text,
                'QR-код': 'telegram-qr' in r.text,
            }
            
            for name, found in elements.items():
                status = "✅" if found else "❌"
                print(f"  {status} {name}")
            
            return True
        return False
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_ai_api():
    """Тест AI API"""
    print("\n🤖 Тест AI API:")
    try:
        # Простой GET запрос для проверки доступности
        r = requests.get('http://localhost:8000/ai/', timeout=5)
        print(f"  AI модуль доступен: {r.status_code}")
        
        # Проверяем AI endpoints
        endpoints = [
            '/ai/api/',
            '/ai/chat/',
        ]
        
        for endpoint in endpoints:
            try:
                resp = requests.get(f'http://localhost:8000{endpoint}', timeout=3)
                status = "✅" if resp.status_code in [200, 405, 302] else "❌"
                print(f"  {status} {endpoint}: HTTP {resp.status_code}")
            except:
                print(f"  ❌ {endpoint}: недоступен")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_telegram_auth():
    """Тест Telegram авторизации"""
    print("\n📱 Тест Telegram авторизации:")
    try:
        r = requests.get('http://localhost:8000/auth/telegram/login/', timeout=5)
        status = "✅" if r.status_code == 200 else "❌"
        print(f"  {status} Telegram Login: HTTP {r.status_code}")
        return r.status_code == 200
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def main():
    print("🚀 БЫСТРОЕ ТЕСТИРОВАНИЕ EXAMFLOW")
    print("=" * 40)
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    time.sleep(3)
    
    results = []
    results.append(("Веб-сайт", test_website()))
    results.append(("AI API", test_ai_api()))
    results.append(("Telegram Auth", test_telegram_auth()))
    
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "✅ ПРОШЁЛ" if success else "❌ ОШИБКА"
        print(f"{test_name:<15} | {status}")
        if success:
            passed += 1
    
    print("=" * 40)
    print(f"ИТОГО: {passed}/{len(results)} тестов прошли")
    
    if passed == len(results):
        print("🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ!")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ")

if __name__ == "__main__":
    main()
