#!/usr/bin/env python
"""
Полная очистка всех ИИ данных
"""
import os
import sys
import django

def full_cleanup():
    """Полная очистка всех ИИ данных"""
    print("🧹 Полная очистка ИИ данных...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        print("✅ Django настроен")
        
        from ai.models import AiRequest, AiResponse, AiLimit, AiProvider
        
        # Удаляем все запросы
        deleted_requests = AiRequest.objects.all().delete()
        print(f"🗑️ Удалено запросов: {deleted_requests[0]}")
        
        # Удаляем все кэшированные ответы
        deleted_responses = AiResponse.objects.all().delete()
        print(f"🗑️ Удалено кэшированных ответов: {deleted_responses[0]}")
        
        # Удаляем все лимиты
        deleted_limits = AiLimit.objects.all().delete()
        print(f"🗑️ Удалено лимитов: {deleted_limits[0]}")
        
        # Удаляем все провайдеры
        deleted_providers = AiProvider.objects.all().delete()
        print(f"🗑️ Удалено провайдеров: {deleted_providers[0]}")
        
        print("✅ Полная очистка завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = full_cleanup()
    if success:
        print("\n🎉 Все данные ИИ успешно очищены!")
    else:
        print("\n💥 Очистка не удалась!")

