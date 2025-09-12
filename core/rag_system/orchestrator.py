"""
RAG Оркестратор - центральный сервис для управления запросами и генерации ответов
"""

import logging
import time
import hashlib
from typing import List, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Центральный оркестратор для RAG системы
    """

    def __init__(self):
        # Получаем настройки из конфигурации
        rag_config = getattr(settings, 'RAG_CONFIG', {})
        cache_config = getattr(settings, 'CACHE_TTL', {})
        
        self.max_context_tokens = rag_config.get('MAX_CONTEXT_LENGTH', 4000)
        self.max_response_tokens = 1000  # Максимум токенов для ответа
        self.timeout_seconds = 30  # Таймаут для AI запросов
        self.cache_ttl = cache_config.get('RAG_RESULTS', 600)  # 10 минут по умолчанию
        self.top_k_chunks = rag_config.get('MAX_SOURCES', 5)
        self.similarity_threshold = rag_config.get('SIMILARITY_THRESHOLD', 0.7)

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
            # Проверяем кеш полного ответа
            cached_result = self._get_cached_ai_response(query, subject, document_type)
            if cached_result:
                logger.info(f"Ответ получен из кеша для запроса: {query[:50]}...")
                cached_result['cached'] = True
                return cached_result

            # Проверяем кеш результатов поиска
            search_results = self._get_cached_search_results(query, subject, document_type)
            
            if not search_results:
                # Выполняем семантический поиск
                from core.rag_system.vector_store import VectorStore
                vector_store = VectorStore()
                
                search_results = vector_store.semantic_search(
                    query=query,
                    subject_filter=subject,
                    document_type_filter=document_type,
                    limit=self.top_k_chunks
                )
                
                # Кэшируем результаты поиска
                if search_results:
                    self._cache_search_results(query, subject, document_type, search_results)
                    logger.info(f"Результаты поиска сохранены в кеш для запроса: {query[:50]}...")
            else:
                logger.info(f"Результаты поиска получены из кеша для запроса: {query[:50]}...")

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
            self._cache_ai_response(query, subject, document_type, result)
            
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

    def _generate_cache_key(self, query: str, subject: str, document_type: str, cache_type: str = "query") -> str:
        """
        Генерирует ключ кеша для запроса
        """
        content = f"{query}|{subject}|{document_type}"
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return f"rag_{cache_type}:{hash_key}"
    
    def _get_cached_search_results(self, query: str, subject: str, document_type: str) -> Optional[List[Dict]]:
        """
        Получает результаты семантического поиска из кеша
        """
        cache_key = self._generate_cache_key(query, subject, document_type, "search")
        return cache.get(cache_key)
    
    def _cache_search_results(self, query: str, subject: str, document_type: str, results: List[Dict]) -> None:
        """
        Сохраняет результаты семантического поиска в кеш
        """
        cache_key = self._generate_cache_key(query, subject, document_type, "search")
        # Кэшируем результаты поиска на более длительное время
        cache.set(cache_key, results, timeout=self.cache_ttl * 2)
    
    def _get_cached_ai_response(self, query: str, subject: str, document_type: str) -> Optional[Dict]:
        """
        Получает ответ AI из кеша
        """
        cache_key = self._generate_cache_key(query, subject, document_type, "ai_response")
        return cache.get(cache_key)
    
    def _cache_ai_response(self, query: str, subject: str, document_type: str, response: Dict) -> None:
        """
        Сохраняет ответ AI в кеш
        """
        cache_key = self._generate_cache_key(query, subject, document_type, "ai_response")
        cache.set(cache_key, response, timeout=self.cache_ttl)

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

    def get_fallback_response(self, query: str) -> str:
        """
        Возвращает простой fallback-ответ без обращения к внешнему AI.

        Используется при региональных ограничениях или сбоях API.
        """
        safe_query = (query or '').strip()
        prefix = "Сейчас недоступна генерация подробного ответа. Дам краткую подсказку."
        if not safe_query:
            return f"{prefix}\n\nПопробуйте уточнить запрос: добавьте тему, класс и тип задания."
        return (
            f"{prefix}\n\nВаш запрос: '{safe_query}'.\n"
            "Попробуйте: 1) уточнить формулировку, 2) разделить на подшаги, "
            "3) указать предмет (Математика/Русский) и тип документа (demo_variant/codifier/specification)."
        )

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