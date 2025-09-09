#!/usr/bin/env python
"""
Скрипт для автоматического наполнения сайта заданиями и документами
"""

import os
import django
import time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from core.models import FIPIData, FIPISourceMap  # noqa: E402
from core.data_ingestion.ingestion_engine import IngestionEngine, TaskPriority  # noqa: E402
from django.utils import timezone  # noqa: E402

def init_source_map():
    """Инициализирует карту источников"""
    print("🗺️ Инициализация карты источников...")
    
    from core.data_ingestion.fipi_structure_map import get_fipi_structure_map
    structure_map = get_fipi_structure_map()
    sources = structure_map.get_all_sources()
    
    created_count = 0
    for source in sources:
        source_obj, created = FIPISourceMap.objects.get_or_create(  # type: ignore
            source_id=source.id,
            defaults={
                'name': source.name,
                'url': source.url,
                'data_type': source.data_type.value,
                'exam_type': source.exam_type.value,
                'subject': source.subject,
                'priority': source.priority.value,
                'update_frequency': source.update_frequency.value,
                'file_format': source.file_format,
                'description': source.description,
            }
        )
        if created:
            created_count += 1
    
    print(f"✅ Создано {created_count} источников")
    return created_count

def start_ingestion_engine():
    """Запускает движок сбора данных"""
    print("🚀 Запуск движка сбора данных...")
    
    engine = IngestionEngine()
    engine.start()
    
    # Добавляем задачи высокого приоритета
    high_priority_sources = FIPISourceMap.objects.filter(priority=1)  # type: ignore
    for source in high_priority_sources:
        from core.data_ingestion.ingestion_engine import IngestionTask
        task = IngestionTask(
            id=f"task_{source.source_id}_{int(time.time())}",
            source_id=source.source_id,
            url=source.url,
            priority=TaskPriority.HIGH,
            data_type=source.data_type,
            created_at=timezone.now()
        )
        engine.task_queue.add_task(task)
    
    print(f"✅ Добавлено {high_priority_sources.count()} задач высокого приоритета")
    return engine

def monitor_progress(engine, max_wait_time=300):
    """Мониторит прогресс сбора данных"""
    print("📊 Мониторинг прогресса...")
    
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < max_wait_time:
        current_count = FIPIData.objects.count()  # type: ignore
        
        if current_count > last_count:
            print(f"📈 Собрано документов: {current_count} (+{current_count - last_count})")
            last_count = current_count
        
        if current_count >= 10:  # Минимальное количество для работы
            print("✅ Достаточно данных для работы сайта!")
            break
            
        time.sleep(10)  # Проверяем каждые 10 секунд
    
    return FIPIData.objects.count()  # type: ignore

def process_pdf_documents():
    """Обрабатывает PDF документы"""
    print("📄 Обработка PDF документов...")
    
    from core.data_ingestion.pdf_processor import PDFProcessor, process_document
    _processor = PDFProcessor()
    
    # Получаем необработанные PDF
    pdf_docs = FIPIData.objects.filter(  # type: ignore
        data_type__in=['demo_variant', 'specification', 'codefier', 'document'],
        is_processed=False,
        url__iendswith='.pdf'
    )[:5]
    
    processed_count = 0
    for doc in pdf_docs:
        try:
            result = process_document(doc.url, doc.id)  # type: ignore
            if isinstance(result, dict) and result.get('status') == 'completed':
                processed_count += 1
                print(f"✅ Обработан: {doc.title}")
        except Exception as e:
            print(f"❌ Ошибка обработки {doc.title}: {e}")
    
    print(f"✅ Обработано {processed_count} PDF документов")
    return processed_count

def create_sample_data():
    """Создает примеры данных для демонстрации"""
    print("📝 Создание примеров данных...")
    
    sample_docs = [
        {
            'title': 'Демонстрационный вариант ЕГЭ по математике 2024',
            'content': 'Примеры заданий по алгебре, геометрии и началам анализа...',
            'data_type': 'demo_variant',
            'subject': 'mathematics',
            'exam_type': 'ege',
            'url': 'https://fipi.ru/ege/demo-varianty-po-matematike',
            'content_hash': 'sample_math_2024_hash',
            'collected_at': timezone.now()
        },
        {
            'title': 'Спецификация ЕГЭ по русскому языку 2024',
            'content': 'Структура экзамена, критерии оценивания, типы заданий...',
            'data_type': 'specification',
            'subject': 'russian',
            'exam_type': 'ege',
            'url': 'https://fipi.ru/ege/specifikacii-po-russkomu-yazyku',
            'content_hash': 'sample_russian_2024_hash',
            'collected_at': timezone.now()
        },
        {
            'title': 'Кодификатор ЕГЭ по физике 2024',
            'content': 'Элементы содержания, проверяемые на ЕГЭ по физике...',
            'data_type': 'codifier',
            'subject': 'physics',
            'exam_type': 'ege',
            'url': 'https://fipi.ru/ege/kodifikatory-po-fizike',
            'content_hash': 'sample_physics_2024_hash',
            'collected_at': timezone.now()
        }
    ]
    
    created_count = 0
    for doc_data in sample_docs:
        doc, created = FIPIData.objects.get_or_create(  # type: ignore
            url=doc_data['url'],
            defaults=doc_data
        )
        if created:
            created_count += 1
            print(f"✅ Создан: {doc.title}")
    
    print(f"✅ Создано {created_count} примеров документов")
    return created_count

def main():
    """Основная функция наполнения сайта"""
    print("🎯 АВТОМАТИЧЕСКОЕ НАПОЛНЕНИЕ САЙТА EXAMFLOW 2.0")
    print("=" * 60)
    
    try:
        # 1. Инициализация карты источников
        sources_created = init_source_map()
        
        # 2. Создание примеров данных
        samples_created = create_sample_data()
        
        # 3. Запуск движка сбора данных
        engine = start_ingestion_engine()
        
        # 4. Мониторинг прогресса
        docs_collected = monitor_progress(engine)
        
        # 5. Обработка PDF документов
        pdf_processed = process_pdf_documents()
        
        # 6. Остановка движка
        engine.stop()
        
        # Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"🗺️  Источников создано: {sources_created}")
        print(f"📝 Примеров создано: {samples_created}")
        print(f"📄 Документов собрано: {docs_collected}")
        print(f"📄 PDF обработано: {pdf_processed}")
        print(f"📋 Всего в базе: {FIPIData.objects.count()}")  # type: ignore
        
        if FIPIData.objects.count() > 0:  # type: ignore    
            print("\n🎉 Сайт успешно наполнен данными!")
            print("\n📝 СЛЕДУЮЩИЕ ШАГИ:")
            print("1. Запустите сервер: python manage.py runserver")
            print("2. Откройте сайт: http://localhost:8000")
            print("3. Проверьте работу AI-ассистента")
            print("4. Протестируйте премиум-функции")
        else:
            print("\n⚠️  Данные не были собраны. Проверьте настройки.")
            
    except Exception as e:
        print(f"\n❌ Ошибка при наполнении сайта: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
