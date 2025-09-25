#!/usr/bin/env python
"""
Простые тесты для learning.models
"""

import pytest
from django.test import TestCase
from learning.models import Subject, Task


class TestLearningModelsSimple(TestCase):
    """Простые тесты для learning.models"""
    
    def test_subject_creation(self):
        """Тест создания предмета"""
        subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ',
            exam_type='other'
        )
        
        self.assertEqual(subject.name, 'Математика')
        self.assertEqual(subject.description, 'Математика для ЕГЭ')
        self.assertEqual(subject.exam_type, 'ege')
        self.assertTrue(subject.is_primary)
        self.assertFalse(subject.is_archived)
    
    def test_subject_str_method(self):
        """Тест метода __str__ для Subject"""
        subject = Subject.objects.create( # type: ignore
            name='Русский язык',
            description='Русский язык для ЕГЭ',
            exam_type='other'
        )
        
        expected_str = f'{subject.name} ({subject.exam_type})'
        self.assertEqual(str(subject), expected_str)
    
    def test_task_creation(self):
        """Тест создания задания"""
        subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ',
            exam_type='other'
        )
        
        task = Task.objects.create( # type: ignore
            title='Задача 1',
            text='Решите уравнение x + 1 = 2',
            subject=subject,
            difficulty=1,
            answer='1'
        )
        
        self.assertEqual(task.title, 'Задача 1')
        self.assertEqual(task.text, 'Решите уравнение x + 1 = 2')
        self.assertEqual(task.subject, subject)
        self.assertEqual(task.difficulty, 1)
        self.assertEqual(task.answer, '1')
    
    def test_task_str_method(self):
        """Тест метода __str__ для Task"""
        subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ',
            exam_type='other'
        )
        
        task = Task.objects.create( # type: ignore
            title='Задача 1',
            text='Решите уравнение x + 1 = 2',
            subject=subject,
            difficulty=1
        )
        
        expected_str = f'{subject.name}: {task.title}'
        self.assertEqual(str(task), expected_str)
    
    def test_task_check_answer_correct(self):
        """Тест проверки правильного ответа"""
        subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ',
            exam_type='other'
        )
        
        task = Task.objects.create( # type: ignore
            title='Задача 1',
            text='Решите уравнение x + 1 = 2',
            subject=subject,
            difficulty=1,
            answer='1'
        )
        
        self.assertTrue(task.check_answer('1'))
        self.assertTrue(task.check_answer('1.0'))
        self.assertTrue(task.check_answer(' 1 '))
    
    def test_task_check_answer_incorrect(self):
        """Тест проверки неправильного ответа"""
        subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ',
            exam_type='other'
        )
        
        task = Task.objects.create( # type: ignore  
            title='Задача 1',
            text='Решите уравнение x + 1 = 2',
            subject=subject,
            difficulty=1,
            answer='1'
        )
        
        self.assertFalse(task.check_answer('2'))
        self.assertFalse(task.check_answer(''))
        self.assertFalse(task.check_answer(None))
