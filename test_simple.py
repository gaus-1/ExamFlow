import requests

print("🧪 Простой тест AI API")

try:
    # Проверяем сервер
    response = requests.get("http://localhost:8000", timeout=5)
    print(f"✅ Сервер доступен: {response.status_code}")

    # Тестируем AI API
    ai_response = requests.post(
        "http://localhost:8000/ai/api/",
        json={"prompt": "Привет, как дела?"},
        timeout=10
    )
    print(f"🤖 AI API статус: {ai_response.status_code}")

    if ai_response.status_code == 200:
        data = ai_response.json()
        print(f"📝 Ответ AI: {data.get('answer', 'Нет ответа')[:100]}...")
    else:
        print(f"❌ Ошибка AI: {ai_response.text}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
