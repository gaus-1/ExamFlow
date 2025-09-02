"""
Процессор для разбиения текста на чанки
"""

import re
import logging
from typing import List, Dict, Tuple
from django.utils import timezone

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Класс для обработки и разбиения текста на чанки
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def clean_text(self, text: str) -> str:
        """
        Очищает текст от лишних символов и форматирования
        """
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Разбивает текст на предложения
        """
        # Простое разбиение по знакам препинания
        sentences = re.split(r'[.!?]+', text)
        
        # Очищаем и фильтруем предложения
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Игнорируем слишком короткие предложения
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    def create_chunks(self, text: str, metadata: Dict = None) -> List[Dict]: # type: ignore
        """
        Создает чанки из текста
        """
        try:
            # Очищаем текст
            clean_text = self.clean_text(text)
            
            # Разбиваем на предложения
            sentences = self.split_into_sentences(clean_text)
            
            chunks = []
            current_chunk = ""
            chunk_index = 0
            
            for sentence in sentences:
                # Проверяем, поместится ли предложение в текущий чанк
                if len(current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk += sentence + ". "
                else:
                    # Сохраняем текущий чанк
                    if current_chunk.strip():
                        chunks.append({
                            'text': current_chunk.strip(),
                            'index': chunk_index,
                            'metadata': metadata or {}
                        })
                        chunk_index += 1
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_text = self.get_overlap_text(current_chunk)
                    current_chunk = overlap_text + sentence + ". "
            
            # Добавляем последний чанк
            if current_chunk.strip():
                chunks.append({
                    'text': current_chunk.strip(),
                    'index': chunk_index,
                    'metadata': metadata or {}
                })
            
            logger.info(f"Создано {len(chunks)} чанков из текста длиной {len(clean_text)} символов")
            return chunks
            
        except Exception as e:
            logger.error(f"Ошибка при создании чанков: {e}")
            return []
    
    def get_overlap_text(self, text: str) -> str:
        """
        Получает текст для перекрытия между чанками
        """
        if len(text) <= self.overlap:
            return text
        
        # Берем последние символы для перекрытия
        overlap_text = text[-self.overlap:]
        
        # Находим последнее предложение в перекрытии
        sentences = self.split_into_sentences(overlap_text)
        if sentences:
            return sentences[-1] + ". "
        
        return ""
    
    def process_fipi_data(self, fipi_data_id: int) -> bool:
        """
        Обрабатывает данные ФИПИ и создает чанки
        """
        try:
            from core.models import FIPIData, DataChunk
            from core.rag_system.vector_store import VectorStore
            
            # Получаем данные ФИПИ
            fipi_data = FIPIData.objects.get(id=fipi_data_id) # type: ignore
            
            if not fipi_data.content:
                logger.warning(f"Нет содержимого для обработки: {fipi_data.title}")
                return False
            
            # Создаем чанки
            chunks = self.create_chunks(
                fipi_data.content,
                {
                    'source_type': fipi_data.data_type,
                    'subject': fipi_data.subject,
                    'url': fipi_data.url,
                    'collected_at': fipi_data.collected_at.isoformat()
                }
            )
            
            # Создаем векторное хранилище
            vector_store = VectorStore()
            
            # Сохраняем чанки
            for chunk_data in chunks:
                success = vector_store.add_chunk(
                    chunk_data['text'],
                    fipi_data_id,
                    chunk_data['index'],
                    chunk_data['metadata']
                )
                
                if not success:
                    logger.error(f"Ошибка при сохранении чанка {chunk_data['index']}")
                    return False
            
            # Отмечаем данные как обработанные
            fipi_data.mark_as_processed()
            
            logger.info(f"Обработаны данные ФИПИ: {fipi_data.title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обработке данных ФИПИ {fipi_data_id}: {e}")
            return False
    
    def process_all_unprocessed_data(self) -> Dict:
        """
        Обрабатывает все необработанные данные
        """
        try:
            from core.models import FIPIData
            
            # Получаем необработанные данные
            unprocessed_data = FIPIData.objects.filter( # type: ignore  
                is_processed=False,
                content__isnull=False
            ).exclude(content='')
            
            results = {
                'total': unprocessed_data.count(),
                'processed': 0,
                'errors': 0,
                'started_at': timezone.now()
            }
            
            for data in unprocessed_data:
                try:
                    if self.process_fipi_data(data.id):
                        results['processed'] += 1
                    else:
                        results['errors'] += 1
                except Exception as e:
                    logger.error(f"Ошибка при обработке {data.id}: {e}")
                    results['errors'] += 1
            
            results['completed_at'] = timezone.now()
            logger.info(f"Обработка завершена: {results['processed']}/{results['total']} успешно")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при массовой обработке: {e}")
            return {'error': str(e)}
