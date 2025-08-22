#!/usr/bin/env python
"""
Сброс лимитов ИИ запросов
"""
import os
import sys
import django

def reset_ai_limits():
    """Сбрасываем лимиты ИИ запросов"""
    print("🔄 Сброс лимитов ИИ запросов...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
        django.setup()
        print("✅ Django настроен")
        
        from ai.models import AiLimit
        from django.utils import timezone
        from datetime import timedelta
        
        # Сбрасываем все лимиты
        limits = AiLimit.objects.all()
        for limit in limits:
            limit.current_usage = 0
            limit.reset_date = timezone.now() + timedelta(days=1)
            limit.save()
            print(f"🔄 Сброшен лимит для {limit.user or 'гостя'}: {limit.current_usage}/{limit.max_limit}")
        
        print(f"✅ Сброшено лимитов: {limits.count()}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = reset_ai_limits()
    if success:
        print("\n🎉 Лимиты успешно сброшены!")
    else:
        print("\n💥 Сброс лимитов не удался!")

