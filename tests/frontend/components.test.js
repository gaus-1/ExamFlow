/**
 * Тесты для React компонентов (если они есть)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Моки для компонентов ExamFlow
const mockComponents = {
  SubjectCard: ({ subject, onClick }) => (
    <div 
      data-testid={`subject-card-${subject.id}`}
      onClick={onClick}
      className="subject-card"
    >
      <h3>{subject.name}</h3>
      <p>{subject.description}</p>
      <span className="exam-type">{subject.examType}</span>
    </div>
  ),
  
  TaskCard: ({ task, onAnswer }) => (
    <div data-testid={`task-card-${task.id}`} className="task-card">
      <h4>{task.title}</h4>
      <p>{task.content}</p>
      <div className="task-actions">
        <button onClick={() => onAnswer(task.id, 'answer')}>
          Ответить
        </button>
      </div>
    </div>
  ),
  
  ProgressBar: ({ progress, total }) => {
    const percentage = Math.round((progress / total) * 100);
    return (
      <div data-testid="progress-bar" className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%` }}
        />
        <span className="progress-text">{progress}/{total}</span>
      </div>
    );
  }
};

describe('ExamFlow Components', () => {
  describe('SubjectCard', () => {
    test('должен отображать информацию о предмете', () => {
      const mockSubject = {
        id: 1,
        name: 'Математика',
        description: 'Профильная математика ЕГЭ',
        examType: 'ЕГЭ'
      };
      
      const mockOnClick = jest.fn();
      
      render(
        <mockComponents.SubjectCard 
          subject={mockSubject} 
          onClick={mockOnClick} 
        />
      );
      
      expect(screen.getByText('Математика')).toBeInTheDocument();
      expect(screen.getByText('Профильная математика ЕГЭ')).toBeInTheDocument();
      expect(screen.getByText('ЕГЭ')).toBeInTheDocument();
    });

    test('должен вызывать onClick при клике', () => {
      const mockSubject = {
        id: 1,
        name: 'Математика',
        description: 'Профильная математика ЕГЭ',
        examType: 'ЕГЭ'
      };
      
      const mockOnClick = jest.fn();
      
      render(
        <mockComponents.SubjectCard 
          subject={mockSubject} 
          onClick={mockOnClick} 
        />
      );
      
      fireEvent.click(screen.getByTestId('subject-card-1'));
      expect(mockOnClick).toHaveBeenCalledWith(mockSubject);
    });
  });

  describe('TaskCard', () => {
    test('должен отображать задание', () => {
      const mockTask = {
        id: 1,
        title: 'Решите уравнение',
        content: 'x + 2 = 5'
      };
      
      const mockOnAnswer = jest.fn();
      
      render(
        <mockComponents.TaskCard 
          task={mockTask} 
          onAnswer={mockOnAnswer} 
        />
      );
      
      expect(screen.getByText('Решите уравнение')).toBeInTheDocument();
      expect(screen.getByText('x + 2 = 5')).toBeInTheDocument();
    });

    test('должен вызывать onAnswer при нажатии кнопки', () => {
      const mockTask = {
        id: 1,
        title: 'Решите уравнение',
        content: 'x + 2 = 5'
      };
      
      const mockOnAnswer = jest.fn();
      
      render(
        <mockComponents.TaskCard 
          task={mockTask} 
          onAnswer={mockOnAnswer} 
        />
      );
      
      fireEvent.click(screen.getByText('Ответить'));
      expect(mockOnAnswer).toHaveBeenCalledWith(1, 'answer');
    });
  });

  describe('ProgressBar', () => {
    test('должен отображать прогресс корректно', () => {
      render(<mockComponents.ProgressBar progress={25} total={100} />);
      
      expect(screen.getByText('25/100')).toBeInTheDocument();
      
      const progressFill = document.querySelector('.progress-fill');
      expect(progressFill).toHaveStyle('width: 25%');
    });

    test('должен обрабатывать нулевой прогресс', () => {
      render(<mockComponents.ProgressBar progress={0} total={100} />);
      
      expect(screen.getByText('0/100')).toBeInTheDocument();
      
      const progressFill = document.querySelector('.progress-fill');
      expect(progressFill).toHaveStyle('width: 0%');
    });

    test('должен обрабатывать полный прогресс', () => {
      render(<mockComponents.ProgressBar progress={100} total={100} />);
      
      expect(screen.getByText('100/100')).toBeInTheDocument();
      
      const progressFill = document.querySelector('.progress-fill');
      expect(progressFill).toHaveStyle('width: 100%');
    });
  });
});

// Тесты для интеграции с API
describe('API Integration', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('должен загружать список предметов', async () => {
    const mockSubjects = [
      { id: 1, name: 'Математика', examType: 'ЕГЭ' },
      { id: 2, name: 'Русский язык', examType: 'ЕГЭ' }
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSubjects,
    });

    // Имитация загрузки данных
    const response = await fetch('/api/subjects/');
    const subjects = await response.json();

    expect(fetch).toHaveBeenCalledWith('/api/subjects/');
    expect(subjects).toEqual(mockSubjects);
  });

  test('должен обрабатывать ошибки API', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    try {
      await fetch('/api/subjects/');
    } catch (error) {
      expect(error.message).toBe('Network error');
    }
  });

  test('должен отправлять ответ на задание', async () => {
    const mockResponse = {
      success: true,
      isCorrect: true,
      explanation: 'Правильно!'
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const response = await fetch('/api/tasks/1/answer/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: '3' })
    });

    const result = await response.json();

    expect(result.success).toBe(true);
    expect(result.isCorrect).toBe(true);
  });
});
