import os
import json
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass

from django.utils import timezone
from django.conf import settings

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # на случай отсутствия в окружении

from .models import AiRequest, AiResponse, AiProvider, AiLimit
from .rag_service import rag_service


@dataclass
class AiResult:
    """Результат ответа ИИ"""
    text: str
    tokens_used: int = 0
    cost: float = 0.0
    provider_name: str = "local"


class BaseProvider:
    """Базовый интерфейс провайдера ИИ"""

    name: str = "base"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    """Провайдер Google Gemini AI - быстрый и надежный!"""

    name = "gemini"

    def __init__(self, model: Optional[str] = None, task_type: str = 'chat') -> None:
        # Используем настройки из Django settings
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.api_url = getattr(settings, 'GEMINI_BASE_URL', '')
        self.timeout = getattr(settings, 'GEMINI_TIMEOUT', 30)
        
        # Выбираем настройки для конкретного типа задачи
        task_configs = getattr(settings, 'GEMINI_TASK_CONFIGS', {})
        task_config = task_configs.get(task_type, task_configs.get('chat', {}))
        
        self.model = model or task_config.get('model', 'gemini-2.0-flash')
        self.temperature = task_config.get('temperature', 0.7)
        self.max_tokens = task_config.get('max_tokens', 1000)
        self.system_prompt = task_config.get('system_prompt', '')

    def is_available(self) -> bool:  # type: ignore
        """Проверяем доступность Gemini API"""
        return bool(self.api_key and self.api_url)

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:  # type: ignore
        """Генерируем ответ через Gemini API"""
        if not self.is_available():
            return AiResult(
                text="❌ **Gemini API недоступен!**\n\nПроверьте настройки API ключа.",
                tokens_used=0,
                cost=0.0,
                provider_name=self.name
            )

        try:
            # Формируем полный промпт с системным промптом
            full_prompt = prompt
            if self.system_prompt:
                full_prompt = f"{self.system_prompt}\n\nПользователь: {prompt}\n\nОтвет:"
            
            # Используем настройки из конфигурации
            actual_max_tokens = min(max_tokens, self.max_tokens)
            
            # Формируем payload для Gemini API (точно по официальной документации)
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_prompt
                            }
                        ]
                    }
                ]
            }

            # Добавляем логирование для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Отправляем запрос к Gemini: модель={self.model}, токены={actual_max_tokens}")

            # Отправляем запрос к Gemini API (точно по официальной документации Google)
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            # URL без ключа (ключ в заголовке)
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            response = requests.post(
                api_url, 
                json=payload, 
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Извлекаем текст ответа из Gemini API
                text = ""
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            text = parts[0]['text']
                
                if text:
                    tokens_used = len(prompt.split()) + len(text.split())
                    logger.info(f"Gemini ответил успешно: токены={tokens_used}, длина ответа={len(text)}")
                    
                    return AiResult(
                        text=text,
                        tokens_used=tokens_used,
                        cost=0.0,  # Gemini бесплатный в рамках лимитов!
                        provider_name=self.name
                    )
                else:
                    logger.error(f"Gemini вернул пустой ответ: {data}")
                    return AiResult(
                        text="❌ **Ошибка Gemini API: пустой ответ**\n\nПопробуйте переформулировать вопрос.",
                        tokens_used=0,
                        cost=0.0,
                        provider_name=self.name
                    )
            else:
                logger.error(f"Gemini API вернул ошибку: {response.status_code}, ответ: {response.text}")
                return AiResult(
                    text=f"❌ **Ошибка Gemini API: {response.status_code}**\n\nПопробуйте позже.",
                    tokens_used=0,
                    cost=0.0,
                    provider_name=self.name
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка Gemini: {str(e)}")
            return AiResult(
                text=f"❌ **Ошибка сети Gemini:** {str(e)}\n\nПроверьте подключение к интернету.",
                tokens_used=0,
                cost=0.0,
                provider_name=self.name
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка Gemini: {str(e)}")
            return AiResult(
                text=f"❌ **Неожиданная ошибка Gemini:** {str(e)}\n\nПопробуйте позже.",
                tokens_used=0,
                cost=0.0,
                provider_name=self.name
            )

class FallbackProvider(BaseProvider):
    """Fallback провайдер для локального тестирования"""
    
    def __init__(self, task_type=None):
        super().__init__()
        self.name = "fallback"
        self.provider_type = "local"
        self.is_available = lambda: True
        self.task_type = task_type or 'chat'
    
    def generate_response(self, prompt, **kwargs):
        """Генерирует ответ на основе локальных данных"""
        try:
            # Простые ответы для тестирования
            if "математика" in prompt.lower() or "егэ" in prompt.lower() or "свеж" in prompt.lower():
                return {
                    'text': '📐 **Свежее задание по математике ЕГЭ**\n\n**Задача:** Найдите все значения параметра a, при которых уравнение x² + (a-2)x + a = 0 имеет ровно один корень.\n\n**Решение:**\n1) Уравнение имеет ровно один корень, когда дискриминант равен нулю\n2) D = (a-2)² - 4·1·a = a² - 4a + 4 - 4a = a² - 8a + 4\n3) D = 0: a² - 8a + 4 = 0\n4) Решаем: a = (8 ± √(64-16))/2 = (8 ± √48)/2 = (8 ± 4√3)/2 = 4 ± 2√3\n\n**Ответ:** a = 4 + 2√3 или a = 4 - 2√3',
                    'tokens_used': 200,
                    'cost': 0.0
                }
            elif "физика" in prompt.lower():
                return {
                    'text': '⚡ **Задание по физике ЕГЭ**\n\n**Задача:** Тело движется равноускоренно с начальной скоростью 2 м/с и ускорением 3 м/с². Какой путь пройдет тело за 4 секунды?\n\n**Решение:**\nS = v₀t + at²/2 = 2×4 + 3×16/2 = 8 + 24 = 32 м\n\n**Ответ:** 32 метра',
                    'tokens_used': 120,
                    'cost': 0.0
                }
            elif "свеж" in prompt.lower() or "последн" in prompt.lower():
                return {
                    'text': '🎯 **Самая свежая задача по математике ЕГЭ**\n\n**Задача:** В треугольнике ABC проведена медиана AM. Известно, что AB = 6, AC = 8, а угол BAC = 60°. Найдите длину медианы AM.\n\n**Решение:**\n1) По формуле медианы: AM² = (2AB² + 2AC² - BC²)/4\n2) Найдем BC по теореме косинусов: BC² = AB² + AC² - 2·AB·AC·cos(60°)\n3) BC² = 36 + 64 - 2·6·8·0.5 = 100 - 48 = 52\n4) AM² = (2·36 + 2·64 - 52)/4 = (72 + 128 - 52)/4 = 148/4 = 37\n5) AM = √37\n\n**Ответ:** AM = √37',
                    'tokens_used': 250,
                    'cost': 0.0
                }
            else:
                return {
                    'text': '🤖 **Локальный помощник ExamFlow**\n\nСейчас я работаю в локальном режиме. Вот что я могу:\n\n📚 Помочь с заданиями ЕГЭ/ОГЭ\n📝 Объяснить решения\n🎯 Дать подсказки\n\nПопробуйте спросить о конкретном предмете или задаче!',
                    'tokens_used': 100,
                    'cost': 0.0
                }
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка fallback провайдера: {e}")
            return {
                'text': '❌ **Ошибка локального помощника**\n\nПопробуйте переформулировать вопрос.',
                'tokens_used': 50,
                'cost': 0.0
            }


class AiService:
    """Сервис управления провайдерами, лимитами и кэшем ответов."""

    def __init__(self) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Инициализация AiService...")
        
        self.providers: list[BaseProvider] = self._load_providers()
        logger.info("AiService инициализирован успешно")

    def _load_providers(self) -> list[BaseProvider]:
        # Используем только Google Gemini AI
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Загружаем провайдеры ИИ...")
        
        ordered: list[BaseProvider] = []
        
        # Пытаемся использовать Gemini
        gemini_provider = GeminiProvider()
        if gemini_provider.is_available():
            ordered.append(gemini_provider)
            logger.info("Gemini провайдер доступен")
        else:
            logger.warning("Gemini провайдер недоступен!")
        
        # ВСЕГДА добавляем fallback провайдер для локального тестирования
        ordered.append(FallbackProvider())
        logger.info("Fallback провайдер доступен")
        
        logger.info(f"Загружено провайдеров: {len(ordered)}")
        return ordered
    
    def get_provider_for_task(self, task_type: str = 'chat') -> Optional[BaseProvider]:
        """Получить провайдера для конкретного типа задачи"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Запрашиваем провайдера для задачи типа: {task_type}")
        
        # Используем только Gemini
        provider = GeminiProvider(task_type=task_type)
        if provider.is_available():
            logger.info(f"Провайдер {provider.name} доступен для задачи {task_type}")
            return provider
        
        logger.warning(f"Gemini провайдер недоступен для задачи {task_type}")
        return None

    def ask_with_rag(self, prompt: str, user=None, task=None, task_type: str = 'chat', 
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        Задает вопрос с использованием RAG системы для контекста
        
        Args:
            prompt: Вопрос пользователя
            user: Пользователь
            task: Задание (если есть)
            task_type: Тип задачи
            use_cache: Использовать кэш
            
        Returns:
            Ответ с контекстом
        """
        try:
            # Если есть задание, используем RAG для персонализации
            if task and user:
                personalized_prompt = rag_service.generate_personalized_prompt(
                    user, task, task_type
                )
                
                # Добавляем оригинальный вопрос пользователя
                full_prompt = f"{personalized_prompt}\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {prompt}"
                
                # Получаем ответ от AI
                result = self._ask_ai(full_prompt, user, task_type, use_cache)
                
                # Добавляем RAG контекст
                similar_tasks = rag_service.find_similar_tasks(task, limit=3)
                recommendations = rag_service.get_learning_recommendations(user, task.subject)
                
                result['rag_context'] = {
                    'similar_tasks': [
                        {
                            'id': t.id, # type: ignore
                            'title': t.title,
                            'difficulty': t.difficulty,
                            'topics': [topic.name for topic in t.topics.all()] # type: ignore
                        } for t in similar_tasks
                    ],
                    'recommendations': recommendations
                }
                
                return result
            else:
                # Обычный вопрос без RAG
                return self.ask(prompt, user, use_cache=use_cache)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка в RAG запросе: {e}")
            return self.ask(prompt, user, use_cache=use_cache)

    def get_personalized_learning_plan(self, user, subject=None) -> Dict[str, Any]:
        """
        Получает персональный план обучения
        
        Args:
            user: Пользователь
            subject: Предмет
            
        Returns:
            План обучения
        """
        try:
            if not user or not user.is_authenticated:
                return {'error': 'Пользователь не авторизован'}
            
            # Анализируем прогресс
            progress = rag_service.analyze_student_progress(user, subject)
            
            # Получаем рекомендации
            recommendations = rag_service.get_learning_recommendations(user, subject)
            
            # Формируем план обучения
            learning_plan = {
                'current_level': progress.get('recommended_difficulty', 1),
                'accuracy': progress.get('accuracy', 0),
                'weak_topics': progress.get('weak_topics', []),
                'strong_topics': progress.get('strong_topics', []),
                'recommendations': recommendations,
                'daily_goal': 3,  # Цель: 3 задания в день
                'weekly_goal': 15,  # Цель: 15 заданий в неделю
                'next_steps': []
            }
            
            # Определяем следующие шаги
            if progress.get('weak_topics'):
                learning_plan['next_steps'].append({
                    'action': 'review_weak_topics',
                    'description': f'Повторить слабые темы: {", ".join(progress["weak_topics"][:3])}',
                    'priority': 'high'
                })
            
            if progress.get('accuracy', 0) < 70:
                learning_plan['next_steps'].append({
                    'action': 'practice_basics',
                    'description': 'Повторить базовые темы для улучшения точности',
                    'priority': 'high'
                })
            
            if progress.get('recommended_difficulty', 1) < 5:
                learning_plan['next_steps'].append({
                    'action': 'increase_difficulty',
                    'description': f'Попробовать задания сложности {progress["recommended_difficulty"]}',
                    'priority': 'medium'
                })
            
            return learning_plan
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при получении плана обучения: {e}")
            return {'error': 'Не удалось создать план обучения'}

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _get_cache(self, prompt: str) -> Optional[AiResponse]:
        ph = self._hash_prompt(prompt)
        return AiResponse.objects.filter(prompt_hash=ph).first()  # type: ignore

    def _set_cache(self, prompt: str, result: AiResult, provider: Optional[AiProvider] = None) -> AiResponse:
        ph = self._hash_prompt(prompt)
        ai_provider = provider if provider else AiProvider.objects.filter(is_active=True).order_by("priority").first()  # type: ignore
        if not ai_provider:
            # создаём запись провайдера локально, если нет ни одного
            ai_provider = AiProvider.objects.create(name="Local", provider_type="fallback", is_active=True, priority=100)  # type: ignore
        return AiResponse.objects.create(  # type: ignore
            prompt_hash=ph,
            prompt=prompt,
            response=result.text,
            tokens_used=result.tokens_used,
            provider=ai_provider,
        )

    def _get_or_create_limits(self, user, session_id: Optional[str]) -> AiLimit:
        # Без регистрации: 10/день; с регистрацией: 30/день
        is_auth = bool(user and getattr(user, "is_authenticated", False))
        max_daily = 30 if is_auth else 10
        limit, _ = AiLimit.objects.get_or_create(  # type: ignore
            user=user if is_auth else None,
            session_id=None if is_auth else (session_id or "guest"),
            limit_type="daily",
            defaults={
                "current_usage": 0,
                "max_limit": max_daily,
                "reset_date": timezone.now(),
            },
        )
        # Автосброс, если пора
        if timezone.now() >= limit.reset_date:
            limit.current_usage = 0
            limit.reset_date = timezone.now() + timezone.timedelta(days=1)
            limit.max_limit = max_daily
            limit.save()  # type: ignore
        return limit

    def _ask_ai(self, prompt: str, user=None, task_type: str = 'chat', use_cache: bool = True) -> Dict[str, Any]:
        """
        Внутренний метод для запроса к AI
        
        Args:
            prompt: Промпт
            user: Пользователь
            task_type: Тип задачи
            use_cache: Использовать кэш
            
        Returns:
            Ответ от AI
        """
        try:
            # Выбираем провайдера для конкретного типа задачи
            provider = self.get_provider_for_task(task_type)
            if not provider:
                return {"error": "Нет доступных ИИ провайдеров для этого типа задачи."}
            
            # Генерируем ответ
            result = provider.generate(prompt)
            
            return {
                "response": result.text,
                "provider": result.provider_name,
                "tokens_used": result.tokens_used,
                "task_type": task_type
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка в _ask_ai: {e}")
            return {"error": f"Ошибка при обращении к AI: {str(e)}"}

    def ask(self, prompt: str, user=None, session_id: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Главный метод: проверяет лимиты, кэш, выбирает провайдера и возвращает ответ."""
        prompt = (prompt or "").strip()
        if not prompt:
            return {"error": "Пустой запрос"}

        # Добавляем логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Получен запрос к ИИ: пользователь={user}, сессия={session_id}, промпт={prompt[:50]}...")

        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
            logger.warning(f"Лимит исчерпан для пользователя={user}, сессии={session_id}")
            return {"error": "Лимит запросов на сегодня исчерпан. Попробуйте завтра."}

        # Кэш ответа - ВРЕМЕННО ОТКЛЮЧЕН
        # if use_cache:
        #     cached = self._get_cache(prompt)
        #     if cached:
        #         cached.increment_usage()
        #         AiRequest.objects.create(  # type: ignore
        #             user=user, session_id=session_id, request_type="question", prompt=prompt,
        #             response=cached.response, tokens_used=cached.tokens_used, cost=0, ip_address=None
        #         )
        #         limit.current_usage += 1  # type: ignore
        #         limit.save()  # type: ignore
        #         return {"response": cached.response, "provider": cached.provider.name if cached.provider else "local", "cached": True, "tokens_used": cached.tokens_used}

        # Выбор провайдера: используем локальный список в порядке приоритета
        provider_client = None
        
        # Проходим по провайдерам в порядке приоритета
        for provider in self.providers:
            if provider.is_available():
                provider_client = provider
                logger.info(f"Выбран провайдер: {provider.name}")
                break
        
        # Если ни один не доступен, используем fallback
        if not provider_client:
            logger.warning("Основные провайдеры недоступны, используем fallback")
            # Ищем fallback провайдер
            for provider in self.providers:
                if isinstance(provider, FallbackProvider):
                    provider_client = provider
                    logger.info(f"Используем fallback провайдер: {provider.name}")
                    break
        
        # Если и fallback недоступен, возвращаем ошибку
        if not provider_client:
            logger.error("Нет доступных ИИ провайдеров")
            return {"error": "Нет доступных ИИ провайдеров. Проверьте настройки API."}

        # Генерация ответа
        logger.info(f"Начинаем генерацию ответа через {provider_client.name}")
        result = provider_client.generate(prompt)
        logger.info(f"Ответ сгенерирован: токены={result.tokens_used}, провайдер={result.provider_name}")

        # Логирование и сохранение
        AiRequest.objects.create(  # type: ignore
            user=user,
            session_id=session_id,
            request_type="question",
            prompt=prompt,
            response=result.text,
            tokens_used=result.tokens_used,
            cost=result.cost,
            ip_address=None,
        )

        # Обновляем лимит
        limit.current_usage += 1  # type: ignore
        limit.save()  # type: ignore

        # Сохраняем кэш - ВРЕМЕННО ОТКЛЮЧЕНО
        # self._set_cache(prompt, result, None)

        logger.info(f"Запрос к ИИ завершен успешно: пользователь={user}, сессия={session_id}")
        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
    
    def chat(self, message: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Обычный чат с ИИ-ассистентом"""
        return self.ask(message, user, session_id)
    
    def explain_task(self, task_text: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Объяснение решения задачи"""
        prompt = f"Объясни подробно, как решить эту задачу:\n\n{task_text}"
        
        # Добавляем логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Запрос на объяснение задачи: пользователь={user}, сессия={session_id}")
        
        # Используем специальный провайдер для объяснения задач
        provider = self.get_provider_for_task('task_explanation')
        if not provider:
            logger.error("Нет доступных провайдеров для объяснения задач")
            return {"error": "Нет доступных ИИ провайдеров для объяснения задач."}
        
        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
            logger.warning(f"Лимит исчерпан для объяснения задачи: пользователь={user}, сессия={session_id}")
            return {"error": "Лимит запросов на сегодня исчерпан. Попробуйте завтра."}
        
        # Генерируем ответ
        logger.info(f"Начинаем генерацию объяснения задачи через {provider.name}")
        result = provider.generate(prompt)
        logger.info(f"Объяснение задачи сгенерировано: токены={result.tokens_used}, провайдер={result.provider_name}")
        
        # Логируем
        AiRequest.objects.create(  # type: ignore
            user=user, session_id=session_id, request_type="task_explanation", 
            prompt=prompt, response=result.text, tokens_used=result.tokens_used, 
            cost=result.cost, ip_address=None
        )
        
        # Обновляем лимит
        limit.current_usage += 1  # type: ignore
        limit.save()  # type: ignore
        
        logger.info(f"Объяснение задачи завершено успешно: пользователь={user}, сессия={session_id}")
        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
    
    def get_hint(self, task_text: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Получение подсказки для решения задачи"""
        prompt = f"Дай краткую подсказку (не полное решение!) для этой задачи:\n\n{task_text}"
        
        # Добавляем логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Запрос на подсказку: пользователь={user}, сессия={session_id}")
        
        # Используем специальный провайдер для подсказок
        provider = self.get_provider_for_task('hint_generation')
        if not provider:
            logger.error("Нет доступных провайдеров для генерации подсказок")
            return {"error": "Нет доступных ИИ провайдеров для генерации подсказок."}
        
        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
            logger.warning(f"Лимит исчерпан для подсказки: пользователь={user}, сессия={session_id}")
            return {"error": "Лимит запросов на сегодня исчерпан. Попробуйте завтра."}
        
        # Генерируем ответ
        logger.info(f"Начинаем генерацию подсказки через {provider.name}")
        result = provider.generate(prompt, max_tokens=300)  # Краткие подсказки
        logger.info(f"Подсказка сгенерирована: токены={result.tokens_used}, провайдер={result.provider_name}")
        
        # Логируем
        AiRequest.objects.create(  # type: ignore
            user=user, session_id=session_id, request_type="hint_generation", 
            prompt=prompt, response=result.text, tokens_used=result.tokens_used, 
            cost=result.cost, ip_address=None
        )
        
        # Обновляем лимит
        limit.current_usage += 1  # type: ignore
        limit.save()  # type: ignore
        
        logger.info(f"Генерация подсказки завершена успешно: пользователь={user}, сессия={session_id}")
        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
