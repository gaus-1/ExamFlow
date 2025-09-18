"""
DeepSeek AI клиент для ExamFlow
Интеграция с DeepSeek API для получения ответов от AI
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    Клиент для работы с DeepSeek API
    Поддерживает chat completion и различные модели
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', '')
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"  # Основная модель DeepSeek
        self.max_tokens = 4000
        self.temperature = 0.7
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в настройках")
        
        logger.info("DeepSeek клиент инициализирован")
    
    def ask(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправляет запрос к DeepSeek API
        
        Args:
            prompt: Вопрос пользователя
            context: Дополнительный контекст (опционально)
        
        Returns:
            Dict с ответом, источниками и метаданными
        """
        try:
            start_time = time.time()
            
            # Подготавливаем сообщения
            messages = [
                {
                    "role": "system", 
                    "content": """Ты - ExamFlow AI, крутой помощник для подготовки к ЕГЭ и ОГЭ.

🎯 ТВОЯ РОЛЬ:
- Ты представляешься как "ExamFlow AI" или просто "ExamFlow"
- Ты ЭКСПЕРТ по МАТЕМАТИКЕ, ФИЗИКЕ, ХИМИИ и точным наукам
- Ты решаешь задачи БЫСТРО и ЧЕТКО, как калькулятор с душой
- Ты можешь пошутить по теме, но не отвлекаешься от дела

🧮 СПЕЦИАЛИЗАЦИЯ:
- Математика профильная: сложные уравнения, производные, интегралы
- Математика базовая: простые задачи, проценты, графики
- Геометрия: площади, объемы, теоремы

😄 СТИЛЬ С ЮМОРОМ:
- Отвечай БЫСТРО и КОНКРЕТНО (2-3 предложения)
- Иногда добавляй математические шутки или забавные аналогии
- Примеры юмора: "Как говорят математики...", "Эта формула проще пирога!", "x убегает, но мы его поймаем!"
- НО главное - РЕШЕНИЕ задачи, юмор только в дополнение

📐 ФОРМАТ ОТВЕТОВ:
- Пошаговое решение для задач
- Простая запись: x², √, ÷, ≠, ≤, ≥
- Всегда подпись "— ExamFlow AI"

Помни: ты не просто AI, ты - ExamFlow, персональный математический гений ученика! 🚀"""
                }
            ]
            
            # Добавляем контекст если есть
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Контекст: {context}"
                })
            
            # Добавляем основной вопрос
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Подготавливаем запрос
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Отправляем запрос
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем ответ
                answer = data.get('choices', [{}])[0].get('message', {}).get('content', 'Не удалось получить ответ')
                
                # Метаданные использования
                usage = data.get('usage', {})
                
                result = {
                    'answer': answer.strip(),
                    'sources': [{'title': 'DeepSeek AI', 'url': 'https://deepseek.com'}],
                    'processing_time': processing_time,
                    'provider': 'deepseek',
                    'model': self.model,
                    'usage': {
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
                }
                
                logger.info(f"DeepSeek ответ получен за {processing_time:.2f}с, токенов: {usage.get('total_tokens', 0)}")
                return result
                
            else:
                error_msg = f"DeepSeek API ошибка: HTTP {response.status_code}"
                logger.error(f"{error_msg}: {response.text}")
                
                return {
                    'answer': f'Ошибка DeepSeek API: {response.status_code}',
                    'sources': [],
                    'processing_time': processing_time,
                    'provider': 'deepseek',
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API timeout")
            return {
                'answer': 'DeepSeek API не отвечает (таймаут)',
                'sources': [],
                'processing_time': 30.0,
                'provider': 'deepseek',
                'error': 'timeout'
            }
            
        except Exception as e:
            logger.error(f"Ошибка DeepSeek клиента: {e}")
            return {
                'answer': f'Ошибка DeepSeek: {str(e)}',
                'sources': [],
                'processing_time': 0.0,
                'provider': 'deepseek',
                'error': str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Получает список доступных моделей DeepSeek"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model['id'] for model in data.get('data', [])]
                logger.info(f"Доступные модели DeepSeek: {models}")
                return models
            else:
                logger.error(f"Ошибка получения моделей: {response.status_code}")
                return [self.model]  # Возвращаем дефолтную модель
                
        except Exception as e:
            logger.error(f"Ошибка получения моделей DeepSeek: {e}")
            return [self.model]
    
    def test_connection(self) -> bool:
        """Тестирует подключение к DeepSeek API"""
        try:
            test_response = self.ask("Привет! Это тест подключения.")
            return 'error' not in test_response
        except Exception as e:
            logger.error(f"Тест подключения DeepSeek не прошел: {e}")
            return False
