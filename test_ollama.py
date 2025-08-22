#!/usr/bin/env python3
"""
Тест подключения к Ollama
"""

import requests
import json

def test_ollama_connection():
    """Тестируем подключение к Ollama"""
    print("🔍 Тестируем подключение к Ollama...")
    
    # 1. Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"✅ Сервер доступен: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Доступные модели: {data}")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения: Ollama сервер не запущен")
        print("💡 Запустите: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # 2. Тестируем генерацию
    print("\n🧠 Тестируем генерацию ответа...")
    
    try:
        payload = {
            "model": "llama3.1:8b",
            "prompt": "Привет! Как дела?",
            "stream": False,
            "options": {
                "num_predict": 50,
                "temperature": 0.7
            }
        }
        
        response = requests.post("http://localhost:11434/api/generate", 
                               json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ответ получен: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Ошибка генерации: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тест Ollama для ExamFlow")
    print("=" * 40)
    
    success = test_ollama_connection()
    
    if success:
        print("\n🎉 Ollama работает корректно!")
        print("💡 Теперь можно тестировать ИИ на сайте")
    else:
        print("\n💥 Ollama не работает!")
        print("🔧 Проверьте настройки и перезапустите сервер")
