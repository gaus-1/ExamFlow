"""
Dual AI Orchestrator для ExamFlow
Поддерживает Gemini и DeepSeek одновременно с fallback логикой
"""

import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.conf import settings

from .clients.gemini_client import GeminiClient
from .clients.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)


class DualAIOrchestrator:
    """
    Оркестратор для работы с двумя AI провайдерами:
    - Gemini (Google) - основной
    - DeepSeek - резервный или по выбору
    
    Поддерживает:
    - Автоматический fallback при ошибках
    - Кэширование ответов
    - Выбор провайдера по типу задачи
    - Мониторинг производительности
    """
    
    def __init__(self, cache_ttl_sec: int = 3600):
        self.cache_ttl_sec = cache_ttl_sec
        self.providers = {}
        self.provider_stats = {
            'gemini': {'requests': 0, 'errors': 0, 'avg_time': 0.0},
            'deepseek': {'requests': 0, 'errors': 0, 'avg_time': 0.0}
        }
        
        # Инициализируем провайдеров
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация AI провайдеров"""
        try:
            # Gemini клиент
            gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
            if gemini_key:
                self.providers['gemini'] = GeminiClient(api_key=gemini_key)
                logger.info("✅ Gemini клиент инициализирован")
            else:
                logger.warning("⚠️ GEMINI_API_KEY не найден")
            
            # DeepSeek клиент  
            deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
            if deepseek_key:
                self.providers['deepseek'] = DeepSeekClient(api_key=deepseek_key)
                logger.info("✅ DeepSeek клиент инициализирован")
            else:
                logger.warning("⚠️ DEEPSEEK_API_KEY не найден")
            
            if not self.providers:
                raise ValueError("Ни один AI провайдер не настроен!")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации AI провайдеров: {e}")
            raise
    
    def ask(self, prompt: str, provider: Optional[str] = None, use_fallback: bool = True) -> Dict[str, Any]:
        """
        Отправляет запрос к AI с поддержкой множественных провайдеров
        
        Args:
            prompt: Вопрос пользователя
            provider: Конкретный провайдер ('gemini' или 'deepseek')
            use_fallback: Использовать fallback при ошибках
        
        Returns:
            Dict с ответом и метаданными
        """
        # Проверяем кэш
        cache_key = self._make_cache_key(prompt, provider)
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"AI Orchestrator: cache hit для {provider or 'auto'}")
            return cached_response
        
        # Определяем порядок провайдеров
        provider_order = self._get_provider_order(prompt, provider)
        
        last_error = None
        
        for current_provider in provider_order:
            if current_provider not in self.providers:
                continue
                
            try:
                start_time = time.time()
                
                # Получаем ответ от провайдера
                if current_provider == 'gemini':
                    response = self._ask_gemini(prompt)
                elif current_provider == 'deepseek':
                    response = self._ask_deepseek(prompt)
                else:
                    continue
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Обновляем статистику
                self._update_stats(current_provider, processing_time, success=True)
                
                # Добавляем метаданные
                response['processing_time'] = processing_time
                response['provider_used'] = current_provider
                response['cache_key'] = cache_key
                
                # Кэшируем успешный ответ
                cache.set(cache_key, response, self.cache_ttl_sec)
                
                logger.info(f"AI ответ получен от {current_provider} за {processing_time:.2f}с")
                return response
                
            except Exception as e:
                self._update_stats(current_provider, 0.0, success=False)
                last_error = e
                logger.warning(f"Ошибка {current_provider}: {e}")
                
                if not use_fallback:
                    break
                    
                # Продолжаем с следующим провайдером
                continue
        
        # Если все провайдеры не сработали
        error_response = {
            'answer': 'Извините, AI сервисы временно недоступны. Попробуйте позже.',
            'sources': [],
            'processing_time': 0.0,
            'provider_used': 'none',
            'error': str(last_error) if last_error else 'Все провайдеры недоступны'
        }
        
        logger.error(f"Все AI провайдеры недоступны. Последняя ошибка: {last_error}")
        return error_response
    
    def _ask_gemini(self, prompt: str) -> Dict[str, Any]:
        """Запрос к Gemini с ролью ExamFlow"""
        client = self.providers['gemini']
        # type: ignore  # подавляем ошибку типизации для _build_gemini_prompt
        # Специальный промпт для Gemini с ролью ExamFlow
        gemini_prompt = self._build_gemini_prompt(prompt)  # type: ignore
        
        # Используем метод generate для совместимости
        if hasattr(client, 'generate'):
            answer = client.generate(gemini_prompt)
        else:
            # Fallback для новых версий клиента
            response = client.ask(gemini_prompt)
            answer = response.get('answer', '') if isinstance(response, dict) else str(response)
        
        # Проверяем и добавляем подпись ExamFlow если нужно
        if not any(word in answer.lower() for word in ['examflow', 'экзамфлоу']):
            answer = f"{answer}\n\n— ExamFlow AI"
        
        return {
            'answer': answer,
            'sources': [{'title': 'ExamFlow AI (Gemini)', 'url': 'https://examflow.ru'}],
            'provider': 'gemini'
        }
    
    def _ask_deepseek(self, prompt: str) -> Dict[str, Any]:
        """Запрос к DeepSeek"""
        client = self.providers['deepseek']
        return client.ask(prompt)
    
    def _get_provider_order(self, prompt: str, preferred: Optional[str] = None) -> List[str]:
        """Определяет порядок использования провайдеров"""
        if preferred and preferred in self.providers:
            # Если указан конкретный провайдер
            other_providers = [p for p in self.providers.keys() if p != preferred]
            return [preferred] + other_providers
        
        # Автоматический выбор на основе предметов ExamFlow
        prompt_lower = prompt.lower()
        
        # DeepSeek для МАТЕМАТИКИ (профильная и базовая)
        math_keywords = ['математика', 'уравнение', 'формула', 'решить', 'вычислить', 
                        'алгебра', 'геометрия', 'профильная', 'базовая', 'график',
                        'функция', 'производная', 'интеграл', 'логарифм', 'тригонометрия',
                        'x²', 'корень', 'дробь', 'процент', 'площадь', 'объем']
        
        if any(word in prompt_lower for word in math_keywords):
            return ['deepseek', 'gemini']  # DeepSeek первый для математики
        
        # Gemini для РУССКОГО ЯЗЫКА
        russian_keywords = ['русский', 'язык', 'орфография', 'пунктуация', 'сочинение', 
                           'изложение', 'текст', 'предложение', 'падеж', 'склонение',
                           'причастие', 'деепричастие', 'наречие', 'союз', 'частица',
                           'запятая', 'тире', 'двоеточие', 'литература', 'анализ']
        
        if any(word in prompt_lower for word in russian_keywords):
            return ['gemini', 'deepseek']  # Gemini первый для русского
        
        # По умолчанию: сначала более быстрый провайдер
        gemini_avg = self.provider_stats['gemini']['avg_time']
        deepseek_avg = self.provider_stats['deepseek']['avg_time']
        
        if gemini_avg > 0 and deepseek_avg > 0:
            if gemini_avg < deepseek_avg:
                return ['gemini', 'deepseek']
            else:
                return ['deepseek', 'gemini']
        
        # Дефолтный порядок
        return ['gemini', 'deepseek']
    
    def _update_stats(self, provider: str, processing_time: float, success: bool):
        """Обновляет статистику провайдера"""
        if provider not in self.provider_stats:
            return
        
        stats = self.provider_stats[provider]
        stats['requests'] += 1
        
        if success:
            # Обновляем среднее время
            if stats['avg_time'] == 0:
                stats['avg_time'] = processing_time
            else:
                stats['avg_time'] = (stats['avg_time'] + processing_time) / 2
        else:
            stats['errors'] += 1
    
    def _make_cache_key(self, prompt: str, provider: Optional[str] = None) -> str:
        """Создает ключ кэша"""
        cache_string = f"{prompt.lower().strip()}:{provider or 'auto'}"
        h = hashlib.sha256(cache_string.encode()).hexdigest()
        return f'ai:dual:{h}'
    
    def _build_prompt(self, user_prompt: str) -> str:
        """Строит промпт для AI"""
        return (
            "Ты - экспертный ИИ-ассистент ExamFlow для подготовки к ЕГЭ и ОГЭ.\n\n"
            "Твои задачи:\n"
            "- Помогать с решением задач по всем предметам\n"
            "- Объяснять сложные темы простым языком\n"
            "- Давать практические советы по подготовке\n"
            "- Мотивировать учеников\n\n"
            f"Вопрос: {user_prompt}\n\n"
            "Отвечай кратко, понятно и по существу."
        )
    
    def _build_gemini_prompt(self, user_prompt: str) -> str:
        """Строит специальный промпт для Gemini с ролью ExamFlow"""
        return f"""Ты - ExamFlow AI, дружелюбный помощник для подготовки к ЕГЭ и ОГЭ.

🎯 ТВОЯ РОЛЬ:
- Ты представляешься как "ExamFlow" или "ExamFlow AI"
- Ты ЭКСПЕРТ по РУССКОМУ ЯЗЫКУ для ЕГЭ и ОГЭ
- Ты помогаешь с орфографией, пунктуацией, сочинениями
- Ты объясняешь правила языка простыми словами

😊 СТИЛЬ ОБЩЕНИЯ:
- Отвечай ДРУЖЕЛЮБНО и с ПОНИМАНИЕМ
- Иногда добавляй уместные шутки или забавные сравнения (но не часто!)
- Используй эмодзи для наглядности: 📚 📝 ✅ 💡
- Говори "на равных" с учеником, как старший друг

📝 СПЕЦИАЛИЗАЦИЯ:
- Орфография и пунктуация
- Разбор предложений и текстов
- Помощь с сочинениями и изложениями
- Литературные термины и анализ

📋 ПРАВИЛА:
- Ответы до 5-6 предложений максимум
- Приводи примеры из классической литературы
- Иногда шути про русский язык: "Как сказал бы Пушкин...", "Этот падеж капризнее кота!"
- Всегда заканчивай подписью "— ExamFlow AI"

Вопрос ученика: {user_prompt}

Ответь дружелюбно, по существу, с легким юмором если уместно:"""
    
    def _build_deepseek_prompt(self, user_prompt: str) -> str:
        """Строит специальный промпт для DeepSeek с ролью ExamFlow"""
        return f"""Ты - ExamFlow AI, крутой помощник для подготовки к ЕГЭ и ОГЭ.

🎯 ТВОЯ РОЛЬ:
- Ты представляешься как "ExamFlow AI" или просто "ExamFlow"  
- Ты ЭКСПЕРТ по МАТЕМАТИКЕ, ФИЗИКЕ, ХИМИИ и точным наукам
- Ты решаешь задачи БЫСТРО и ЧЕТКО, как калькулятор с душой
- Ты можешь пошутить по теме, но не отвлекаешься от дела

🧮 СПЕЦИАЛИЗАЦИЯ:
- Математика: уравнения, функции, геометрия
- Физика: формулы, законы, задачи  
- Химия: реакции, формулы, расчеты

😄 СТИЛЬ С ЮМОРОМ:
- Отвечай БЫСТРО и КОНКРЕТНО (2-3 предложения)
- Иногда добавляй математические шутки или забавные аналогии
- Примеры юмора: "Как говорят математики...", "Эта формула проще пирога!", "x убегает, но мы его поймаем!"
- НО главное - РЕШЕНИЕ задачи, юмор только в дополнение

📐 ФОРМАТ ОТВЕТОВ:
- Пошаговое решение для задач
- Простая запись: x², √, ÷, ≠, ≤, ≥
- Всегда подпись "— ExamFlow AI"

Вопрос ученика: {user_prompt}

Реши быстро и четко, с легкой шуткой если уместно:"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования провайдеров"""
        return {
            'providers': self.provider_stats,
            'available_providers': list(self.providers.keys()),
            'cache_info': {
                'ttl_seconds': self.cache_ttl_sec
            }
        }
    
    def test_all_providers(self) -> Dict[str, bool]:
        """Тестирует все доступные провайдеры"""
        results = {}
        
        for provider_name, client in self.providers.items():
            try:
                if hasattr(client, 'test_connection'):
                    results[provider_name] = client.test_connection()
                else:
                    # Простой тест
                    test_response = self.ask("Тест", provider=provider_name, use_fallback=False)
                    results[provider_name] = 'error' not in test_response
            except Exception as e:
                logger.error(f"Тест {provider_name} не прошел: {e}")
                results[provider_name] = False
        
        return results
