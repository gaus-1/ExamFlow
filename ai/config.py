"""
🤖 Единая конфигурация для всех AI компонентов ExamFlow

Централизованные настройки для:
- AI провайдеров (Gemini, OpenAI, etc.)
- RAG системы
- Лимитов и кэширования
- Промптов и шаблонов
- Персонализации
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from django.conf import settings

@dataclass
class AIProviderConfig:
    """Конфигурация AI провайдера"""
    name: str
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    priority: int = 1
    is_active: bool = True

@dataclass
class RAGConfig:
    """Конфигурация RAG системы"""
    max_context_tokens: int = 4000
    max_response_tokens: int = 1000
    top_k_chunks: int = 5
    similarity_threshold: float = 0.7
    cache_ttl: int = 600  # 10 минут
    timeout_seconds: int = 30

@dataclass
class LimitsConfig:
    """Конфигурация лимитов"""
    daily_guest_limit: int = 10
    daily_auth_limit: int = 30
    weekly_auth_limit: int = 200
    monthly_auth_limit: int = 1000

@dataclass
class PromptTemplates:
    """Шаблоны промптов для разных типов задач"""
    
    # Базовые промпты
    SYSTEM_BASE = """Ты - эксперт по подготовке к ЕГЭ и ОГЭ. 
Отвечай кратко, структурированно и по делу.
Используй эмодзи для лучшего восприятия.
Всегда давай практические советы и примеры."""

    TASK_EXPLANATION = """Объясни решение этой задачи пошагово:

{task_text}

Требования:
- Объясни каждый шаг подробно
- Покажи альтернативные способы решения
- Укажи типичные ошибки
- Дай похожие задачи для практики"""

    HINT_GENERATION = """Дай подсказку для решения этой задачи:

{task_text}

Требования:
- НЕ давай полное решение
- Направь к правильному подходу
- Укажи ключевые моменты
- Дай наводящие вопросы"""

    PERSONALIZED_HELP = """Помоги ученику с учетом его уровня:

Уровень ученика: {user_level}/5
Слабые темы: {weak_topics}
Сильные темы: {strong_topics}

Задача: {task_text}

Дай персонализированное объяснение с учетом уровня ученика."""

    LEARNING_PLAN = """Создай план обучения для ученика:

Текущий уровень: {current_level}/5
Точность: {accuracy}%
Слабые темы: {weak_topics}
Цель: {goal}

Создай пошаговый план на неделю."""

class AIConfig:
    """Главный класс конфигурации AI системы"""
    
    def __init__(self):
        self.providers = self._load_providers()
        self.rag = self._load_rag_config()
        self.limits = self._load_limits_config()
        self.prompts = PromptTemplates()
    
    def _load_providers(self) -> List[AIProviderConfig]:
        """Загружает конфигурацию провайдеров"""
        providers = []
        
        # Gemini провайдер
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            providers.append(AIProviderConfig(
                name="gemini",
                api_key=settings.GEMINI_API_KEY,
                base_url=getattr(settings, 'GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta'),
                model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash'),
                temperature=0.7,
                max_tokens=1000,
                timeout=30,
                priority=1,
                is_active=True
            ))
        
        # OpenAI провайдер (если есть)
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            providers.append(AIProviderConfig(
                name="openai",
                api_key=settings.OPENAI_API_KEY,
                base_url=getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                temperature=0.7,
                max_tokens=1000,
                timeout=30,
                priority=2,
                is_active=True
            ))
        
        return providers
    
    def _load_rag_config(self) -> RAGConfig:
        """Загружает конфигурацию RAG системы"""
        rag_settings = getattr(settings, 'RAG_CONFIG', {})
        
        return RAGConfig(
            max_context_tokens=rag_settings.get('MAX_CONTEXT_LENGTH', 4000),
            max_response_tokens=rag_settings.get('MAX_RESPONSE_LENGTH', 1000),
            top_k_chunks=rag_settings.get('MAX_SOURCES', 5),
            similarity_threshold=rag_settings.get('SIMILARITY_THRESHOLD', 0.7),
            cache_ttl=rag_settings.get('CACHE_TTL', 600),
            timeout_seconds=rag_settings.get('TIMEOUT', 30)
        )
    
    def _load_limits_config(self) -> LimitsConfig:
        """Загружает конфигурацию лимитов"""
        limits_settings = getattr(settings, 'AI_LIMITS', {})
        
        return LimitsConfig(
            daily_guest_limit=limits_settings.get('DAILY_GUEST', 10),
            daily_auth_limit=limits_settings.get('DAILY_AUTH', 30),
            weekly_auth_limit=limits_settings.get('WEEKLY_AUTH', 200),
            monthly_auth_limit=limits_settings.get('MONTHLY_AUTH', 1000)
        )
    
    def get_provider_config(self, provider_name: str) -> AIProviderConfig:
        """Получает конфигурацию провайдера по имени"""
        for provider in self.providers:
            if provider.name == provider_name and provider.is_active:
                return provider
        raise ValueError(f"Провайдер {provider_name} не найден или неактивен")
    
    def get_active_providers(self) -> List[AIProviderConfig]:
        """Получает список активных провайдеров"""
        return [p for p in self.providers if p.is_active]
    
    def get_primary_provider(self) -> AIProviderConfig:
        """Получает основной провайдер (с наивысшим приоритетом)"""
        active_providers = self.get_active_providers()
        if not active_providers:
            raise ValueError("Нет активных AI провайдеров")
        
        return min(active_providers, key=lambda p: p.priority)
    
    def get_prompt_template(self, template_name: str, **kwargs) -> str:
        """Получает шаблон промпта с подстановкой переменных"""
        template = getattr(self.prompts, template_name.upper(), None)
        if not template:
            raise ValueError(f"Шаблон {template_name} не найден")
        
        return template.format(**kwargs)
    
    def get_limits_for_user(self, is_authenticated: bool) -> Dict[str, int]:
        """Получает лимиты для пользователя"""
        if is_authenticated:
            return {
                'daily': self.limits.daily_auth_limit,
                'weekly': self.limits.weekly_auth_limit,
                'monthly': self.limits.monthly_auth_limit
            }
        else:
            return {
                'daily': self.limits.daily_guest_limit,
                'weekly': self.limits.daily_guest_limit * 7,
                'monthly': self.limits.daily_guest_limit * 30
            }

# Глобальный экземпляр конфигурации
ai_config = AIConfig()

# Экспорт для удобства
__all__ = ['AIConfig', 'AIProviderConfig', 'RAGConfig', 'LimitsConfig', 'PromptTemplates', 'ai_config']
