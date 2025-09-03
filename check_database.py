#!/usr/bin/env python
"""
Скрипт для проверки состояния базы данных и наполнения контентом
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from core.models import FIPIData, FIPISourceMap, DataChunk
from authentication.models import UserProfile, Subscription

def check_database():
    """Проверяет состояние базы данных"""
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    
    # Проверяем модели
    try:
        fipi_count = FIPIData.objects.count()
        source_map_count = FIPISourceMap.objects.count()
        chunks_count = DataChunk.objects.count()
        users_count = UserProfile.objects.count()
        subscriptions_count = Subscription.objects.count()
        
        print(f"📊 FIPIData (документы): {fipi_count}")
        print(f"🗺️  FIPISourceMap (источники): {source_map_count}")
        print(f"📝 DataChunk (чанки): {chunks_count}")
        print(f"👥 UserProfile (пользователи): {users_count}")
        print(f"💳 Subscription (подписки): {subscriptions_count}")
        
        # Показываем последние документы
        if fipi_count > 0:
            print("\n📄 Последние документы:")
            for doc in FIPIData.objects.all()[:5]:
                print(f"  - {doc.title} ({doc.data_type})")
        
        # Показываем источники
        if source_map_count > 0:
            print("\n🔗 Источники данных:")
            for source in FIPISourceMap.objects.all()[:5]:
                print(f"  - {source.url} ({source.priority})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False

def check_ingestion_system():
    """Проверяет систему сбора данных"""
    print("\n=== ПРОВЕРКА СИСТЕМЫ СБОРА ===")
    
    try:
        from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper
        from core.data_ingestion.ingestion_engine import IngestionEngine
        
        scraper = AdvancedFIPIScraper()
        print("✅ AdvancedFIPIScraper инициализирован")
        
        engine = IngestionEngine()
        print("✅ IngestionEngine инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке системы сбора: {e}")
        return False

def check_premium_system():
    """Проверяет систему премиум-доступа"""
    print("\n=== ПРОВЕРКА ПРЕМИУМ-СИСТЕМЫ ===")
    
    try:
        from core.premium.access_control import get_access_control, get_usage_tracker
        
        access_control = get_access_control()
        usage_tracker = get_usage_tracker()
        
        print("✅ AccessControlService инициализирован")
        print("✅ UsageTracker инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке премиум-системы: {e}")
        return False

def main():
    """Основная функция"""
    print("🔍 ПРОВЕРКА СИСТЕМЫ EXAMFLOW 2.0")
    print("=" * 50)
    
    # Проверяем все компоненты
    db_ok = check_database()
    ingestion_ok = check_ingestion_system()
    premium_ok = check_premium_system()
    
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ СТАТУС:")
    print(f"  База данных: {'✅' if db_ok else '❌'}")
    print(f"  Система сбора: {'✅' if ingestion_ok else '❌'}")
    print(f"  Премиум-система: {'✅' if premium_ok else '❌'}")
    
    if db_ok and ingestion_ok and premium_ok:
        print("\n🎉 Все системы работают корректно!")
        print("\n📝 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Запустите: python manage.py init_fipi_source_map")
        print("2. Запустите: python manage.py manage_ingestion_engine start")
        print("3. Добавьте задачи: python manage.py manage_ingestion_engine add-tasks --priority high")
        print("4. Проверьте статус: python manage.py manage_ingestion_engine status")
    else:
        print("\n⚠️  Есть проблемы, требующие внимания")

if __name__ == "__main__":
    main()
