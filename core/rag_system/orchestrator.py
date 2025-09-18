"""
RAG Orchestrator - простая заглушка для совместимости
"""

import logging

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Простая заглушка RAG системы"""
    
    def __init__(self):
        self.initialized = False
    
    def search_similar_content(self, query: str, limit: int = 5):
        """Поиск похожего контента"""
        logger.info(f"RAG поиск: {query}")
        return []
    
    def get_context_for_query(self, query: str):
        """Получение контекста для запроса"""
        return ""
    
    def initialize(self):
        """Инициализация RAG системы"""
        self.initialized = True
        logger.info("RAG система инициализирована (заглушка)")
