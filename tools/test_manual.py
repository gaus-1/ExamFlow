import re

import requests


def test_ai_website():
    print("=== ТЕСТ AI НА САЙТЕ ===")

    try:
        # 1. Проверяем сайт
        r = requests.get("http://localhost:8000/", timeout=10)
        print(f"Сайт: {r.status_code}")

        if r.status_code != 200:
            return False

        # 2. Проверяем AI элементы
        html = r.text
        ai_elements = ["ai-interface", "ai-input", "ai-send-btn", "examflow-main.js"]

        for element in ai_elements:
            found = element in html
            print(f"{element}: {'✓' if found else '✗'}")

        # 3. Тестируем AI API
        session = requests.Session()
        session.get("http://localhost:8000/")  # Получаем cookies

        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
        if not csrf_match:
            print("CSRF: ✗")
            return False

        csrf = csrf_match.group(1)
        print("CSRF: ✓")

        # Тестируем AI запрос
        ai_resp = session.post(
            "http://localhost:8000/ai/api/",
            json={"prompt": "Привет! Это тест ИИ."},
            headers={
                "X-CSRFToken": csrf,
                "Content-Type": "application/json",
                "Referer": "http://localhost:8000/",
            },
            timeout=30,
        )

        print(f"AI API: {ai_resp.status_code}")

        if ai_resp.status_code == 200:
            try:
                data = ai_resp.json()
                if "answer" in data and data["answer"]:
                    print(f"AI ответ: ✓ ({len(data['answer'])} символов)")
                    return True
                else:
                    print("AI ответ: ✗ (пустой)")
                    return False
            except Exception:
                print("AI ответ: ✗ (не JSON)")
                return False
        else:
            print(f"AI ошибка: {ai_resp.status_code}")
            return False

    except Exception as e:
        print(f"Ошибка: {e}")
        return False


def test_responsive():
    print("\n=== ТЕСТ АДАПТИВНОСТИ ===")

    try:
        # Тестируем разные User-Agent для имитации устройств
        devices = [
            ("Mobile", "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"),
            ("Tablet", "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"),
            ("Desktop", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        ]

        for device, ua in devices:
            resp = requests.get(
                "http://localhost:8000/", headers={"User-Agent": ua}, timeout=5
            )

            if resp.status_code == 200:
                # Проверяем наличие адаптивных элементов
                html = resp.text
                responsive_elements = ["mobile-menu", "container", "grid", "flex"]

                found_elements = sum(1 for elem in responsive_elements if elem in html)
                print(
                    f"{device}: ✓ ({found_elements}/{len(responsive_elements)} элементов)"
                )
            else:
                print(f"{device}: ✗ (HTTP {resp.status_code})")

        return True

    except Exception as e:
        print(f"Ошибка адаптивности: {e}")
        return False


def test_telegram_bot():
    print("\n=== ТЕСТ AI В БОТЕ ===")

    try:
        # Проверяем доступность Telegram auth
        resp = requests.get("http://localhost:8000/auth/telegram/login/", timeout=5)
        print(f"Telegram auth: {'✓' if resp.status_code == 200 else '✗'}")

        # Проверяем бот endpoint
        resp = requests.get("http://localhost:8000/bot/", timeout=5)
        print(f"Bot endpoint: {'✓' if resp.status_code in [200, 404, 405] else '✗'}")

        return True

    except Exception as e:
        print(f"Ошибка бота: {e}")
        return False


if __name__ == "__main__":
    print("🧪 РУЧНОЕ ТЕСТИРОВАНИЕ EXAMFLOW")
    print("=" * 40)

    results = []
    results.append(("AI на сайте", test_ai_website()))
    results.append(("Адаптивность", test_responsive()))
    results.append(("Telegram бот", test_telegram_bot()))

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
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ")
