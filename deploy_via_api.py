#!/usr/bin/env python3
"""
Скрипт для деплоя через Render API
Требует настройки RENDER_API_KEY в переменных окружения
"""

import os

import requests


def trigger_render_deploy():
    """Запускает деплой через Render API"""

    api_key = os.getenv("RENDER_API_KEY")
    service_id = os.getenv("RENDER_SERVICE_ID")  # ID вашего сервиса

    if not api_key or not service_id:
        print("❌ Ошибка: нужны переменные RENDER_API_KEY и RENDER_SERVICE_ID")
        return False

    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 201:
            print("✅ Деплой запущен через API!")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    trigger_render_deploy()
