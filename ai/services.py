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


class OllamaProvider(BaseProvider):
    """Провайдер Ollama - бесплатный локальный ИИ!"""

    name = "ollama"

    def __init__(self, model: str = None, task_type: str = 'chat') -> None:
        # Используем настройки из Django settings
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        self.api_url = f"{self.base_url}/api/generate"
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 30)
        
        # Выбираем модель и настройки для конкретного типа задачи
        task_configs = getattr(settings, 'OLLAMA_TASK_CONFIGS', {})
        task_config = task_configs.get(task_type, task_configs.get('chat', {}))
        
        self.model = model or task_config.get('model', getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama2:7b'))
        self.temperature = task_config.get('temperature', 0.7)
        self.max_tokens = task_config.get('max_tokens', 1000)
        self.system_prompt = task_config.get('system_prompt', '')

    def is_available(self) -> bool:
        """Проверяем доступность Ollama сервера"""
        try:
            if not requests:
                return False
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:
        """Генерируем ответ через Ollama API"""
        if not self.is_available():
            return AiResult(
                text=f"❌ **Ollama недоступен!**\n\nУбедитесь, что:\n1. Ollama установлен и запущен\n2. Сервер работает на {self.base_url}\n3. Модель {self.model} загружена\n\n**Команды для запуска:**\n```bash\nollama serve\nollama run {self.model}\n```",
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
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": actual_max_tokens,
                    "temperature": self.temperature
                }
            }

            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "")
                tokens_used = len(prompt.split()) + len(text.split())
                
                return AiResult(
                    text=text,
                    tokens_used=tokens_used,
                    cost=0.0,  # Ollama бесплатный!
                    provider_name=self.name
                )
            else:
                return AiResult(
                    text=f"❌ **Ошибка Ollama API: {response.status_code}**\n\nПопробуйте перезапустить Ollama сервер.",
                    tokens_used=0,
                    cost=0.0,
                    provider_name=self.name
                )
                
        except requests.exceptions.RequestException as e:
            return AiResult(
                text=f"❌ **Ошибка сети Ollama:** {str(e)}\n\nПроверьте, что Ollama сервер запущен.",
                tokens_used=0,
                cost=0.0,
                provider_name=self.name
            )
        except Exception as e:
            return AiResult(
                text=f"❌ **Неожиданная ошибка Ollama:** {str(e)}\n\nПопробуйте перезапустить сервер.",
                tokens_used=0,
                cost=0.0,
                provider_name=self.name
            )





# DeepSeekProvider удален - заменен на Ollama








class AiService:
    """Сервис управления провайдерами, лимитами и кэшем ответов."""

    def __init__(self) -> None:
        self.providers: list[BaseProvider] = self._load_providers()

    def _load_providers(self) -> list[BaseProvider]:
        # Только Ollama - бесплатный и мощный!
        ordered: list[BaseProvider] = [OllamaProvider()]
        return ordered
    
    def get_provider_for_task(self, task_type: str = 'chat') -> Optional[BaseProvider]:
        """Получить провайдера для конкретного типа задачи"""
        provider = OllamaProvider(task_type=task_type)
        if provider.is_available():
            return provider
        return None

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

    def ask(self, prompt: str, user=None, session_id: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Главный метод: проверяет лимиты, кэш, выбирает провайдера и возвращает ответ."""
        prompt = (prompt or "").strip()
        if not prompt:
            return {"error": "Пустой запрос"}

        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
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
                break
        
        # Если ни один не доступен, возвращаем ошибку
        if not provider_client:
            return {"error": "Нет доступных ИИ провайдеров. Проверьте настройки API."}

        # Генерация ответа
        result = provider_client.generate(prompt)

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

        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
    
    def chat(self, message: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Обычный чат с ИИ-ассистентом"""
        return self.ask(message, user, session_id)
    
    def explain_task(self, task_text: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Объяснение решения задачи"""
        prompt = f"Объясни подробно, как решить эту задачу:\n\n{task_text}"
        
        # Используем специальный провайдер для объяснения задач
        provider = self.get_provider_for_task('task_explanation')
        if not provider:
            return {"error": "Нет доступных ИИ провайдеров для объяснения задач."}
        
        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
            return {"error": "Лимит запросов на сегодня исчерпан. Попробуйте завтра."}
        
        # Генерируем ответ
        result = provider.generate(prompt)
        
        # Логируем
        AiRequest.objects.create(  # type: ignore
            user=user, session_id=session_id, request_type="task_explanation", 
            prompt=prompt, response=result.text, tokens_used=result.tokens_used, 
            cost=result.cost, ip_address=None
        )
        
        # Обновляем лимит
        limit.current_usage += 1  # type: ignore
        limit.save()  # type: ignore
        
        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
    
    def get_hint(self, task_text: str, user=None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Получение подсказки для решения задачи"""
        prompt = f"Дай краткую подсказку (не полное решение!) для этой задачи:\n\n{task_text}"
        
        # Используем специальный провайдер для подсказок
        provider = self.get_provider_for_task('hint_generation')
        if not provider:
            return {"error": "Нет доступных ИИ провайдеров для генерации подсказок."}
        
        # Проверяем лимиты
        limit = self._get_or_create_limits(user, session_id)
        if not limit.can_make_request():
            return {"error": "Лимит запросов на сегодня исчерпан. Попробуйте завтра."}
        
        # Генерируем ответ
        result = provider.generate(prompt, max_tokens=300)  # Краткие подсказки
        
        # Логируем
        AiRequest.objects.create(  # type: ignore
            user=user, session_id=session_id, request_type="hint_generation", 
            prompt=prompt, response=result.text, tokens_used=result.tokens_used, 
            cost=result.cost, ip_address=None
        )
        
        # Обновляем лимит
        limit.current_usage += 1  # type: ignore
        limit.save()  # type: ignore
        
        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
