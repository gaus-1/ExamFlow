"""
🤖 Оптимизированный сервис для Telegram бота

Единый сервис для всех операций бота:
- Обработка команд
- Генерация клавиатур
- Форматирование сообщений
- Интеграция с AI
- Геймификация
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from learning.models import Subject, Task, UserProgress
from core.models import UnifiedProfile
from core.services.unified_profile import UnifiedProfileService
from core.services.chat_session import ChatSessionService
from ai.optimized_service import ai_service
from .gamification import TelegramGamification

logger = logging.getLogger(__name__)

class OptimizedBotService:
    """Оптимизированный сервис для Telegram бота"""
    
    def __init__(self):
        self.ai_service = ai_service
        self.gamification = TelegramGamification()
        self.logger = logging.getLogger(__name__)
    
    # ===== ОСНОВНЫЕ КОМАНДЫ =====
    
    async def get_start_message(self, user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """Получает приветственное сообщение"""
        try:
            # Получаем профиль пользователя
            profile = await self._get_user_profile(user_id)
            
            # Формируем персонализированное приветствие
            if profile and profile.get('level', 1) > 1:
                message = f"""🎉 Добро пожаловать обратно, {profile.get('name', 'ученик')}!

📊 Ваш уровень: {profile.get('level', 1)}
🏆 Очков: {profile.get('points', 0)}
📚 Решено заданий: {profile.get('solved_tasks', 0)}

Что будем изучать сегодня?"""
            else:
                message = """🎓 Добро пожаловать в ExamFlow!

Я помогу тебе подготовиться к ЕГЭ и ОГЭ:
📚 Решение заданий
🤖 ИИ-помощник
📊 Отслеживание прогресса
🏆 Геймификация

Выбери предмет для начала:"""
            
            keyboard = self._get_main_menu_keyboard()
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения приветствия: {e}")
            return "Добро пожаловать в ExamFlow! Выбери действие:", self._get_main_menu_keyboard()
    
    async def get_subjects_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Получает меню предметов"""
        try:
            subjects = await self._get_subjects()
            
            message = "📚 Выбери предмет для изучения:"
            keyboard = self._get_subjects_keyboard(subjects)
            
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения предметов: {e}")
            return "❌ Ошибка загрузки предметов", self._get_main_menu_keyboard()
    
    async def get_subject_topics(self, subject_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """Получает темы предмета"""
        try:
            subject = await self._get_subject(subject_id)
            if not subject:
                return "❌ Предмет не найден", self._get_subjects_keyboard([])
            
            message = f"📖 {subject['name']} - {subject['exam_type']}\n\nВыбери тему:"
            keyboard = self._get_topics_keyboard(subject_id, subject.get('topics', []))
            
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения тем: {e}")
            return "❌ Ошибка загрузки тем", self._get_subjects_keyboard([])
    
    async def get_random_task(self, subject_id: int = None) -> Tuple[str, InlineKeyboardMarkup]: # type: ignore
        """Получает случайное задание"""
        try:
            task = await self._get_random_task(subject_id)
            if not task:
                return "❌ Задания не найдены", self._get_main_menu_keyboard()
            
            message = f"""📝 **{task['title']}**

{task['text'][:500]}{'...' if len(task['text']) > 500 else ''}

**Сложность:** {task['difficulty']}/5
**Предмет:** {task['subject']}"""
            
            keyboard = self._get_task_keyboard(task['id'])
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения задания: {e}")
            return "❌ Ошибка загрузки задания", self._get_main_menu_keyboard()
    
    async def get_ai_response(self, 
                            prompt: str, 
                            user_id: int,
                            task_id: int = None) -> Tuple[str, InlineKeyboardMarkup]: # type: ignore
        """Получает ответ от AI"""
        try:
            # Получаем пользователя
            user = await self._get_django_user(user_id)
            
            # Получаем ответ от AI
            if task_id:
                task = await self._get_task(task_id)
                result = self.ai_service.get_personalized_help( # type: ignore
                    task['text'], user, user_level=3 # type: ignore
                )
            else:
                result = self.ai_service.ask(prompt, user, use_rag=True) # type: ignore
            
            if 'error' in result:
                message = f"❌ {result['error']}"
            else:
                message = f"🤖 **AI Ответ:**\n\n{result['response']}"
            
            keyboard = self._get_ai_keyboard()
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения AI ответа: {e}")
            return "❌ Ошибка AI сервиса", self._get_main_menu_keyboard()
    
    async def get_user_stats(self, user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """Получает статистику пользователя"""
        try:
            profile = await self._get_user_profile(user_id)
            if not profile:
                return "❌ Профиль не найден", self._get_main_menu_keyboard()
            
            message = f"""📊 **Твоя статистика:**

🎯 **Уровень:** {profile.get('level', 1)}
🏆 **Очки:** {profile.get('points', 0)}
📚 **Решено заданий:** {profile.get('solved_tasks', 0)}
🎖️ **Достижений:** {profile.get('achievements', 0)}
🔥 **Серия побед:** {profile.get('streak', 0)}

**Прогресс до следующего уровня:**
{self._get_progress_bar(profile.get('xp', 0), profile.get('next_level_xp', 100))}"""
            
            keyboard = self._get_stats_keyboard()
            return message, keyboard
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return "❌ Ошибка загрузки статистики", self._get_main_menu_keyboard()
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
    async def _get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает профиль пользователя"""
        try:
            profile = await sync_to_async(UnifiedProfileService.get_or_create_profile)(
                user_id, 'telegram' # type: ignore
            )
            return profile
        except Exception as e:
            self.logger.error(f"Ошибка получения профиля: {e}")
            return None
    
    async def _get_django_user(self, user_id: int) -> Optional[User]:
        """Получает Django пользователя"""
        try:
            user_tuple = await sync_to_async(User.objects.get_or_create)(
                username=f"tg_{user_id}",
                defaults={'first_name': f'User {user_id}'}
            )
            return user_tuple[0]  # type: ignore
        except Exception as e:
            self.logger.error(f"Ошибка получения Django пользователя: {e}")
            return None
    async def _get_subjects(self) -> List[Dict[str, Any]]:
        """Получает список предметов"""
        try:
            subjects = await sync_to_async(list)(
                Subject.objects.all().values('id', 'name', 'exam_type') # type: ignore
            )
            return list(subjects)
        except Exception as e:
            self.logger.error(f"Ошибка получения предметов: {e}")
            return []
    
    async def _get_subject(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """Получает предмет по ID"""
        try:
            subject = await sync_to_async(Subject.objects.get)(id=subject_id) # type: ignore
            return {
                'id': subject.id,
                'name': subject.name,
                'exam_type': subject.exam_type,
                'topics': []  # Можно добавить загрузку тем
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения предмета: {e}")
            return None
    
    async def _get_random_task(self, subject_id: int = None) -> Optional[Dict[str, Any]]: # type: ignore
        """Получает случайное задание"""
        try:
            from django.db.models import Q
            from random import choice
            
            query = Task.objects.all() # type: ignore
            if subject_id:
                query = query.filter(subject_id=subject_id)
            
            tasks = await sync_to_async(list)(query.values('id', 'title', 'text', 'difficulty', 'subject__name')) # type: ignore
            
            if tasks:
                task = choice(tasks)
                return {
                    'id': task['id'],
                    'title': task['title'],
                    'text': task['text'],
                    'difficulty': task['difficulty'],
                    'subject': task['subject__name']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения задания: {e}")
            return None
    
    async def _get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получает задание по ID"""
        try:
            task = await sync_to_async(Task.objects.get)(id=task_id) # type: ignore
            return {
                'id': task.id,
                'title': task.title,
                'text': task.text,
                'difficulty': task.difficulty,
                'subject': task.subject.name
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения задания: {e}")
            return None
    
    # ===== КЛАВИАТУРЫ =====
    
    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = [
            [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
            [InlineKeyboardButton("🎲 Случайное задание", callback_data="random_task")],
            [InlineKeyboardButton("🤖 AI Помощник", callback_data="ai_help")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_subjects_keyboard(self, subjects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Клавиатура предметов"""
        keyboard = []
        for subject in subjects[:6]:  # Максимум 6 предметов
            keyboard.append([
                InlineKeyboardButton(
                    f"{subject['name']} ({subject['exam_type']})",
                    callback_data=f"subject_{subject['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    def _get_topics_keyboard(self, subject_id: int, topics: List[str]) -> InlineKeyboardMarkup:
        """Клавиатура тем"""
        keyboard = []
        for i, topic in enumerate(topics[:5]):  # Максимум 5 тем
            keyboard.append([
                InlineKeyboardButton(
                    topic,
                    callback_data=f"topic_{subject_id}_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="subjects")])
        return InlineKeyboardMarkup(keyboard)
    
    def _get_task_keyboard(self, task_id: int) -> InlineKeyboardMarkup:
        """Клавиатура задания"""
        keyboard = [
            [InlineKeyboardButton("🤖 Объяснить", callback_data=f"explain_{task_id}")],
            [InlineKeyboardButton("💡 Подсказка", callback_data=f"hint_{task_id}")],
            [InlineKeyboardButton("✅ Решено", callback_data=f"solved_{task_id}")],
            [InlineKeyboardButton("🎲 Другое задание", callback_data="random_task")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_ai_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура AI"""
        keyboard = [
            [InlineKeyboardButton("🔄 Новый вопрос", callback_data="ai_help")],
            [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_stats_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура статистики"""
        keyboard = [
            [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
            [InlineKeyboardButton("📈 Прогресс", callback_data="progress")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        """Получает прогресс-бар"""
        if total == 0:
            return "█" * length
        
        filled = int((current / total) * length)
        bar = "█" * filled + "░" * (length - filled)
        percentage = int((current / total) * 100)
        
        return f"{bar} {percentage}%"

# Глобальный экземпляр сервиса
bot_service = OptimizedBotService()
