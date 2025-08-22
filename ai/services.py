import os
import json
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass

from django.utils import timezone

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


class LocalSimpleProvider(BaseProvider):
    """Локальный бесплатный провайдер (правила/заглушка). Не требует интернета и денег."""

    name = "local-simple"

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:
        # Простейшая имитация рассуждения: перефразирование и структурирование
        prompt_clean = prompt.strip()
        if not prompt_clean:
            return AiResult(text="Пожалуйста, напишите ваш вопрос подробнее.")

        base_reply = (
            "Я понял запрос. Ниже краткий план ответа:\n"
            "1) Определим цель вопроса.\n"
            "2) Разложим на шаги решение.\n"
            "3) Дадим пример и проверку.\n\n"
        )
        text = f"{base_reply}Ваш запрос: {prompt_clean}\n\nПредварительный ответ: этот модуль в стадии разработки. " \
            f"Скоро здесь будет развёрнутая подсказка с примерами."
        return AiResult(text=text, tokens_used=len(prompt_clean.split()), cost=0.0, provider_name=self.name)


class DeepSeekProvider(BaseProvider):
    """DeepSeek Chat (при наличии ключа)."""

    name = "deepseek"

    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

    def is_available(self) -> bool:
        return bool(self.api_key and requests)

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=30)  # type: ignore
            resp.raise_for_status()
            data = resp.json()
            # Унифицированный разбор; формат может отличаться — оставляем гибко
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            usage = data.get("usage", {})
            tokens = int(usage.get("total_tokens", 0))
            return AiResult(text=text or "", tokens_used=tokens, cost=0.0, provider_name=self.name)
        except Exception:
            # При ошибке — даём мягкий откат на локальный провайдер
            fallback = LocalSimpleProvider()
            return fallback.generate(prompt, max_tokens)


class GigaChatProvider(BaseProvider):
    """GigaChat (при наличии ключа)."""

    name = "gigachat"

    def __init__(self) -> None:
        self.api_key = os.getenv("GIGACHAT_API_KEY", "")
        self.api_url = os.getenv("GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1/chat/completions")

    def is_available(self) -> bool:
        return bool(self.api_key and requests)

    def generate(self, prompt: str, max_tokens: int = 512) -> AiResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": os.getenv("GIGACHAT_MODEL", "GigaChat:latest"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=30)  # type: ignore
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            usage = data.get("usage", {})
            tokens = int(usage.get("total_tokens", 0))
            return AiResult(text=text or "", tokens_used=tokens, cost=0.0, provider_name=self.name)
        except Exception:
            fallback = LocalSimpleProvider()
            return fallback.generate(prompt, max_tokens)


class AiService:
    """Сервис управления провайдерами, лимитами и кэшем ответов."""

    def __init__(self) -> None:
        self.providers: list[BaseProvider] = self._load_providers()

    def _load_providers(self) -> list[BaseProvider]:
        # Порядок важен: сначала бесплатные локальные, затем внешние
        ordered: list[BaseProvider] = [LocalSimpleProvider(), DeepSeekProvider(), GigaChatProvider()]
        # Можно ещё учитывать приоритеты из БД AiProvider
        return ordered

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

        # Кэш ответа
        if use_cache:
            cached = self._get_cache(prompt)
            if cached:
                cached.increment_usage()
                AiRequest.objects.create(  # type: ignore
                    user=user, session_id=session_id, request_type="question", prompt=prompt,
                    response=cached.response, tokens_used=cached.tokens_used, cost=0, ip_address=None
                )
                limit.current_usage += 1  # type: ignore
                limit.save()  # type: ignore
                return {"response": cached.response, "provider": cached.provider.name, "cached": True, "tokens_used": cached.tokens_used}

        # Выбор провайдера: сначала БД активных, затем локально определённые
        provider_obj = AiProvider.objects.filter(is_active=True).order_by("priority").first()  # type: ignore
        provider_client: BaseProvider
        if provider_obj:
            # Мэпим тип на клиента
            mapping = {
                "deepseek": DeepSeekProvider,
                "gigachat": GigaChatProvider,
                "fallback": LocalSimpleProvider,
                "llama": LocalSimpleProvider,   # заглушки на локальные модели
                "falcon": LocalSimpleProvider,
            }
            provider_client = mapping.get(provider_obj.provider_type, LocalSimpleProvider)()
        else:
            # Если нет записей в БД — используем порядок по умолчанию
            provider_client = LocalSimpleProvider()

        # Если выбранный клиент недоступен — fallback
        if not provider_client.is_available():
            provider_client = LocalSimpleProvider()

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

        # Сохраняем кэш
        self._set_cache(prompt, result, provider_obj)

        return {"response": result.text, "provider": result.provider_name, "cached": False, "tokens_used": result.tokens_used}
