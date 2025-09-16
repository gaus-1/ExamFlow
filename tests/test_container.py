from __future__ import annotations

from core.container import Container
from core.notifications.telegram_notifier import TelegramNotifier


def test_ai_orchestrator_singleton() -> None:
    a = Container.ai_orchestrator()
    b = Container.ai_orchestrator()
    assert a is b


def test_notifier_singleton() -> None:
    a = Container.notifier()
    b = Container.notifier()
    assert isinstance(a, TelegramNotifier)
    assert a is b


def test_cache_default_available() -> None:
    cache = Container.cache()
    assert cache is not None

def test_container_provides_cache() -> None:
    cache = Container.cache()
    cache.set("k", 1, 1)
    assert cache.get("k") == 1


def test_container_provides_notifier() -> None:
    notifier = Container.notifier()
    assert notifier is not None


def test_container_provides_ai_orchestrator() -> None:
    orchestrator = Container.ai_orchestrator()
    assert hasattr(orchestrator, "process_query")

