#!/usr/bin/env python
"""
Очистка кэша от GigaChat
"""
import os
import sys
import django

def clear_gigachat_cache():
    """Очищаем кэш от GigaChat"""
    print("🧹 Очистка кэша от GigaChat...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        print("✅ Django настроен")
        
        from ai.models import AiResponse, AiRequest
        
        # Удаляем все кэшированные ответы
        deleted_responses = AiResponse.objects.all().delete()
        print(f"🗑️ Удалено кэшированных ответов: {deleted_responses[0]}")
        
        # Удаляем все запросы
        deleted_requests = AiRequest.objects.all().delete()
        print(f"🗑️ Удалено запросов: {deleted_requests[0]}")
        
        print("✅ Кэш очищен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = clear_gigachat_cache()
    if success:
        print("\n🎉 Кэш успешно очищен!")
    else:
        print("\n💥 Очистка не удалась!")

