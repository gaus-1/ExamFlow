"""
🚀 Оптимизированный AI сервис для ExamFlow

Единый сервис для всех AI операций:
- Управление провайдерами
- RAG интеграция
- Кэширование
- Лимиты
- Персонализация
"""

import logging
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction

from .config import ai_config
from .models import AiRequest, AiResponse, AiProvider, AiLimit
from core.rag_system.orchestrator import RAGOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class AIResult:
    """Результат AI запроса"""
    text: str
    provider: str
    tokens_used: int = 0
    cost: float = 0.0
    cached: bool = False
    processing_time: float = 0.0

class OptimizedAIService:
    """Оптимизированный AI сервис с единой архитектурой"""
    
    def __init__(self):
        self.config = ai_config
        self.rag_orchestrator = RAGOrchestrator()
        self.logger = logging.getLogger(__name__)
    
    def ask(self, 
            prompt: str, 
            user: Optional[User] = None,
            task_type: str = 'chat',
            use_rag: bool = False,
            use_cache: bool = True) -> Dict[str, Any]:
        """
        Главный метод для AI запросов
        
        Args:
            prompt: Вопрос пользователя
            user: Пользователь (опционально)
            task_type: Тип задачи (chat, task_explanation, hint_generation, etc.)
            use_rag: Использовать RAG систему
            use_cache: Использовать кэш
            
        Returns:
            Результат AI запроса
        """
        start_time = time.time()
        
        try:
            # Валидация
            if not prompt or not prompt.strip():
                return {'error': 'Пустой запрос'}
            
            # Проверка лимитов
            if not self._check_limits(user):
                return {'error': 'Лимит запросов исчерпан'}
            
            # Проверка кэша
            if use_cache:
                cached_result = self._get_cached_result(prompt, task_type)
                if cached_result:
                    self._update_limits(user)
                    return cached_result
            
            # Выбор провайдера
            provider_config = self._get_best_provider(task_type)
            if not provider_config:
                return {'error': 'Нет доступных AI провайдеров'}
            
            # Подготовка промпта
            enhanced_prompt = self._prepare_prompt(prompt, user, task_type, use_rag)
            
            # Генерация ответа
            result = self._generate_response(enhanced_prompt, provider_config, task_type)
            
            # Обработка результата
            if 'error' in result:
                return result
            
            # Сохранение в кэш
            if use_cache:
                self._cache_result(prompt, task_type, result)
            
            # Обновление лимитов
            self._update_limits(user)
            
            # Логирование
            processing_time = time.time() - start_time
            self._log_request(user, prompt, result, processing_time)
            
            return {
                'response': result['text'],
                'provider': result['provider'],
                'tokens_used': result['tokens_used'],
                'cached': False,
                'processing_time': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка в AI сервисе: {e}")
            return {'error': f'Внутренняя ошибка: {str(e)}'}
    
    def explain_task(self, 
                    task_text: str, 
                    user: Optional[User] = None) -> Dict[str, Any]:
        """Объяснение решения задачи"""
        prompt = self.config.get_prompt_template(
            'TASK_EXPLANATION',
            task_text=task_text
        )
        
        return self.ask(prompt, user, 'task_explanation', use_rag=True)
    
    def get_hint(self, 
                task_text: str, 
                user: Optional[User] = None) -> Dict[str, Any]:
        """Получение подсказки для задачи"""
        prompt = self.config.get_prompt_template(
            'HINT_GENERATION',
            task_text=task_text
        )
        
        return self.ask(prompt, user, 'hint_generation', use_rag=True)
    
    def get_personalized_help(self, 
                            task_text: str, 
                            user: User,
                            user_level: int = 3,
                            weak_topics: List[str] = None, # type: ignore
                            strong_topics: List[str] = None) -> Dict[str, Any]: # type: ignore
        """Персонализированная помощь"""
        prompt = self.config.get_prompt_template(
            'PERSONALIZED_HELP',
            task_text=task_text,
            user_level=user_level,
            weak_topics=', '.join(weak_topics or []),
            strong_topics=', '.join(strong_topics or [])
        )
        
        return self.ask(prompt, user, 'personalized_help', use_rag=True)
    
    def get_learning_plan(self, 
                         user: User,
                         current_level: int = 3,
                         accuracy: float = 75.0,
                         weak_topics: List[str] = None, # type: ignore
                         goal: str = "Подготовка к ЕГЭ") -> Dict[str, Any]:
        """Получение плана обучения"""
        prompt = self.config.get_prompt_template(
            'LEARNING_PLAN',
            current_level=current_level,
            accuracy=accuracy,
            weak_topics=', '.join(weak_topics or []),
            goal=goal
        )
        
        return self.ask(prompt, user, 'learning_plan', use_rag=True)
    
    def _check_limits(self, user: Optional[User]) -> bool:
        """Проверка лимитов пользователя"""
        try:
            is_authenticated = user and user.is_authenticated
            limits = self.config.get_limits_for_user(is_authenticated) # type: ignore
            
            # Получаем или создаем лимит
            limit, created = AiLimit.objects.get_or_create( # type: ignore
                user=user if is_authenticated else None,
                session_id=None if is_authenticated else "guest",
                limit_type="daily",
                defaults={
                    'current_usage': 0,
                    'max_limit': limits['daily'],
                    'reset_date': timezone.now() + timezone.timedelta(days=1)
                }
            )
            
            # Проверяем сброс лимита
            if timezone.now() >= limit.reset_date:
                limit.current_usage = 0
                limit.max_limit = limits['daily']
                limit.reset_date = timezone.now() + timezone.timedelta(days=1)
                limit.save()
            
            return limit.current_usage < limit.max_limit
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки лимитов: {e}")
            return True  # Разрешаем запрос в случае ошибки
    
    def _update_limits(self, user: Optional[User]):
        """Обновление лимитов пользователя"""
        try:
            is_authenticated = user and user.is_authenticated
            limit = AiLimit.objects.filter( # type: ignore
                user=user if is_authenticated else None,
                session_id=None if is_authenticated else "guest",
                limit_type="daily"
            ).first()
            
            if limit:
                limit.current_usage += 1
                limit.save()
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления лимитов: {e}")
    
    def _get_cached_result(self, prompt: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Получение результата из кэша"""
        try:
            cache_key = f"ai_response:{hashlib.sha256(prompt.encode()).hexdigest()}:{task_type}"
            cached = cache.get(cache_key)
            
            if cached:
                self.logger.info(f"Результат получен из кэша для: {prompt[:50]}...")
                return {
                    'response': cached['text'],
                    'provider': cached['provider'],
                    'tokens_used': cached['tokens_used'],
                    'cached': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    def _cache_result(self, prompt: str, task_type: str, result: Dict[str, Any]):
        """Сохранение результата в кэш"""
        try:
            cache_key = f"ai_response:{hashlib.sha256(prompt.encode()).hexdigest()}:{task_type}"
            cache_data = {
                'text': result['text'],
                'provider': result['provider'],
                'tokens_used': result['tokens_used']
            }
            
            cache.set(cache_key, cache_data, self.config.rag.cache_ttl)
            self.logger.info(f"Результат сохранен в кэш для: {prompt[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в кэш: {e}")
    
    def _get_best_provider(self, task_type: str) -> Optional[Any]:
        """Выбор лучшего провайдера для задачи"""
        try:
            # Пока используем основной провайдер
            return self.config.get_primary_provider()
            
        except Exception as e:
            self.logger.error(f"Ошибка выбора провайдера: {e}")
            return None
    
    def _prepare_prompt(self, 
                       prompt: str, 
                       user: Optional[User], 
                       task_type: str,
                       use_rag: bool) -> str:
        """Подготовка промпта с контекстом"""
        try:
            # Базовый промпт
            enhanced_prompt = prompt
            
            # Добавляем системный промпт
            if task_type != 'chat':
                system_prompt = self.config.get_prompt_template('SYSTEM_BASE')
                enhanced_prompt = f"{system_prompt}\n\n{enhanced_prompt}"
            
            # Используем RAG если нужно
            if use_rag:
                rag_result = self.rag_orchestrator.process_query(
                    prompt,
                    user_id=user.id if user else None # type: ignore
                )
                
                if rag_result.get('sources'):
                    enhanced_prompt += f"\n\nКонтекст из базы знаний:\n{rag_result['answer']}"
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Ошибка подготовки промпта: {e}")
            return prompt
    
    def _generate_response(self, 
                          prompt: str, 
                          provider_config: Any, 
                          task_type: str) -> Dict[str, Any]:
        """Генерация ответа через провайдер"""
        try:
            # Здесь должна быть логика вызова конкретного провайдера
            # Пока возвращаем заглушку
            return {
                'text': f"Ответ от {provider_config.name}: {prompt[:100]}...",
                'provider': provider_config.name,
                'tokens_used': 100
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа: {e}")
            return {'error': f'Ошибка генерации: {str(e)}'}
    
    def _log_request(self, 
                    user: Optional[User], 
                    prompt: str, 
                    result: Dict[str, Any], 
                    processing_time: float):
        """Логирование запроса"""
        try:
            AiRequest.objects.create( # type: ignore
                user=user,
                session_id=None if user else "guest",
                request_type="question",
                prompt=prompt,
                response=result['text'],
                tokens_used=result['tokens_used'],
                cost=result.get('cost', 0.0),
                ip_address=None
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка логирования: {e}")

# Глобальный экземпляр сервиса
ai_service = OptimizedAIService()
