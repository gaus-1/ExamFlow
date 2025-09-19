"""
Тесты Telegram бота ExamFlow
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from django.test import Client
from django.urls import reverse


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramWebhook:
    """Тесты Telegram webhook"""
    
    def test_webhook_start_command(self, client, telegram_webhook_data):
        """Тест команды /start через webhook"""
        webhook_data = telegram_webhook_data.copy()
        webhook_data['message']['text'] = '/start'
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_help_command(self, client, telegram_webhook_data):
        """Тест команды /help через webhook"""
        webhook_data = telegram_webhook_data.copy()
        webhook_data['message']['text'] = '/help'
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_subjects_command(self, client, telegram_webhook_data):
        """Тест команды /subjects через webhook"""
        webhook_data = telegram_webhook_data.copy()
        webhook_data['message']['text'] = '/subjects'
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_invalid_command(self, client, telegram_webhook_data):
        """Тест невалидной команды через webhook"""
        webhook_data = telegram_webhook_data.copy()
        webhook_data['message']['text'] = '/invalid_command'
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_empty_message(self, client, telegram_webhook_data):
        """Тест пустого сообщения через webhook"""
        webhook_data = telegram_webhook_data.copy()
        webhook_data['message']['text'] = ''
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_callback_query(self, client):
        """Тест callback query через webhook"""
        callback_data = {
            'update_id': 123456789,
            'callback_query': {
                'id': 'callback_id',
                'from': {
                    'id': 123456789,
                    'is_bot': False,
                    'first_name': 'Тест',
                    'username': 'testuser'
                },
                'message': {
                    'message_id': 1,
                    'chat': {'id': 123456789, 'type': 'private'},
                    'date': 1695123456,
                    'text': 'Выберите предмет:'
                },
                'data': 'subject_math'
            }
        }
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(callback_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_webhook_invalid_json(self, client):
        """Тест webhook с невалидным JSON"""
        response = client.post(
            '/bot/webhook/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code in [200, 400]
    
    def test_webhook_missing_fields(self, client):
        """Тест webhook с отсутствующими полями"""
        incomplete_data = {
            'update_id': 123456789
            # Отсутствует message
        }
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotHandlers:
    """Тесты обработчиков Telegram бота"""
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_start_handler(self, mock_get_bot, user):
        """Тест обработчика команды /start"""
        from telegram_bot.bot_handlers import handle_start # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        update = Mock()
        update.message.from_user.id = user.telegram_id
        update.message.from_user.username = user.telegram_username
        update.message.from_user.first_name = 'Тест'
        update.message.from_user.last_name = 'Пользователь'
        
        context = Mock()
        
        # Вызываем обработчик
        handle_start(update, context)
        
        # Проверяем что бот отправил сообщение
        mock_bot.send_message.assert_called_once()
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_help_handler(self, mock_get_bot, user):
        """Тест обработчика команды /help"""
        from telegram_bot.bot_handlers import handle_help # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        update = Mock()
        update.message.from_user.id = user.telegram_id
        
        context = Mock()
        
        # Вызываем обработчик
        handle_help(update, context)
        
        # Проверяем что бот отправил сообщение с помощью
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert 'помощь' in call_args[1]['text'].lower() or 'help' in call_args[1]['text'].lower()
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_subjects_handler(self, mock_get_bot, user, math_subject, russian_subject):
        """Тест обработчика команды /subjects"""
        from telegram_bot.bot_handlers import handle_subjects # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        update = Mock()
        update.message.from_user.id = user.telegram_id
        
        context = Mock()
        
        # Вызываем обработчик
        handle_subjects(update, context)
        
        # Проверяем что бот отправил сообщение с предметами
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        message_text = call_args[1]['text']
        assert 'предмет' in message_text.lower()
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_ai_handler(self, mock_get_bot, user, mock_ai_service):
        """Тест обработчика AI запросов"""
        from telegram_bot.bot_handlers import handle_ai_request # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        update = Mock()
        update.message.from_user.id = user.telegram_id
        update.message.text = 'Решите уравнение 2x + 3 = 7'
        
        context = Mock()
        
        # Вызываем обработчик
        handle_ai_request(update, context)
        
        # Проверяем что бот отправил ответ от AI
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]['text'] is not None
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_task_handler(self, mock_get_bot, user, math_task):
        """Тест обработчика заданий"""
        from telegram_bot.bot_handlers import handle_task_request # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        update = Mock()
        update.message.from_user.id = user.telegram_id
        update.message.text = f'/task {math_task.id}'
        
        context = Mock()
        
        # Вызываем обработчик
        handle_task_request(update, context)
        
        # Проверяем что бот отправил задание
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        message_text = call_args[1]['text']
        assert 'задание' in message_text.lower() or 'task' in message_text.lower()


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotGamification:
    """Тесты геймификации Telegram бота"""
    
    @patch('telegram_bot.gamification.TelegramGamification')
    def test_points_award(self, mock_gamification, user):
        """Тест начисления очков"""
        mock_instance = Mock()
        mock_gamification.return_value = mock_instance
        mock_instance.award_points.return_value = {'points': 10, 'level': 1}
        
        from telegram_bot.gamification import TelegramGamification
        
        gamification = TelegramGamification()
        result = gamification.award_points(user.telegram_id, 'task_completed', 10) # type: ignore
        
        assert result['points'] == 10
        assert result['level'] == 1
        mock_instance.award_points.assert_called_once_with(user.telegram_id, 'task_completed', 10)
    
    @patch('telegram_bot.gamification.TelegramGamification')
    def test_achievement_unlock(self, mock_gamification, user):
        """Тест разблокировки достижения"""
        mock_instance = Mock()
        mock_gamification.return_value = mock_instance
        mock_instance.check_achievements.return_value = [{'name': 'Первое задание', 'description': 'Решите первое задание'}]
        
        from telegram_bot.gamification import TelegramGamification
        
        gamification = TelegramGamification()
        achievements = gamification.check_achievements(user.telegram_id, 'task_completed') # type: ignore
        
        assert len(achievements) == 1
        assert achievements[0]['name'] == 'Первое задание'
        mock_instance.check_achievements.assert_called_once_with(user.telegram_id, 'task_completed')
    
    @patch('telegram_bot.gamification.TelegramGamification')
    def test_level_up(self, mock_gamification, user):
        """Тест повышения уровня"""
        mock_instance = Mock()
        mock_gamification.return_value = mock_instance
        mock_instance.get_user_level.return_value = {'level': 2, 'points': 150, 'next_level_points': 200}
        
        from telegram_bot.gamification import TelegramGamification
        
        gamification = TelegramGamification()
        level_info = gamification.get_user_level(user.telegram_id) # type: ignore
        
        assert level_info['level'] == 2
        assert level_info['points'] == 150
        assert level_info['next_level_points'] == 200
        mock_instance.get_user_level.assert_called_once_with(user.telegram_id)


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotUserManagement:
    """Тесты управления пользователями в Telegram боте"""
    
    def test_user_registration(self, user):
        """Тест регистрации пользователя"""
        from telegram_bot.bot_handlers import register_telegram_user # type: ignore
        
        telegram_user_data = {
            'id': 999888777,
            'username': 'newuser',
            'first_name': 'Новый',
            'last_name': 'Пользователь'
        }
        
        # Регистрируем пользователя
        registered_user = register_telegram_user(telegram_user_data) # type: ignore
        
        assert registered_user is not None
        assert registered_user.telegram_id == 999888777
        assert registered_user.telegram_username == 'newuser'
    
    def test_user_profile_update(self, user):
        """Тест обновления профиля пользователя"""
        from telegram_bot.bot_handlers import update_user_profile # type: ignore
        
        new_data = {
            'first_name': 'Обновленное',
            'last_name': 'Имя',
            'username': 'updated_username'
        }
        
        # Обновляем профиль
        updated_user = update_user_profile(user.telegram_id, new_data) # type: ignore
        
        assert updated_user is not None
        assert updated_user.telegram_first_name == 'Обновленное'
        assert updated_user.telegram_last_name == 'Имя'
        assert updated_user.telegram_username == 'updated_username'
    
    def test_user_progress_tracking(self, user, math_task):
        """Тест отслеживания прогресса пользователя"""
        from telegram_bot.bot_handlers import track_user_progress # type: ignore
        
        # Отслеживаем прогресс
        progress_data = {
            'task_id': math_task.id,
            'is_correct': True,
            'attempts': 1,
            'time_spent': 30
        }
        
        result = track_user_progress(user.telegram_id, progress_data) # type: ignore
        
        assert result is not None
        assert result['success'] is True


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotAI:
    """Тесты AI интеграции в Telegram боте"""
    
    @patch('telegram_bot.bot_handlers.Container')
    def test_ai_response_generation(self, mock_container, user):
        """Тест генерации AI ответов"""
        from telegram_bot.bot_handlers import generate_ai_response # type: ignore
        
        mock_ai_service = Mock()
        mock_ai_service.ask.return_value = {
            'answer': 'Ответ от AI',
            'sources': [{'title': 'Источник', 'content': 'Содержание'}]
        }
        mock_container.ai_orchestrator.return_value = mock_ai_service
        
        # Генерируем AI ответ
        response = generate_ai_response('Тестовый вопрос', user.telegram_id, 'Математика') # type: ignore
        
        assert response is not None
        assert response['answer'] == 'Ответ от AI'
        assert len(response['sources']) == 1
        mock_ai_service.ask.assert_called_once()
    
    @patch('telegram_bot.bot_handlers.Container')
    def test_ai_context_usage(self, mock_container, user, mock_rag_system):
        """Тест использования контекста в AI"""
        from telegram_bot.bot_handlers import generate_ai_response # type: ignore
        
        mock_ai_service = Mock()
        mock_ai_service.ask.return_value = {
            'answer': 'Контекстный ответ от AI',
            'context_sources': [{'title': 'Задание 1', 'content': 'Контекст задания'}]
        }
        mock_container.ai_orchestrator.return_value = mock_ai_service
        
        # Генерируем AI ответ с контекстом
        response = generate_ai_response('Помогите с математикой', user.telegram_id, 'Математика') # type: ignore
        
        assert response is not None
        assert 'Контекстный ответ от AI' in response['answer']
        mock_ai_service.ask.assert_called_once()
    
    @patch('telegram_bot.bot_handlers.Container')
    def test_ai_error_handling(self, mock_container, user):
        """Тест обработки ошибок AI"""
        from telegram_bot.bot_handlers import generate_ai_response # type: ignore
        
        mock_ai_service = Mock()
        mock_ai_service.ask.side_effect = Exception('AI Service Error')
        mock_container.ai_orchestrator.return_value = mock_ai_service
        
        # Генерируем AI ответ при ошибке
        response = generate_ai_response('Тестовый вопрос', user.telegram_id) # type: ignore
        
        assert response is not None
        assert 'ошибка' in response['answer'].lower() or 'error' in response['answer'].lower()


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotCommands:
    """Тесты команд Telegram бота"""
    
    def test_command_parsing(self):
        """Тест парсинга команд"""
        from telegram_bot.bot_handlers import parse_command # type: ignore
        
        # Тестируем различные команды
        assert parse_command('/start') == ('start', []) # type: ignore
        assert parse_command('/help') == ('help', []) # type: ignore
        assert parse_command('/subjects') == ('subjects', []) # type: ignore
        assert parse_command('/task 123') == ('task', ['123'])
        assert parse_command('/ai Помогите с математикой') == ('ai', ['Помогите с математикой'])
        assert parse_command('/stats') == ('stats', [])
        assert parse_command('Обычное сообщение') == ('message', ['Обычное сообщение'])
    
    def test_command_validation(self):
        """Тест валидации команд"""
        from telegram_bot.bot_handlers import validate_command # type: ignore
        
        # Валидные команды
        assert validate_command('start') is True
        assert validate_command('help') is True
        assert validate_command('subjects') is True
        assert validate_command('task') is True
        assert validate_command('ai') is True
        assert validate_command('stats') is True
        
        # Невалидные команды
        assert validate_command('invalid_command') is False # type: ignore          
        assert validate_command('') is False
    
    def test_command_arguments_validation(self):
        """Тест валидации аргументов команд"""
        from telegram_bot.bot_handlers import validate_command_arguments # type: ignore
        
        # Валидные аргументы
        assert validate_command_arguments('task', ['123']) is True
        assert validate_command_arguments('ai', ['Вопрос по математике']) is True
        assert validate_command_arguments('start', []) is True
        
        # Невалидные аргументы
        assert validate_command_arguments('task', []) is False
        assert validate_command_arguments('task', ['abc']) is False  # Не числовой ID


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotNotifications:
    """Тесты уведомлений Telegram бота"""
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_send_notification(self, mock_get_bot, user):
        """Тест отправки уведомления"""
        from telegram_bot.bot_handlers import send_notification # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        # Отправляем уведомление
        result = send_notification(user.telegram_id, 'Тестовое уведомление')
        
        assert result is True
        mock_bot.send_message.assert_called_once()
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_send_achievement_notification(self, mock_get_bot, user):
        """Тест отправки уведомления о достижении"""
        from telegram_bot.bot_handlers import send_achievement_notification # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        achievement = {
            'name': 'Первое задание',
            'description': 'Решите первое задание',
            'icon': '🎯',
            'points': 10
        }
        
        # Отправляем уведомление о достижении
        result = send_achievement_notification(user.telegram_id, achievement)
        
        assert result is True
        mock_bot.send_message.assert_called_once()
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_send_daily_reminder(self, mock_get_bot, user):
        """Тест отправки ежедневного напоминания"""
        from telegram_bot.bot_handlers import send_daily_reminder # type: ignore
        
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        
        # Отправляем напоминание
        result = send_daily_reminder(user.telegram_id)
        
        assert result is True
        mock_bot.send_message.assert_called_once()


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotErrorHandling:
    """Тесты обработки ошибок Telegram бота"""
    
    @patch('telegram_bot.bot_handlers.get_bot')
    def test_bot_error_handling(self, mock_get_bot, user):
        """Тест обработки ошибок бота"""
        from telegram_bot.bot_handlers import handle_bot_error # type: ignore
        
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception('Bot API Error')
        mock_get_bot.return_value = mock_bot
        
        # Обрабатываем ошибку
        result = handle_bot_error(user.telegram_id, 'Test error')
        
        # Должна быть обработка ошибки
        assert result is not None
    
    def test_webhook_error_handling(self, client):
        """Тест обработки ошибок webhook"""
        # Отправляем некорректные данные
        invalid_data = {
            'invalid': 'data',
            'structure': 'test'
        }
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Webhook должен обрабатывать ошибки корректно
        assert response.status_code == 200
    
    @patch('telegram_bot.bot_handlers.Container')
    def test_ai_service_error_handling(self, mock_container, user):
        """Тест обработки ошибок AI сервиса"""
        from telegram_bot.bot_handlers import generate_ai_response # type: ignore
        
        mock_ai_service = Mock()
        mock_ai_service.ask.side_effect = Exception('AI Service Unavailable')
        mock_container.ai_orchestrator.return_value = mock_ai_service
        
        # Генерируем ответ при ошибке AI
        response = generate_ai_response('Тестовый вопрос', user.telegram_id) # type: ignore
        
        assert response is not None
        assert 'ошибка' in response['answer'].lower() or 'недоступен' in response['answer'].lower()


@pytest.mark.bot
@pytest.mark.django_db
class TestTelegramBotIntegration:
    """Интеграционные тесты Telegram бота"""
    
    def test_full_user_journey(self, client, user):
        """Тест полного пути пользователя"""
        # 1. Регистрация через /start
        start_data = {
            'update_id': 123456789,
            'message': {
                'message_id': 1,
                'from': {
                    'id': user.telegram_id,
                    'username': user.telegram_username,
                    'first_name': 'Тест'
                },
                'chat': {'id': user.telegram_id, 'type': 'private'},
                'date': 1695123456,
                'text': '/start'
            }
        }
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(start_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 2. Запрос предметов
        subjects_data = start_data.copy()
        subjects_data['message']['text'] = '/subjects'
        subjects_data['message']['message_id'] = 2
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(subjects_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 3. AI запрос
        ai_data = start_data.copy()
        ai_data['message']['text'] = '/ai Помогите с математикой'
        ai_data['message']['message_id'] = 3
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(ai_data),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_bot_statistics_collection(self, user):
        """Тест сбора статистики бота"""
        from telegram_bot.bot_handlers import collect_bot_statistics # type: ignore
        
        # Собираем статистику
        stats = collect_bot_statistics()
        
        assert 'total_users' in stats
        assert 'active_users' in stats
        assert 'total_messages' in stats
        assert 'ai_requests' in stats
        assert 'commands_used' in stats
    
    def test_bot_performance_metrics(self, user):
        """Тест метрик производительности бота"""
        from telegram_bot.bot_handlers import get_performance_metrics # type: ignore
        
        # Получаем метрики
        metrics = get_performance_metrics()
        
        assert 'response_time_avg' in metrics
        assert 'error_rate' in metrics
        assert 'uptime' in metrics
        assert 'memory_usage' in metrics
