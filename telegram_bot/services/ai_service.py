"""
Сервис для работы с ИИ в Telegram боте
Применяет принцип Dependency Inversion Principle (DIP)
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Абстрактный класс для провайдеров ИИ"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Сгенерировать ответ ИИ"""
        pass


class ContainerAIProvider(AIProvider):
    """Провайдер ИИ через Container"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Сгенерировать ответ через Container"""
        try:
            from core.container import Container
            
            ai = Container.ai_orchestrator()
            kwargs = {'prompt': prompt}
            
            if context:
                if 'user_id' in context:
                    kwargs['user_id'] = context['user_id']
                if 'subject' in context:
                    kwargs['subject'] = context['subject']
            
            result = ai.ask(**kwargs)
            
            if isinstance(result, dict):
                return result
            return {'answer': str(result)}
            
        except Exception as e:
            self.logger.error(f"Ошибка Container AI: {e}")
            return {'answer': f'Ошибка ИИ: {str(e)}'}


class MockAIProvider(AIProvider):
    """Мок-провайдер для тестирования"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Мок-ответ для тестирования"""
        return {
            'answer': f'Мок-ответ на вопрос: {prompt}',
            'sources': ['Тестовый источник'],
            'confidence': 0.95
        }


class AIService:
    """Сервис для работы с ИИ"""
    
    def __init__(self, provider: AIProvider = None):
        self.provider = provider or ContainerAIProvider()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def process_question(self, question: str, user_id: int = None, 
                             subject: str = None) -> Dict[str, Any]:
        """Обработать вопрос пользователя"""
        try:
            context = {}
            if user_id:
                context['user_id'] = user_id
            if subject:
                context['subject'] = subject
            
            response = await self.provider.generate_response(question, context)
            
            # Форматируем ответ для Telegram
            formatted_response = self._format_response(response)
            
            return {
                'success': True,
                'response': formatted_response,
                'raw_response': response
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки вопроса: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'Извините, произошла ошибка при обработке вашего вопроса.'
            }
    
    def _format_response(self, response: Dict[str, Any]) -> str:
        """Форматировать ответ для отображения в Telegram"""
        if not isinstance(response, dict):
            return str(response)
        
        answer = response.get('answer', 'Нет ответа')
        
        # Добавляем источники если есть
        sources = response.get('sources', [])
        if sources:
            answer += "\n\n📚 Источники:"
            for source in sources[:3]:  # Показываем максимум 3 источника
                answer += f"\n• {source}"
        
        # Ограничиваем длину ответа для Telegram
        if len(answer) > 4000:
            answer = answer[:3900] + "\n\n... (ответ обрезан)"
        
        return answer
    
    async def explain_task(self, task_text: str, user_answer: str = None) -> Dict[str, Any]:
        """Объяснить решение задачи"""
        prompt = f"Объясни решение задачи: {task_text}"
        
        if user_answer:
            prompt += f"\n\nОтвет пользователя: {user_answer}"
            prompt += "\n\nЕсли ответ неправильный, объясни правильное решение."
        
        return await self.process_question(prompt)
    
    async def get_hint(self, task_text: str) -> Dict[str, Any]:
        """Получить подсказку для задачи"""
        prompt = f"Дай подсказку для решения задачи (не давай полное решение): {task_text}"
        return await self.process_question(prompt)
