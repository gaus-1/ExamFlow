"""
Команда для тестирования RAG-системы
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from core.rag_system.orchestrator import AIOrchestrator
from core.rag_system.vector_store import VectorStore
from core.rag_system.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирует RAG-систему ExamFlow'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            help='Тестовый запрос для RAG-системы',
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Запустить полное тестирование всех компонентов',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показать статистику системы',
        )
    
    def handle(self, *args, **options):
        if options['stats']:
            self.show_statistics()
            return
        
        if options['test_all']:
            self.run_full_test()
            return
        
        if options['query']:
            self.test_query(options['query'])
            return
        
        # Интерактивный режим
        self.interactive_mode()
    
    def show_statistics(self):
        """Показывает статистику RAG-системы"""
        self.stdout.write(
            self.style.SUCCESS('📊 Статистика RAG-системы ExamFlow')
        )
        
        try:
            # Статистика векторного хранилища
            vector_store = VectorStore()
            stats = vector_store.get_statistics()
            
            self.stdout.write(f"📚 Всего источников данных: {stats.get('total_sources', 0)}")
            self.stdout.write(f"🧩 Всего чанков: {stats.get('total_chunks', 0)}")
            self.stdout.write(f"✅ Обработано источников: {stats.get('processed_sources', 0)}")
            self.stdout.write(f"📈 Процент обработки: {stats.get('processing_percentage', 0):.1f}%")
            
            # Статистика базы данных
            from core.models import FIPIData, DataChunk
            
            total_fipi = FIPIData.objects.count()
            processed_fipi = FIPIData.objects.filter(is_processed=True).count()
            total_chunks = DataChunk.objects.count()
            
            self.stdout.write(f"\n📋 Детальная статистика:")
            self.stdout.write(f"   - Записей ФИПИ: {total_fipi}")
            self.stdout.write(f"   - Обработано: {processed_fipi}")
            self.stdout.write(f"   - Чанков в БД: {total_chunks}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при получении статистики: {e}')
            )
    
    def run_full_test(self):
        """Запускает полное тестирование всех компонентов"""
        self.stdout.write(
            self.style.SUCCESS('🧪 Запуск полного тестирования RAG-системы...')
        )
        
        # Тест 1: Векторное хранилище
        self.stdout.write("\n1️⃣ Тестирование векторного хранилища...")
        try:
            vector_store = VectorStore()
            test_text = "Тестовый текст для создания эмбеддинга"
            embedding = vector_store.create_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Эмбеддинг создан (размер: {len(embedding)})")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Ошибка создания эмбеддинга")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Ошибка векторного хранилища: {e}")
            )
        
        # Тест 2: Текстовый процессор
        self.stdout.write("\n2️⃣ Тестирование текстового процессора...")
        try:
            processor = TextProcessor()
            test_text = "Это тестовый текст для разбиения на чанки. " * 50
            chunks = processor.create_chunks(test_text)
            
            if chunks and len(chunks) > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Создано {len(chunks)} чанков")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Ошибка создания чанков")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Ошибка текстового процессора: {e}")
            )
        
        # Тест 3: Оркестратор
        self.stdout.write("\n3️⃣ Тестирование оркестратора...")
        try:
            orchestrator = AIOrchestrator()
            test_query = "Что такое квадратное уравнение?"
            response = orchestrator.process_query(test_query)
            
            if response and 'answer' in response:
                self.stdout.write(
                    self.style.SUCCESS("   ✅ Оркестратор работает")
                )
                self.stdout.write(f"   📝 Ответ: {response['answer'][:100]}...")
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Ошибка оркестратора")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Ошибка оркестратора: {e}")
            )
        
        # Тест 4: Семантический поиск
        self.stdout.write("\n4️⃣ Тестирование семантического поиска...")
        try:
            vector_store = VectorStore()
            search_results = vector_store.search("математика", limit=3)
            
            if search_results is not None:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Найдено {len(search_results)} результатов")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Ошибка поиска")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Ошибка поиска: {e}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Тестирование завершено!")
        )
    
    def test_query(self, query):
        """Тестирует конкретный запрос"""
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Тестирование запроса: "{query}"')
        )
        
        try:
            orchestrator = AIOrchestrator()
            response = orchestrator.process_query(query)
            
            self.stdout.write("\n📝 Ответ:")
            self.stdout.write(f"   {response.get('answer', 'Нет ответа')}")
            
            if 'sources' in response and response['sources']:
                self.stdout.write("\n📚 Источники:")
                for i, source in enumerate(response['sources'], 1):
                    self.stdout.write(f"   {i}. {source.get('title', 'Без названия')}")
                    self.stdout.write(f"      URL: {source.get('url', 'Нет URL')}")
                    self.stdout.write(f"      Релевантность: {source.get('relevance', 0):.2f}")
            
            if 'practice' in response:
                practice = response['practice']
                self.stdout.write(f"\n💪 Практика: {practice.get('description', 'Нет описания')}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при тестировании: {e}')
            )
    
    def interactive_mode(self):
        """Интерактивный режим тестирования"""
        self.stdout.write(
            self.style.SUCCESS('🎮 Интерактивный режим тестирования RAG-системы')
        )
        self.stdout.write("Введите 'exit' для выхода, 'stats' для статистики")
        
        try:
            orchestrator = AIOrchestrator()
            
            while True:
                query = input("\n❓ Ваш вопрос: ").strip()
                
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'stats':
                    self.show_statistics()
                    continue
                elif not query:
                    continue
                
                self.stdout.write("🤔 Обрабатываю запрос...")
                
                try:
                    response = orchestrator.process_query(query)
                    
                    self.stdout.write("\n💡 Ответ:")
                    self.stdout.write(f"   {response.get('answer', 'Нет ответа')}")
                    
                    if 'sources' in response and response['sources']:
                        self.stdout.write(f"\n📚 Найдено {len(response['sources'])} источников")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Ошибка: {e}")
                    )
        
        except KeyboardInterrupt:
            self.stdout.write("\n👋 До свидания!")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка в интерактивном режиме: {e}")
            )
