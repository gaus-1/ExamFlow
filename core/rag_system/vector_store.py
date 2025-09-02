"""
Векторное хранилище для семантического поиска
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from django.conf import settings
import json
import hashlib

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Класс для работы с векторными представлениями
    """
    
    def __init__(self):
        self.embedding_dim = 768  # Размерность эмбеддингов Gemini
        self.similarity_threshold = 0.7  # Порог схожести
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Создает векторное представление текста
        """
        try:
            import google.generativeai as genai
            
            # Настраиваем API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Создаем эмбеддинг
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Ошибка при создании эмбеддинга: {e}")
            # Возвращаем нулевой вектор в случае ошибки
            return [0.0] * self.embedding_dim
    
    def create_query_embedding(self, query: str) -> List[float]:
        """
        Создает векторное представление запроса
        """
        try:
            import google.generativeai as genai
            
            # Настраиваем API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Создаем эмбеддинг для запроса
            result = genai.embed_content(
                model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Ошибка при создании эмбеддинга запроса: {e}")
            return [0.0] * self.embedding_dim
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Вычисляет косинусное сходство между векторами
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Нормализуем векторы
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Вычисляем косинусное сходство
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении сходства: {e}")
            return 0.0
    
    def find_similar_chunks(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """
        Находит наиболее похожие чанки
        """
        try:
            from core.models import DataChunk
            
            # Получаем все чанки
            chunks = DataChunk.objects.all()
            
            similarities = []
            
            for chunk in chunks:
                # Вычисляем сходство
                similarity = self.cosine_similarity(
                    query_embedding, 
                    chunk.embedding
                )
                
                if similarity >= self.similarity_threshold:
                    similarities.append({
                        'chunk': chunk,
                        'similarity': similarity,
                        'text': chunk.chunk_text,
                        'source': chunk.source_data,
                        'metadata': chunk.metadata
                    })
            
            # Сортируем по сходству
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих чанков: {e}")
            return []
    
    def add_chunk(self, text: str, source_data_id: int, chunk_index: int, metadata: Dict = None) -> bool:
        """
        Добавляет новый чанк в векторное хранилище
        """
        try:
            from core.models import DataChunk, FIPIData
            
            # Создаем эмбеддинг
            embedding = self.create_embedding(text)
            
            # Получаем исходные данные
            source_data = FIPIData.objects.get(id=source_data_id)
            
            # Создаем чанк
            chunk = DataChunk.objects.create(
                source_data=source_data,
                chunk_text=text,
                chunk_index=chunk_index,
                embedding=embedding,
                metadata=metadata or {}
            )
            
            logger.info(f"Добавлен чанк {chunk_index} для {source_data.title}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении чанка: {e}")
            return False
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Выполняет семантический поиск
        """
        try:
            # Создаем эмбеддинг запроса
            query_embedding = self.create_query_embedding(query)
            
            # Находим похожие чанки
            results = self.find_similar_chunks(query_embedding, limit)
            
            # Форматируем результаты
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'text': result['text'],
                    'similarity': result['similarity'],
                    'source_title': result['source'].title,
                    'source_url': result['source'].url,
                    'source_type': result['source'].data_type,
                    'subject': result['source'].subject,
                    'metadata': result['metadata']
                })
            
            logger.info(f"Найдено {len(formatted_results)} релевантных результатов для запроса: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Возвращает статистику векторного хранилища
        """
        try:
            from core.models import DataChunk, FIPIData
            
            total_chunks = DataChunk.objects.count()
            total_sources = FIPIData.objects.count()
            processed_sources = FIPIData.objects.filter(is_processed=True).count()
            
            return {
                'total_chunks': total_chunks,
                'total_sources': total_sources,
                'processed_sources': processed_sources,
                'processing_percentage': (processed_sources / total_sources * 100) if total_sources > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}
