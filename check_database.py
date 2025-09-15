#!/usr/bin/env python
"""
Скрипт для проверки состояния базы данных и наполнения контентом
"""

import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from core.models import FIPIData, FIPISourceMap, DataChunk  # noqa: E402
from authentication.models import UserProfile, Subscription  # noqa: E402

def check_database():
    """Проверяет состояние базы данных"""
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")

    # Проверяем модели
    try:
        fipi_count = FIPIData.objects.count()  # type: ignore
        source_map_count = FIPISourceMap.objects.count()  # type: ignore
        chunks_count = DataChunk.objects.count()  # type: ignore
        users_count = UserProfile.objects.count()  # type: ignore
        subscriptions_count = Subscription.objects.count()  # type: ignore

        print("📊 FIPIData (документы): {fipi_count}")
        print("🗺️  FIPISourceMap (источники): {source_map_count}")
        print("📝 DataChunk (чанки): {chunks_count}")
        print("👥 UserProfile (пользователи): {users_count}")
        print("💳 Subscription (подписки): {subscriptions_count}")

        # Показываем последние документы
        if fipi_count > 0:
            print("\n📄 Последние документы:")
            for doc in FIPIData.objects.all()[:5]:  # type: ignore
                print("  - {doc.title} ({doc.data_type})")

        # Показываем источники
        if source_map_count > 0:
            print("\n🔗 Источники данных:")
            for source in FIPISourceMap.objects.all()[:5]:  # type: ignore
                print("  - {source.url} ({source.priority})")

        return True

    except Exception as e:
        print("❌ Ошибка при проверке базы данных: {e}")
        return False

def check_ingestion_system():
    """Проверяет систему сбора данных"""
    print("\n=== ПРОВЕРКА СИСТЕМЫ СБОРА ===")

    try:
        from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper
        from core.data_ingestion.ingestion_engine import IngestionEngine

        _scraper = AdvancedFIPIScraper()
        print("✅ AdvancedFIPIScraper инициализирован")

        _engine = IngestionEngine()
        print("✅ IngestionEngine инициализирован")

        return True

    except Exception as e:
        print("❌ Ошибка при проверке системы сбора: {e}")
        return False

def check_premium_system():
    """Проверяет систему премиум-доступа"""
    print("\n=== ПРОВЕРКА ПРЕМИУМ-СИСТЕМЫ ===")

    try:
        from core.premium.access_control import get_access_control, get_usage_tracker

        _access_control = get_access_control()  # type: ignore
        _usage_tracker = get_usage_tracker()  # type: ignore

        print("✅ AccessControlService инициализирован")
        print("✅ UsageTracker инициализирован")

        return True

    except Exception as e:
        print("❌ Ошибка при проверке премиум-системы: {e}")
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
    print("  База данных: {'✅' if db_ok else '❌'}")
    print("  Система сбора: {'✅' if ingestion_ok else '❌'}")
    print("  Премиум-система: {'✅' if premium_ok else '❌'}")

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
