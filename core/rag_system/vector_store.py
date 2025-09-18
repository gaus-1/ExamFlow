"""
Vector Store - простая заглушка для совместимости
"""

import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Простая заглушка векторного хранилища"""
    
    def __init__(self):
        self.data = []
    
    def add_document(self, content: str, metadata: dict = None):
        """Добавление документа"""
        logger.info(f"Добавлен документ: {content[:50]}...")
        self.data.append({
            'content': content,
            'metadata': metadata or {}
        })
    
    def search(self, query: str, limit: int = 5):
        """Поиск по векторам"""
        logger.info(f"Поиск в векторном хранилище: {query}")
        return []
    
    def initialize(self):
        """Инициализация хранилища"""
        logger.info("Векторное хранилище инициализировано (заглушка)")
