"""
Dependency Injection Container для ExamFlow
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Container:
    """Контейнер зависимостей для ExamFlow"""
    
    _ai_orchestrator_instance = None
    _cache_instance = None
    _notifier_instance = None
    
    @classmethod
    def ai_orchestrator(cls):
        """Получить экземпляр AI оркестратора"""
        if cls._ai_orchestrator_instance is None:
            try:
                from ai.services import AiService
                cls._ai_orchestrator_instance = AiService()
                logger.info("AI оркестратор инициализирован через AiService")
            except ImportError:
                # Fallback на простую реализацию
                cls._ai_orchestrator_instance = SimpleAIOrchestrator()
                logger.warning("Используется простой AI оркестратор (fallback)")
        
        return cls._ai_orchestrator_instance
    
    @classmethod
    def cache(cls):
        """Получить экземпляр кэша"""
        if cls._cache_instance is None:
            try:
                from django.core.cache import cache
                cls._cache_instance = cache
                logger.info("Django cache инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации кэша: {e}")
                cls._cache_instance = DummyCache()
        
        return cls._cache_instance
    
    @classmethod
    def notifier(cls):
        """Получить экземпляр уведомлений"""
        if cls._notifier_instance is None:
            cls._notifier_instance = SimpleNotifier()
            logger.info("Простой нотификатор инициализирован")
        
        return cls._notifier_instance


class SimpleAIOrchestrator:
    """Простая реализация AI оркестратора для fallback"""
    
    def ask(self, prompt: str, **kwargs):
        """Простой метод получения ответа от AI"""
        try:
            import google.generativeai as genai
            from django.conf import settings
            
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            if not api_key:
                return {
                    'answer': 'Сервис ИИ временно недоступен',
                    'sources': [],
                    'error': 'API key not configured'
                }
            
            genai.configure(api_key=api_key)  # type: ignore
            model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
            
            # Системный промпт для ExamFlow
            system_prompt = """Ты - ExamFlow AI, эксперт по подготовке к ЕГЭ и ОГЭ.

🎯 СПЕЦИАЛИЗАЦИЯ:
📐 МАТЕМАТИКА:
- Профильная математика ЕГЭ (задания 1-19): уравнения, функции, производные, интегралы, геометрия, стереометрия
- Базовая математика ЕГЭ (задания 1-20): арифметика, алгебра, геометрия, статистика
- Математика ОГЭ (задания 1-26): алгебра, геометрия, реальная математика

📝 РУССКИЙ ЯЗЫК:
- ЕГЭ: сочинение (задание 27), грамматические нормы, орфография, пунктуация
- ОГЭ: изложение, сочинение, тестовые задания, грамматика

💬 СТИЛЬ ОБЩЕНИЯ:
- Краткий и конкретный ответ (до 300 слов)
- Пошаговые решения для математики
- Примеры и образцы для русского языка
- НЕ используй длинные вступления
- НЕ упоминай провайдера ИИ
- Если вопрос не по твоим предметам - скажи: "Я специализируюсь на математике и русском языке. Задайте вопрос по этим предметам!"

🚫 НЕ ДЕЛАЙ:
- Длинных приветствий
- Упоминаний о DeepSeek, Gemini или других ИИ
- Ответов на вопросы не по твоим предметам
- Слишком длинных объяснений"""
            
            full_prompt = f"{system_prompt}\n\n{prompt}"
            response = model.generate_content(full_prompt)
            
            if response.text:
                answer = response.text.strip()
                if len(answer) > 4000:
                    answer = answer[:4000] + "..."
                
                return {
                    'answer': answer,
                    'sources': [
                        {'title': 'ExamFlow AI', 'content': 'Персонализированный ответ'},
                        {'title': 'Математика ЕГЭ', 'content': 'Теория и практика'},
                        {'title': 'Русский язык ОГЭ', 'content': 'Правила и примеры'}
                    ]
                }
            else:
                return {
                    'answer': 'Не удалось получить ответ от ИИ. Попробуйте переформулировать вопрос.',
                    'sources': [],
                    'error': 'Empty response'
                }
                
        except Exception as e:
            logger.error(f"Ошибка в SimpleAIOrchestrator: {e}")
            return {
                'answer': f'Ошибка AI сервиса: попробуйте позже',
                'sources': [],
                'error': str(e)
            }


class DummyCache:
    """Заглушка для кэша"""
    
    def get(self, key, default=None):
        return default
    
    def set(self, key, value, timeout=None):
        pass
    
    def delete(self, key):
        pass


class SimpleNotifier:
    """Простая система уведомлений"""
    
    def send_notification(self, message: str, user_id: Optional[int] = None):
        """Отправка уведомления"""
        logger.info(f"Уведомление для {user_id or 'всех'}: {message}")
        return True
    
    def send_email(self, subject: str, message: str, recipient: str):
        """Отправка email"""
        logger.info(f"Email '{subject}' для {recipient}: {message}")
        return True
