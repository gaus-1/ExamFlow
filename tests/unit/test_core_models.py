#!/usr/bin/env python
"""
Тесты для моделей core приложения
"""

import pytest
from django.test import TestCase
from unittest.mock import Mock, patch

from telegram_auth.models import TelegramUser
from core.models import (
    Subject, Task, UserProgress, UserProfile, 
    DailyChallenge, UserChallenge, ChatSession,
    FIPIData, FIPISourceMap
)


class TestCoreModels(TestCase):
    """Тесты для основных моделей core"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем пользователя Telegram
        self.user = TelegramUser.objects.create(
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        # Создаем профиль пользователя
        self.profile = UserProfile.objects.create( # type: ignore
            user=self.user
        )
        
        # Создаем предмет
        self.subject = Subject.objects.first() # type: ignore
        if not self.subject:
            self.subject = Subject.objects.create( # type: ignore
                name='Тестовая Математика',
                description='Тестовая математика для тестов',
                exam_type=''
            )
        
        # Создаем задание
        self.task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            text='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1
        )
    
    def test_subject_creation(self):
        """Тест создания предмета"""
        subject = Subject.objects.create( # type: ignore
            name='Тестовый Русский язык',
            description='Тестовый русский язык для тестов'
        )
        
        assert subject.name == 'Тестовый Русский язык'
        assert subject.description == 'Тестовый русский язык для тестов'
        assert str(subject) is not None
    
    def test_subject_str_method(self):
        """Тест метода __str__ для Subject"""
        assert str(self.subject) is not None
        assert len(str(self.subject)) > 0
    
    def test_task_creation(self):
        """Тест создания задания"""
        task = Task.objects.create( # type: ignore
            title='Тестовое задание 2',
            description='Решите уравнение x + 2 = 3',
            subject=self.subject,
            difficulty=2
        )
        
        assert task.title == 'Тестовое задание 2'
        assert task.description == 'Решите уравнение x + 2 = 3'
        assert task.subject == self.subject
        assert task.difficulty == 2
    
    def test_task_str_method(self):
        """Тест метода __str__ для Task"""
        assert str(self.task) == self.task.title
    
    def test_user_progress_creation(self):
        """Тест создания прогресса пользователя"""
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_correct=True,
            attempts=1
        )
        
        assert progress.user == self.user
        assert progress.task == self.task
        assert progress.is_correct is True
        assert progress.attempts == 1
    
    def test_user_progress_str_method(self):
        """Тест метода __str__ для UserProgress"""
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_correct=True
        )
        
        expected_str = f'{self.user.telegram_username} - {self.task.subject.name}'
        assert str(progress) == expected_str
    
    def test_user_profile_creation(self):
        """Тест создания профиля пользователя"""
        profile = UserProfile.objects.create( # type: ignore
            user=self.user,
        )
        
        assert profile.user == self.user
    
    def test_user_profile_str_method(self):
        """Тест метода __str__ для UserProfile"""
        assert str(self.profile) == self.user.telegram_username
    
    def test_daily_challenge_creation(self):
        """Тест создания ежедневного вызова"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание вызова',
            challenge_type='math',
            difficulty=1
        )
        
        assert challenge.title == 'Тестовый вызов'
        assert challenge.description == 'Описание вызова'
        assert challenge.challenge_type == 'math'
        assert challenge.difficulty == 1
    
    def test_daily_challenge_str_method(self):
        """Тест метода __str__ для DailyChallenge"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание вызова',
            challenge_type='math'
        )
        
        assert str(challenge) == 'Тестовый вызов'
    
    def test_user_challenge_creation(self):
        """Тест создания пользовательского вызова"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание вызова',
            challenge_type='math'
        )
        
        user_challenge = UserChallenge.objects.create( # type: ignore
            user=self.user,
            challenge=challenge,
            current_progress=50
        )
        
        assert user_challenge.user == self.user
        assert user_challenge.challenge == challenge
        assert user_challenge.current_progress == 50
    
    def test_user_challenge_progress_percentage(self):
        """Тест расчета процента прогресса"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание вызова',
            challenge_type='math',
            target_value=100
        )
        
        user_challenge = UserChallenge.objects.create( # type: ignore
            user=self.user,
            challenge=challenge,
            current_progress=75
        )
        
        assert user_challenge.progress_percentage == 75.0
    
    def test_chat_session_creation(self):
        """Тест создания сессии чата"""
        session = ChatSession.objects.create( # type: ignore
            user=self.user,
            subject=self.subject
        )
        
        assert session.user == self.user
        assert session.subject == self.subject
        assert session.messages == []
    
    def test_chat_session_add_message(self):
        """Тест добавления сообщения в сессию"""
        session = ChatSession.objects.create( # type: ignore
            user=self.user,
            subject=self.subject
        )
        
        session.add_message('user', 'Привет!')
        session.add_message('ai', 'Привет! Как дела?')
        
        assert len(session.messages) == 2
        assert session.messages[0]['role'] == 'user'
        assert session.messages[0]['content'] == 'Привет!'
        assert session.messages[1]['role'] == 'ai'
        assert session.messages[1]['content'] == 'Привет! Как дела?'
    
    def test_chat_session_get_context_for_ai(self):
        """Тест получения контекста для ИИ"""
        session = ChatSession.objects.create( # type: ignore
            user=self.user,
            subject=self.subject
        )
        
        session.add_message('user', 'Решите уравнение x + 1 = 2')
        session.add_message('ai', 'x = 1')
        
        context = session.get_context_for_ai()
        
        assert 'subject' in context
        assert 'messages' in context
        assert context['subject'] == self.subject.name
        assert len(context['messages']) == 2
    
    def test_fipi_data_creation(self):
        """Тест создания FIPI данных"""
        fipi_data = FIPIData.objects.create( # type: ignore
            title='Тестовые данные FIPI',
            description='Содержимое данных',
            data_type='task',
            exam_type='ege',
            difficulty=1
        )
        
        assert fipi_data.title == 'Тестовые данные FIPI'
        assert fipi_data.content == 'Содержимое данных'
        assert fipi_data.data_type == 'task'
        assert fipi_data.exam_type == 'ege'
        assert fipi_data.difficulty == 1
    
    def test_fipi_data_str_method(self):
        """Тест метода __str__ для FIPIData"""
        fipi_data = FIPIData.objects.create( # type: ignore
            title='Тестовые данные FIPI',
            description='Содержимое данных',
            data_type='task'
        )
        
        assert str(fipi_data) == 'Тестовые данные FIPI'
    
    def test_fipi_source_map_creation(self):
        """Тест создания карты источников FIPI"""
        source_map = FIPISourceMap.objects.create( # type: ignore
            source_name='Тестовый источник',
            source_url='https://example.com',
            priority=1
        )
        
        assert source_map.source_name == 'Тестовый источник'
        assert source_map.source_url == 'https://example.com'
        assert source_map.priority == 1
    
    def test_fipi_source_map_str_method(self):
        """Тест метода __str__ для FIPISourceMap"""
        source_map = FIPISourceMap.objects.create( # type: ignore
            source_name='Тестовый источник',
            source_url='https://example.com'
        )
        
        assert str(source_map) == 'Тестовый источник'
    
    def test_task_check_answer_correct(self):
        """Тест проверки правильного ответа"""
        task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            text='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1,
            answer='1'
        )
        
        assert task.check_answer('1') is True
        assert task.check_answer(' 1 ') is True
        assert task.check_answer('1.0') is False  # Строгое сравнение
    
    def test_task_check_answer_incorrect(self):
        """Тест проверки неправильного ответа"""
        task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            text='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1,
            answer='1'
        )
        
        assert task.check_answer('2') is False
        assert task.check_answer('') is False
    
    def test_task_check_answer_no_answer(self):
        """Тест проверки ответа для задачи без правильного ответа"""
        task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            text='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1
        )
        
        assert task.check_answer('1') is False
    
    def test_task_check_answer_case_insensitive(self):
        """Тест проверки ответа без учета регистра"""
        task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            description='Назовите столицу России',
            subject=self.subject,
            difficulty=1,
            answer='Москва'
        )
        
        assert task.check_answer('москва') is True
        assert task.check_answer('МОСКВА') is True
        assert task.check_answer('Москва') is True
    
    def test_user_progress_relationships(self):
        """Тест связей UserProgress"""
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            user_answer='1',
            is_correct=True,
            attempts=2,
            time_spent=120
        )
        
        assert progress.user == self.user
        assert progress.task == self.task
        assert progress.user_answer == '1'
        assert progress.is_correct is True
        assert progress.attempts == 2
        assert progress.time_spent == 120
    
    def test_subject_choices(self):
        """Тест choices для Subject"""
        subject = Subject.objects.create( # type: ignore
            name='Тестовый предмет',
            description='Описание',
            exam_type='oge'
        )
        
        assert subject.get_exam_type_display() == 'ОГЭ'
    
    def test_daily_challenge_choices(self):
        """Тест choices для DailyChallenge"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание',
            challenge_type='russian'
        )
        
        assert challenge.get_challenge_type_display() == 'Русский язык'
    
    def test_user_challenge_relationships(self):
        """Тест связей UserChallenge"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание',
            challenge_type='math',
            target_value=100
        )
        
        user_challenge = UserChallenge.objects.create( # type: ignore
            user=self.user,
            challenge=challenge,
            current_progress=50
        )
        
        assert user_challenge.user == self.user
        assert user_challenge.challenge == challenge
        assert user_challenge.current_progress == 50
        assert user_challenge.progress_percentage == 50.0
    
    def test_user_challenge_zero_target(self):
        """Тест UserChallenge с нулевым target_value"""
        challenge = DailyChallenge.objects.create( # type: ignore
            title='Тестовый вызов',
            description='Описание',
            challenge_type='math',
            target_value=0
        )
        
        user_challenge = UserChallenge.objects.create( # type: ignore
            user=self.user,
            challenge=challenge,
            current_progress=50
        )
        
        # При target_value=0 должно возвращать 0
        assert user_challenge.progress_percentage == 0.0
    
    def test_chat_session_message_limit(self):
        """Тест ограничения количества сообщений в ChatSession"""
        session = ChatSession.objects.create( # type: ignore
            user=self.user,
            subject=self.subject
        )
        
        # Добавляем много сообщений
        for i in range(50):
            session.add_message('user', f'Сообщение {i}')
            session.add_message('ai', f'Ответ {i}')
        
        # Должно быть ограничение на количество сообщений
        assert len(session.messages) <= 50  # Или какое-то разумное ограничение
    
    def test_fipi_data_choices(self):
        """Тест choices для FIPIData"""
        fipi_data = FIPIData.objects.create( # type: ignore
            title='Тестовые данные',
            description='Содержимое',
            data_type='task',
            exam_type='ege',
            difficulty=2
        )
        
        assert fipi_data.get_data_type_display() == 'Задание'
        assert fipi_data.get_exam_type_display() == 'ЕГЭ'
        assert fipi_data.get_difficulty_display() == 'Средняя'
    
    def test_fipi_source_map_update_frequency(self):
        """Тест update_frequency для FIPISourceMap"""
        source_map = FIPISourceMap.objects.create( # type: ignore
            source_name='Тестовый источник',
            source_url='https://example.com',
            update_frequency='daily'
        )
        
        assert source_map.get_update_frequency_display() == 'Ежедневно'
