#!/usr/bin/env python
"""
Скрипт для тестирования функциональности Telegram бота
Проверяет все основные кнопки и их ответы
"""

import os
import sys
import django
import asyncio
from unittest.mock import Mock, AsyncMock

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram_bot.bot_handlers import (
    start, subjects_menu, show_stats, ai_help_handler,
    show_subject_topics, random_task, handle_ai_message
)
from telegram import Update, User, Message, CallbackQuery, Chat
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async


class BotTester:
    """Класс для тестирования функциональности бота"""
    
    def __init__(self):
        self.test_user_id = 123456789
        self.test_results = []
    
    def create_mock_update(self, message_text=None, callback_data=None):
        """Создает мок Update объект"""
        update = Mock(spec=Update)
        
        # Мок пользователя
        user = Mock(spec=User)
        user.id = self.test_user_id
        user.first_name = "Test"
        user.last_name = "User"
        user.username = "testuser"
        
        update.effective_user = user
        
        if message_text:
            # Мок сообщения
            message = AsyncMock(spec=Message)
            message.text = message_text
            update.message = message
            update.callback_query = None
        elif callback_data:
            # Мок callback query
            callback_query = AsyncMock(spec=CallbackQuery)
            callback_query.data = callback_data
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            update.callback_query = callback_query
            update.message = None
        
        # Мок чата
        chat = Mock(spec=Chat)
        chat.id = self.test_user_id
        update.effective_chat = chat
        
        return update
    
    def create_mock_context(self):
        """Создает мок Context объект"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = AsyncMock()
        context.bot.send_message = AsyncMock()
        return context
    
    async def test_start_command(self):
        """Тестирует команду /start"""
        print("🧪 Тестирую команду /start...")
        
        update = self.create_mock_update(message_text="/start")
        context = self.create_mock_context()
        
        try:
            await start(update, context)
            print("✅ Команда /start работает")
            self.test_results.append(("start", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в /start: {e}")
            self.test_results.append(("start", False, str(e)))
    
    async def test_subjects_button(self):
        """Тестирует кнопку 'Предметы'"""
        print("🧪 Тестирую кнопку 'Предметы'...")
        
        update = self.create_mock_update(callback_data="subjects")
        context = self.create_mock_context()
        
        try:
            await subjects_menu(update, context)
            print("✅ Кнопка 'Предметы' работает")
            self.test_results.append(("subjects", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в кнопке 'Предметы': {e}")
            self.test_results.append(("subjects", False, str(e)))
    
    async def test_stats_button(self):
        """Тестирует кнопку 'Прогресс'"""
        print("🧪 Тестирую кнопку 'Прогресс'...")
        
        update = self.create_mock_update(callback_data="stats")
        context = self.create_mock_context()
        
        try:
            await show_stats(update, context)
            print("✅ Кнопка 'Прогресс' работает")
            self.test_results.append(("stats", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в кнопке 'Прогресс': {e}")
            self.test_results.append(("stats", False, str(e)))
    
    async def test_ai_button(self):
        """Тестирует кнопку 'Спросить ИИ'"""
        print("🧪 Тестирую кнопку 'Спросить ИИ'...")
        
        update = self.create_mock_update(callback_data="ai_chat")
        context = self.create_mock_context()
        
        try:
            await ai_help_handler(update, context)
            print("✅ Кнопка 'Спросить ИИ' работает")
            self.test_results.append(("ai_chat", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в кнопке 'Спросить ИИ': {e}")
            self.test_results.append(("ai_chat", False, str(e)))
    
    async def test_subject_selection(self):
        """Тестирует выбор предмета"""
        print("🧪 Тестирую выбор предмета...")
        
        # Берем первый предмет
        from learning.models import Subject
        subject = await sync_to_async(Subject.objects.filter(is_archived=False).first)()  # type: ignore
        if not subject:
            print("❌ Нет доступных предметов")
            self.test_results.append(("subject_selection", False, "No subjects"))
            return
        
        update = self.create_mock_update(callback_data=f"subject_{subject.id}")
        context = self.create_mock_context()
        
        try:
            await show_subject_topics(update, context)
            print(f"✅ Выбор предмета '{subject.name}' работает")
            self.test_results.append(("subject_selection", True, f"Subject: {subject.name}"))
        except Exception as e:
            print(f"❌ Ошибка при выборе предмета: {e}")
            self.test_results.append(("subject_selection", False, str(e)))
    
    async def test_random_task(self):
        """Тестирует случайное задание"""
        print("🧪 Тестирую случайное задание...")
        
        update = self.create_mock_update(callback_data="random_task")
        context = self.create_mock_context()
        
        try:
            await random_task(update, context)
            print("✅ Случайное задание работает")
            self.test_results.append(("random_task", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в случайном задании: {e}")
            self.test_results.append(("random_task", False, str(e)))
    
    async def test_ai_message(self):
        """Тестирует прямое сообщение ИИ"""
        print("🧪 Тестирую прямое сообщение ИИ...")
        
        update = self.create_mock_update(message_text="Как решать квадратные уравнения?")
        context = self.create_mock_context()
        
        try:
            await handle_ai_message(update, context)
            print("✅ Прямое сообщение ИИ работает")
            self.test_results.append(("ai_message", True, "OK"))
        except Exception as e:
            print(f"❌ Ошибка в прямом сообщении ИИ: {e}")
            self.test_results.append(("ai_message", False, str(e)))
    
    async def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 Запуск тестирования функциональности бота...\n")
        
        await self.test_start_command()
        await self.test_subjects_button()
        await self.test_stats_button()
        await self.test_ai_button()
        await self.test_subject_selection()
        await self.test_random_task()
        await self.test_ai_message()
        
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, message in self.test_results:
            status = "✅ ПРОШЁЛ" if success else "❌ ОШИБКА"
            print(f"{test_name:<20} | {status:<10} | {message}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📈 ИТОГО: {passed} прошли, {failed} ошибок")
        
        if failed == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Бот полностью функционален.")
        else:
            print("⚠️  Есть проблемы, требующие исправления.")


async def main():
    """Главная функция"""
    tester = BotTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
