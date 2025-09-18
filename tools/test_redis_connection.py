#!/usr/bin/env python
"""
Простой тест подключения к Redis
"""

import os
import redis
from urllib.parse import urlparse

def test_redis():
    print("🔧 ТЕСТИРОВАНИЕ REDIS ПОДКЛЮЧЕНИЯ")
    print("=" * 40)
    
    redis_url = "rediss://red-d2qldkje5dus73c73tr0:zccbozd9aZ5sbiSSZ8xZaJpW9qM3BnOz@oregon-keyvalue.render.com:6379"
    
    try:
        # Парсим URL
        url = urlparse(redis_url)
        print(f"Host: {url.hostname}")
        print(f"Port: {url.port}")
        print(f"SSL: {'Да' if url.scheme == 'rediss' else 'Нет'}")
        
        # Подключаемся
        print("\n🔄 Подключение к Redis...")
        
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Тестируем подключение
        r.ping()  # type: ignore
        print("✅ Ping успешен")
        
        # Тестируем запись/чтение
        r.set("test_key", "test_value", ex=60)  # type: ignore
        value = r.get("test_key")  # type: ignore
        
        if value == "test_value":
            print("✅ Запись/чтение работает")
        else:
            print("❌ Проблемы с записью/чтением")
        
        # Очищаем тестовый ключ
        r.delete("test_key")  # type: ignore
        
        print("🎉 REDIS ПОЛНОСТЬЮ РАБОТАЕТ!")
        return True
        
    except redis.exceptions.ConnectionError as e:  # type: ignore
        if "allowlist" in str(e):
            print(f"❌ IP не в whitelist: {e}")
            print(f"💡 Добавьте IP 84.17.55.155 в allowlist на Render.com")
        else:
            print(f"❌ Ошибка подключения: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка Redis: {e}")
        return False

if __name__ == "__main__":
    test_redis()
