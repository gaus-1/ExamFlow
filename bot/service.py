from typing import Dict, Optional
import asyncio

from core.rag_system.orchestrator import RAGOrchestrator


class BotService:
    def __init__(self) -> None:
        self._orchestrator = RAGOrchestrator()

    async def process_query(self, query: str, subject: str = "", document_type: str = "") -> Dict:
        return await asyncio.to_thread(self._orchestrator.process_query, query, subject, document_type)


