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
            user=self.user,
            subscription='free'
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
            description='Решите уравнение x + 1 = 2',
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
            subscription='premium'
        )
        
        assert profile.user == self.user
        assert profile.subscription == 'premium'
    
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
            content='Содержимое данных',
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
            content='Содержимое данных',
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
