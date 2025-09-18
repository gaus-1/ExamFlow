"""
Расширенные тесты для Telegram бота.
"""

import asyncio
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase
from telegram_bot.bot_handlers import BotHandlers

class TestBotHandlers(TestCase):
    """Тесты обработчиков Telegram бота."""

    def setUp(self):
        """Настройка тестов."""
        self.handlers = BotHandlers()
        self.mock_update = Mock()
        self.mock_context = Mock()

    def test_start_command(self):
        """Тест команды /start."""
        # Настраиваем мок
        self.mock_update.message = AsyncMock()
        self.mock_update.callback_query = None
        self.mock_update.effective_user = Mock()
        self.mock_update.effective_user.id = 123456789
        self.mock_update.effective_user.first_name = "Test"
        self.mock_update.effective_user.username = "testuser"

        # Вызываем обработчик асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.handlers.start_command(self.mock_update, self.mock_context)
            )
        finally:
            loop.close()

        # Проверяем, что сообщение было отправлено
        self.mock_update.message.reply_text.assert_called()

    def test_help_command(self):
        """Тест команды /help."""
        # Настраиваем мок
        self.mock_update.message = AsyncMock()
        self.mock_update.effective_user = Mock()
        self.mock_update.effective_user.id = 123456789

        # Вызываем обработчик асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.handlers.help_command(self.mock_update, self.mock_context)
            )
        finally:
            loop.close()

    @patch('core.rag_system.orchestrator.RAGOrchestrator')
    def test_search_command(self, mock_rag_class):
        """Тест команды поиска."""
        # Настраиваем мок RAG системы
        mock_rag = Mock()
        mock_rag_class.return_value = mock_rag
        mock_rag.process_query.return_value = {
            'answer': 'тест ответ',
            'sources': ['источник 1'],
            'cached': False
        }

        # Настраиваем мок сообщения
        self.mock_update.message.text = "/search тест запрос"
        self.mock_update.message.reply_text = Mock()

        # Вызываем обработчик асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.handlers.search_command(self.mock_update, self.mock_context)
            )
        finally:
            loop.close()

        # Проверяем, что RAG система была вызвана
        mock_rag.process_query.assert_called_once()

        # Проверяем, что ответ был отправлен
        self.mock_update.message.reply_text.assert_called_once()

    @patch('core.rag_system.orchestrator.RAGOrchestrator')
    def test_fipi_command(self, mock_rag_class):
        """Тест команды поиска по ФИПИ."""
        # Настраиваем мок RAG системы
        mock_rag = Mock()
        mock_rag_class.return_value = mock_rag
        mock_rag.process_query.return_value = {
            'answer': 'ФИПИ ответ',
            'sources': ['ФИПИ источник'],
            'cached': False
        }

        # Настраиваем мок сообщения
        self.mock_update.message.text = "/fipi математика"
        self.mock_update.message.reply_text = Mock()

        # Вызываем обработчик асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.handlers.fipi_command(self.mock_update, self.mock_context)
            )
        finally:
            loop.close()

        # Проверяем, что RAG система была вызвана с правильными параметрами
        mock_rag.process_query.assert_called_once()
        call_args = mock_rag.process_query.call_args[1]
        self.assertEqual(call_args['subject'], 'математика')
        self.assertEqual(call_args['document_type'], 'fipi')

    def test_handle_message_text(self):
        """Тест обработки текстовых сообщений."""
        # Настраиваем мок сообщения
        self.mock_update.message.text = "тест сообщение"
        self.mock_update.message.reply_text = Mock()

        # Мокаем RAG систему
        with patch('core.rag_system.orchestrator.RAGOrchestrator') as mock_rag_class:
            mock_rag = Mock()
            mock_rag_class.return_value = mock_rag
            mock_rag.process_query.return_value = {
                'answer': 'ответ на сообщение',
                'sources': [],
                'cached': False
            }
            # Вызываем обработчик (асинхронный вызов, результат нужно ожидать)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.handlers.handle_message(self.mock_update, self.mock_context)
                )
            finally:
                loop.close()

            # Проверяем, что RAG система была вызвана
            mock_rag.process_query.assert_called_once()

            # Проверяем, что ответ был отправлен
            self.mock_update.message.reply_text.assert_called_once()

    def test_handle_message_non_text(self):
        """Тест обработки не-текстовых сообщений."""
        # Настраиваем мок сообщения без текста
        self.mock_update.message.text = None
        self.mock_update.message.reply_text = Mock()

        # Вызываем обработчик (асинхронный вызов, результат нужно ожидать)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.handlers.handle_message(self.mock_update, self.mock_context)
            )
        finally:
            loop.close()

        # Проверяем, что сообщение было отправлено
        self.mock_update.message.reply_text.assert_called_once()
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn('текстовое сообщение', call_args)

    def test_error_handling(self):
        """Тест обработки ошибок."""
        # Настраиваем мок с ошибкой
        self.mock_update.message.text = "тест"
        self.mock_update.message.reply_text = Mock()

        # Мокаем RAG систему с ошибкой
        with patch('core.rag_system.orchestrator.RAGOrchestrator') as mock_rag_class:
            mock_rag = Mock()
            mock_rag_class.return_value = mock_rag
            mock_rag.process_query.side_effect = Exception("Тестовая ошибка")

            # Вызываем обработчик (асинхронный вызов, результат нужно ожидать)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.handlers.handle_message(self.mock_update, self.mock_context)
                )
            finally:
                loop.close()

            # Проверяем, что ошибка была обработана
            self.mock_update.message.reply_text.assert_called_once()
            call_args = self.mock_update.message.reply_text.call_args[0][0]
            self.assertIn('ошибка', call_args.lower())

class TestBotIntegration(TestCase):
    """Интеграционные тесты бота."""

    def test_bot_initialization(self):
        """Тест инициализации бота."""
        handlers = BotHandlers()
        self.assertIsNotNone(handlers)

    def test_command_parsing(self):
        """Тест парсинга команд."""
        handlers = BotHandlers()

        # Тест команды /search
        result = handlers._parse_search_command("/search тест запрос")
        self.assertEqual(result, "тест запрос")

        # Тест команды /fipi
        result = handlers._parse_fipi_command("/fipi математика")
        self.assertEqual(result, "математика")

        # Тест некорректных команд
        result = handlers._parse_search_command("обычное сообщение")
        self.assertIsNone(result)

    def test_message_formatting(self):
        """Тест форматирования сообщений."""
        handlers = BotHandlers()

        # Тест форматирования ответа RAG
        rag_response = {
            'answer': 'тест ответ',
            'sources': ['источник 1', 'источник 2'],
            'cached': False,
            'processing_time': 1.5
        }

        formatted = handlers._format_rag_response(rag_response)

        self.assertIn('тест ответ', formatted)
        self.assertIn('источник 1', formatted)
        self.assertIn('источник 2', formatted)
        self.assertIn('1.5', formatted)  # время обработки
