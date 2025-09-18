#!/usr/bin/env python3
"""
Тестирование AI API на веб-сайте ExamFlow
"""

import requests
import json
import time

def test_ai_website():
    """Тестирует AI API на локальном сервере"""
    
    print("🧪 ТЕСТИРОВАНИЕ AI НА ВЕБ-САЙТЕ")
    print("=" * 50)
    
    # Тестовые вопросы
    test_questions = [
        "Привет, как дела?",
        "Объясни теорему Пифагора",
        "Помоги решить квадратное уравнение x² + 5x + 6 = 0",
        "Что такое производная?",
        "Расскажи про ЕГЭ по математике"
    ]
    
    base_url = "http://localhost:8000"
    ai_endpoint = f"{base_url}/ai/api/"
    
    print(f"🌐 Тестируем: {ai_endpoint}")
    print()
    
    # Проверяем доступность сервера
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Сервер доступен: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return
    
    # Тестируем AI API
    success_count = 0
    total_time = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Тест {i}/5: {question[:30]}...")
        
        try:
            start_time = time.time()
            
            # Отправляем POST запрос
            response = requests.post(
                ai_endpoint,
                json={"prompt": question},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            end_time = time.time()
            request_time = end_time - start_time
            total_time += request_time
            
            print(f"   📊 HTTP статус: {response.status_code}")
            print(f"   ⏱️ Время ответа: {request_time:.2f}с")
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'Нет ответа')
                print(f"   🤖 Ответ AI: {answer[:100]}...")
                
                # Проверяем структуру ответа
                if 'answer' in data:
                    print("   ✅ Структура ответа корректна")
                    success_count += 1
                else:
                    print("   ❌ Некорректная структура ответа")
            else:
                print(f"   ❌ Ошибка: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print("   ⏰ Таймаут запроса (>30с)")
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
    
    # Итоговая статистика
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   ✅ Успешных тестов: {success_count}/{len(test_questions)}")
    print(f"   ⏱️ Среднее время ответа: {total_time/len(test_questions):.2f}с")
    
    if success_count == len(test_questions):
        print("   🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    elif success_count > len(test_questions) // 2:
        print("   ⚠️ Большинство тестов прошли")
    else:
        print("   🚨 МНОГО ОШИБОК - ТРЕБУЕТ ИСПРАВЛЕНИЯ")

if __name__ == "__main__":
    test_ai_website()
