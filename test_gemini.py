#!/usr/bin/env python3
"""
Тест Gemini API для ExamFlow
"""

import os
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем API ключ
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY не найден в .env файле!")
    exit(1)

print(f"✅ Gemini API ключ найден: {api_key[:20]}...")

try:
    # Тестируем Gemini API
    print("\n🤖 Тестируем Gemini API...")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Напиши короткое стихотворение про математику на русском языке"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100,
            "topP": 0.8,
            "topK": 40
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    text = parts[0]['text']
                    print("✅ Gemini API работает!")
                    print(f"🤖 Ответ: {text}")
                else:
                    print("❌ Пустой ответ от Gemini API")
            else:
                print("❌ Неожиданный формат ответа от Gemini API")
        else:
            print("❌ Нет кандидатов в ответе Gemini API")
    else:
        print(f"❌ Ошибка Gemini API: {response.status_code}")
        print(f"Ответ: {response.text}")
        
except Exception as e:
    print(f"❌ Ошибка при тестировании Gemini API: {e}")

print("\n" + "="*50)
print("🎯 РЕЗУЛЬТАТ ТЕСТА GEMINI:")
print("="*50)
