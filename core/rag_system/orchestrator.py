"""
RAG Orchestrator - полноценная система поиска и получения контекста
"""

import logging
from typing import Dict, List, Any, Optional
from django.db import models

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Полноценная RAG система для поиска контекста"""
    
    def __init__(self):
        self.initialized = True
        logger.info("RAG система инициализирована")
    
    def process_query(self, prompt: str, subject: str = "", user_id: int = None, limit: int = 5) -> Dict[str, Any]: # type: ignore
        """
        Обрабатывает запрос и возвращает релевантный контекст
        
        Args:
            prompt: Запрос пользователя
            subject: Предмет (математика, русский)
            user_id: ID пользователя
            limit: Максимальное количество результатов
            
        Returns:
            Dict с контекстом и источниками
        """
        try:
            # Поиск релевантных заданий и материалов
            sources = self._find_relevant_sources(prompt, subject, limit)
            
            # Формирование контекста
            context = self._build_context(sources, prompt)
            
            return {
                'context': context,
                'sources': sources,
                'context_chunks': len(sources),
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Ошибка в RAG запросе: {e}")
            return {
                'context': '',
                'sources': [],
                'context_chunks': 0,
                'subject': subject
            }
    
    def _find_relevant_sources(self, query: str, subject: str, limit: int) -> List[Dict[str, Any]]:
        """Поиск релевантных источников в базе данных"""
        try:
            from learning.models import Task, Subject
            
            sources = []
            
            # Поиск по предмету
            if subject:
                try:
                    subject_obj = Subject.objects.filter(name__icontains=subject).first() # type: ignore
                    if subject_obj:
                        tasks = Task.objects.filter(subject=subject_obj)[:limit] # type: ignore
                        
                        for task in tasks:
                            if self._is_relevant(query, task.title or "", task.content or ""):
                                sources.append({
                                    'title': task.title or f"Задание по {subject}",
                                    'content': task.content or "",
                                    'type': 'task',
                                    'subject': subject,
                                    'id': task.id
                                })
                except Exception as e:
                    logger.error(f"Ошибка поиска по предмету: {e}")
            
            # Если мало результатов, ищем по всем предметам
            if len(sources) < limit:
                try:
                    all_tasks = Task.objects.all()[:limit * 2] # type: ignore
                    
                    for task in all_tasks:
                        if len(sources) >= limit:
                            break
                            
                        if self._is_relevant(query, task.title or "", task.content or ""):
                            sources.append({
                                'title': task.title or "Задание",
                                'content': task.content or "",
                                'type': 'task',
                                'subject': task.subject.name if task.subject else "общее",
                                'id': task.id
                            })
                except Exception as e:
                    logger.error(f"Ошибка общего поиска: {e}")
            
            return sources[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка поиска источников: {e}")
            return []
    
    def _is_relevant(self, query: str, title: str, content: str) -> bool:
        """Простая проверка релевантности"""
        query_lower = query.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Ключевые слова для поиска
        query_words = set(query_lower.split())
        text_words = set((title_lower + " " + content_lower).split())
        
        # Если есть пересечение слов - считаем релевантным
        common_words = query_words.intersection(text_words)
        return len(common_words) > 0
    
    def _build_context(self, sources: List[Dict[str, Any]], query: str) -> str:
        """Построение контекста из найденных источников"""
        if not sources:
            return ""
        
        context_parts = []
        
        for source in sources:
            title = source.get('title', '')
            content = source.get('content', '')
            subject = source.get('subject', '')
            
            if title or content:
                part = f"[{subject}] {title}"
                if content:
                    # Ограничиваем длину контента
                    content_short = content[:200] + "..." if len(content) > 200 else content
                    part += f": {content_short}"
                
                context_parts.append(part)
        
        return "\n\n".join(context_parts)
    
    def search_similar_content(self, query: str, limit: int = 5):
        """Поиск похожего контента (для обратной совместимости)"""
        result = self.process_query(query, limit=limit)
        return result.get('sources', [])
    
    def get_context_for_query(self, query: str):
        """Получение контекста для запроса (для обратной совместимости)"""
        result = self.process_query(query)
        return result.get('context', '')
    
    def initialize(self):
        """Инициализация RAG системы"""
        self.initialized = True
        logger.info("RAG система инициализирована")
