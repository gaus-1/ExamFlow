"""
RAG Оркестратор - центральный сервис для управления запросами и генерации ответов
"""

import logging
import time
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Центральный оркестратор для RAG системы
    """

    def __init__(self):
        self.max_context_tokens = 4000  # Максимум токенов для контекста
        self.max_response_tokens = 1000  # Максимум токенов для ответа
        self.timeout_seconds = 30  # Таймаут для AI запросов
        self.cache_ttl = 3600  # TTL кеша в секундах (1 час)
        self.top_k_chunks = 5  # Количество чанков для контекста

    def process_query(
            self,
            query: str,
            subject: str = "",
            document_type: str = "",
            user_id: Optional[int] = None) -> Dict:
        """
        Обрабатывает пользовательский запрос через RAG систему
        """
        start_time = time.time()
        
        try:
            # Проверяем кеш
            cache_key = self._generate_cache_key(query, subject, document_type)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Ответ получен из кеша для запроса: {query[:50]}...")
                return cached_result

            # Выполняем семантический поиск
            from core.rag_system.vector_store import VectorStore
            vector_store = VectorStore()
            
            search_results = vector_store.semantic_search(
                query=query,
                subject_filter=subject,
                document_type_filter=document_type,
                limit=self.top_k_chunks
            )

            if not search_results:
                return {
                    'answer': 'Извините, не удалось найти релевантную информацию по вашему запросу.',
                    'sources': [],
                    'context_chunks': 0,
                    'processing_time': time.time() - start_time,
                    'cached': False
                }

            # Агрегируем контекст
            context = self._aggregate_context(search_results)
            
            # Генерируем ответ с помощью AI
            answer = self._generate_answer(query, context, subject)
            
            # Форматируем источники
            sources = self._format_sources(search_results)

            result = {
                'answer': answer,
                'sources': sources,
                'context_chunks': len(search_results),
                'processing_time': time.time() - start_time,
                'cached': False,
                'query': query,
                'subject': subject,
                'document_type': document_type
            }

            # Сохраняем в кеш
            cache.set(cache_key, result, self.cache_ttl)
            
            # Обновляем профиль пользователя (если есть)
            if user_id:
                self._update_user_profile(user_id, query, subject, search_results)

            logger.info(f"Запрос обработан за {result['processing_time']:.2f}с")
            return result

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return {
                'answer': 'Произошла ошибка при обработке вашего запроса. Попробуйте позже.',
                'sources': [],
                'context_chunks': 0,
                'processing_time': time.time() - start_time,
                'cached': False,
                'error': str(e)
            }

    def _generate_cache_key(self, query: str, subject: str, document_type: str) -> str:
        """
        Генерирует ключ кеша для запроса
        """
        content = f"{query}|{subject}|{document_type}"
        return f"rag_query:{hashlib.md5(content.encode()).hexdigest()}"

    def _aggregate_context(self, search_results: List[Dict]) -> str:
        """
        Агрегирует контекст из результатов поиска с учетом лимитов токенов
        """
        context_parts = []
        current_tokens = 0
        
        for result in search_results:
            # Примерная оценка токенов (1 токен ≈ 4 символа)
            chunk_tokens = len(result['text']) // 4
            
            if current_tokens + chunk_tokens > self.max_context_tokens:
                break
                
            context_parts.append(f"[{result['source_title']}] {result['text']}")
            current_tokens += chunk_tokens

        return "\n\n".join(context_parts)

    def _generate_answer(self, query: str, context: str, subject: str) -> str:
        """
        Генерирует ответ с помощью AI с учетом лимитов токенов
        """
        try:
            import google.generativeai as genai
            import time

            # Настраиваем API
            genai.configure(api_key=settings.GEMINI_API_KEY)  # type: ignore

            # Создаем промпт
            prompt = self._create_prompt(query, context, subject)

            # Создаем модель с ограничениями
            model = genai.GenerativeModel(  # type: ignore
                model_name="gemini-1.5-flash",
                generation_config=genai.GenerationConfig(  # type: ignore
                    max_output_tokens=self.max_response_tokens,
                    temperature=0.7,
                    top_p=0.8,
                )
            )

            # Генерируем ответ с таймаутом
            start_time = time.time()
            response = model.generate_content(prompt)
            
            if time.time() - start_time > self.timeout_seconds:
                raise TimeoutError("Превышен таймаут генерации ответа")

            return response.text

        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return f"Не удалось сгенерировать ответ: {str(e)}"

    def _create_prompt(self, query: str, context: str, subject: str) -> str:
        """
        Создает промпт для AI с учетом предмета и контекста
        """
        subject_context = f" по предмету {subject}" if subject else ""
        
        return f"""Ты - эксперт по подготовке к ЕГЭ{subject_context}. 
Отвечай на вопросы на основе предоставленного контекста из официальных материалов ФИПИ.

Контекст:
{context}

Вопрос: {query}

Требования к ответу:
1. Используй только информацию из предоставленного контекста
2. Если информации недостаточно, честно скажи об этом
3. Структурируй ответ четко и понятно
4. Укажи конкретные источники, если это уместно
5. Дай практические рекомендации для подготовки

Ответ:"""

    def _format_sources(self, search_results: List[Dict]) -> List[Dict]:
        """
        Форматирует источники для ответа
        """
        sources = []
        seen_sources = set()
        
        for result in search_results:
            source_key = f"{result['source_title']}|{result['source_url']}"
            if source_key not in seen_sources:
                sources.append({
                    'title': result['source_title'],
                    'url': result['source_url'],
                    'type': result['source_type'],
                    'subject': result['subject'],
                    'similarity': result['similarity']
                })
                seen_sources.add(source_key)
        
        return sources

    def _update_user_profile(
            self,
            user_id: int,
            query: str,
            subject: str,
            search_results: List[Dict]) -> None:
        """
        Обновляет профиль пользователя на основе взаимодействия
        """
        try:
            from core.models import UserProfile  # type: ignore
            
            profile, created = UserProfile.objects.get_or_create(user_id=user_id)  # type: ignore
            
            # Обновляем статистику запросов
            if not hasattr(profile, 'query_stats'):
                profile.query_stats = {}
            
            subject_key = subject or 'general'
            if subject_key not in profile.query_stats:
                profile.query_stats[subject_key] = 0
            profile.query_stats[subject_key] += 1
            
            # Обновляем последние запросы
            if not hasattr(profile, 'recent_queries'):
                profile.recent_queries = []
            
            profile.recent_queries.append({
                'query': query,
                'subject': subject,
                'timestamp': timezone.now().isoformat(),
                'results_count': len(search_results)
            })
            
            # Ограничиваем количество последних запросов
            if len(profile.recent_queries) > 50:
                profile.recent_queries = profile.recent_queries[-50:]
            
            profile.save()
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля пользователя: {e}")

    def get_statistics(self) -> Dict:
        """
        Возвращает статистику работы оркестратора
        """
        try:
            from core.rag_system.vector_store import VectorStore
            
            vector_stats = VectorStore().get_statistics()
            
            return {
                'vector_store': vector_stats,
                'cache_size': len(cache._cache) if hasattr(cache, '_cache') else 0,
                'max_context_tokens': self.max_context_tokens,
                'max_response_tokens': self.max_response_tokens,
                'timeout_seconds': self.timeout_seconds,
                'cache_ttl': self.cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}