from __future__ import annotations

import os

import pytest

from core.container import Container

pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY не задан — интеграционный тест пропущен",
)


def test_gemini_integration_real_api():
    orchestrator = Container.ai_orchestrator()
    result = orchestrator.process_query("Кратко объясни, что такое производная")  # type: ignore
    assert isinstance(result, dict)
    assert "answer" in result
    assert len(result.get("answer", "")) > 0
