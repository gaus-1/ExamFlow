#!/usr/bin/env python
"""
Очистка старых провайдеров и инициализация Ollama
"""
import os
import sys
import django

def cleanup_and_init_ollama():
    """Очищаем старые провайдеры и инициализируем Ollama"""
    print("🧹 Очистка старых провайдеров и инициализация Ollama...")

    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        print("✅ Django настроен")

        from ai.models import AiRequest, AiResponse, AiLimit, AiProvider

        # Удаляем все старые данные
        deleted_requests = AiRequest.objects.all().delete()  # type: ignore
        print(f"🗑️ Удалено запросов: {deleted_requests[0]}")

        deleted_responses = AiResponse.objects.all().delete()  # type: ignore
        print(f"🗑️ Удалено кэшированных ответов: {deleted_responses[0]}")

        deleted_limits = AiLimit.objects.all().delete()  # type: ignore
        print(f"🗑️ Удалено лимитов: {deleted_limits[0]}")

        deleted_providers = AiProvider.objects.all().delete()  # type: ignore
        print(f"🗑️ Удалено провайдеров: {deleted_providers[0]}")

        # Создаем Ollama провайдер
        ollama_provider = AiProvider.objects.create(  # type: ignore
            name="Ollama",
            provider_type="ollama",
            is_active=True,
            priority=1,
            daily_limit=1000  # Высокий лимит для Ollama
        )
        print(f"✅ Создан Ollama провайдер: {ollama_provider.name}")

        # Создаем лимиты для гостей и пользователей
        from django.utils import timezone
        from datetime import timedelta

        # Лимит для гостей
        guest_limit = AiLimit.objects.create(  # type: ignore
            limit_type="daily",
            max_limit=50,  # 50 запросов в день для гостей
            current_usage=0,
            reset_date=timezone.now() + timedelta(days=1)
        )
        print(f"✅ Создан лимит для гостей: {guest_limit.max_limit}/день")

        # Лимит для зарегистрированных пользователей
        user_limit = AiLimit.objects.create(  # type: ignore
            limit_type="daily",
            max_limit=200,  # 200 запросов в день для пользователей
            current_usage=0,
            reset_date=timezone.now() + timedelta(days=1)
        )
        print(f"✅ Создан лимит для пользователей: {user_limit.max_limit}/день")

        print("🎉 Очистка и инициализация завершены!")
        print("\n📋 Текущие настройки:")
        print(f"• Провайдер: {ollama_provider.name} ({ollama_provider.provider_type})")
        print(f"• Лимит гостей: {guest_limit.max_limit}/день")
        print(f"• Лимит пользователей: {user_limit.max_limit}/день")
        print(f"• Статус: {'✅ Активен' if ollama_provider.is_active else '❌ Неактивен'}")

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = cleanup_and_init_ollama()
    if success:
        print("\n🎉 Ollama успешно настроен!")
        print("\n🚀 Следующие шаги:")
        print("1. Установите Ollama с https://ollama.ai/download")
        print("2. Запустите: ollama run llama3.1:8b")
        print("3. Перезапустите Django сервер")
        print("4. Тестируйте ИИ на сайте!")
    else:
        print("\n💥 Настройка не удалась!")
