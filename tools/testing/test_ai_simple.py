#!/usr/bin/env python
"""
Простой тест AI системы
"""

import requests
import json
import re
import sys

def main():
    print("🧪 ПРОСТОЙ ТЕСТ AI СИСТЕМЫ")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    try:
        # 1. Проверяем сайт
        print("\n📱 Проверка сайта...")
        response = requests.get(base_url, timeout=10)
        print(f"Статус сайта: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Сайт недоступен")
            return False
        
        # 2. Проверяем AI элементы
        html = response.text
        ai_elements = [
            "ai-interface",
            "ai-input", 
            "ai-send-btn",
            "examflow-main.js"
        ]
        
        print("\n🔍 Проверка AI элементов:")
        for element in ai_elements:
            found = element in html
            status = "✅" if found else "❌"
            print(f"  {status} {element}")
        
        # 3. Получаем CSRF токен
        print("\n🔐 Получение CSRF токена...")
        csrf_match = re.search(r'csrfmiddlewaretoken[^>]*value=["\']([^"\']*)["\']', html)
        
        if not csrf_match:
            print("❌ CSRF токен не найден")
            return False
        
        csrf_token = csrf_match.group(1)
        print("✅ CSRF токен получен")
        
        # 4. Тестируем AI API
        print("\n🤖 Тестирование AI API...")
        session = requests.Session()
        
        # Копируем cookies из первого запроса
        session.cookies.update(response.cookies)
        
        ai_response = session.post(
            f"{base_url}/ai/api/",
            json={"prompt": "Привет! Это тест AI системы."},
            headers={
                "X-CSRFToken": csrf_token,
                "Content-Type": "application/json",
                "Referer": base_url
            },
            timeout=30
        )
        
        print(f"AI API статус: {ai_response.status_code}")
        
        if ai_response.status_code == 200:
            try:
                data = ai_response.json()
                if "answer" in data and data["answer"]:
                    answer_preview = data["answer"][:100] + "..." if len(data["answer"]) > 100 else data["answer"]
                    print(f"✅ AI ответ получен: {answer_preview}")
                    return True
                else:
                    print("❌ AI ответ пустой или некорректный")
                    print(f"Данные: {data}")
                    return False
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                print(f"Ответ: {ai_response.text[:200]}")
                return False
        else:
            print(f"❌ Ошибка AI API: {ai_response.status_code}")
            print(f"Ответ: {ai_response.text[:200]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 AI СИСТЕМА РАБОТАЕТ!")
    else:
        print("\n🔧 ТРЕБУЮТСЯ ИСПРАВЛЕНИЯ")
    
    sys.exit(0 if success else 1)
