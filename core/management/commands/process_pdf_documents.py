"""
Команда для обработки PDF документов
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
import logging

from core.models import FIPIData
from core.data_ingestion.pdf_processor import process_pdf_document

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Обрабатывает PDF документы из базы данных'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Максимальное количество документов для обработки'
        )
        parser.add_argument(
            '--data-type',
            choices=['demo_variant', 'specification', 'codefier', 'open_bank_task'],
            help='Тип данных для обработки'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно переобработать уже обработанные документы'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать какие документы будут обработаны без фактической обработки'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        data_type = options.get('data_type')
        force = options['force']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('📄 Обработка PDF документов') # type: ignore
        )
        self.stdout.write('=' * 60)
        
        try:
            # Получаем документы для обработки
            documents = self._get_documents_to_process(data_type, force, limit)  # type: ignore
            
            if not documents:
                self.stdout.write(
                    self.style.WARNING('❌ Нет документов для обработки') # type: ignore
                )
                return
            
            if dry_run:
                self._show_documents_preview(documents)
                return
            
            # Обрабатываем документы
            self._process_documents(documents)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при обработке документов: {e}') # type: ignore
            )
            logger.error(f'Ошибка обработки PDF документов: {e}')
    
    def _get_documents_to_process(self, data_type: str, force: bool, limit: int):
        """Получает документы для обработки"""
        query = FIPIData.objects.all()  # type: ignore
        
        # Фильтр по типу данных
        if data_type:
            query = query.filter(data_type=data_type) # type: ignore
        
        # Фильтр по статусу обработки
        if not force:
            query = query.filter(is_processed=False) # type: ignore
        
        # Фильтр по URL (только PDF)
        query = query.filter(url__icontains='.pdf') # type: ignore
        
        # Сортировка по дате сбора
        query = query.order_by('collected_at') # type: ignore
        
        return query[:limit]
    
    def _show_documents_preview(self, documents):
        """Показывает превью документов для обработки"""
        self.stdout.write(f'📋 Найдено {len(documents)} документов для обработки:')
        self.stdout.write('')
        
        for doc in documents:
            status = "✅ Обработан" if doc.is_processed else "⏳ Ожидает" # type: ignore            
            self.stdout.write(f'  • {doc.title}')
            self.stdout.write(f'    Тип: {doc.get_data_type_display()}')  # type: ignore
            self.stdout.write(f'    Статус: {status}')
            self.stdout.write(f'    URL: {doc.url}')
            self.stdout.write(f'    Дата сбора: {doc.collected_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write('')
    
    def _process_documents(self, documents):
        """Обрабатывает документы"""
        total_documents = len(documents)
        processed_count = 0
        failed_count = 0
        
        self.stdout.write(f'🚀 Начинаем обработку {total_documents} документов...')
        self.stdout.write('')
        
        for i, document in enumerate(documents, 1):
            self.stdout.write(
                f'[{i}/{total_documents}] Обрабатываем: {document.title[:50]}...'
            )
            
            try:
                # Обрабатываем документ
                result = process_pdf_document(document)
                
                if result['status'] == 'completed':
                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS( # type: ignore
                            f'  ✅ Успешно обработан: {result["chunks_saved"]} чанков сохранено'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR( # type: ignore
                            f'  ❌ Ошибка: {result.get("error", "Неизвестная ошибка")}'
                        )
                    )
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Исключение: {e}') # type: ignore
                )
                logger.error(f'Ошибка обработки документа {document.id}: {e}')
            
            self.stdout.write('')
        
        # Итоговая статистика
        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'📊 Итоговая статистика:') # type: ignore
        )
        self.stdout.write(f'  Всего документов: {total_documents}')
        self.stdout.write(f'  Успешно обработано: {processed_count}')
        self.stdout.write(f'  Ошибок: {failed_count}')
        
        if processed_count > 0:
            success_rate = (processed_count / total_documents) * 100
            self.stdout.write(f'  Процент успеха: {success_rate:.1f}%')
