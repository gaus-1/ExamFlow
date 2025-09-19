/**
 * Тесты для утилитарных функций JavaScript
 */

// Тестируем функции валидации
const validationUtils = {
  isValidEmail: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },
  
  isValidTelegramId: (id) => {
    return typeof id === 'number' && id > 0 && id.toString().length >= 6;
  },
  
  sanitizeInput: (input) => {
    if (typeof input !== 'string') return '';
    return input.trim().replace(/[<>]/g, '');
  },
  
  formatExamType: (type) => {
    const types = {
      'ege': 'ЕГЭ',
      'oge': 'ОГЭ',
      'EGE': 'ЕГЭ',
      'OGE': 'ОГЭ'
    };
    return types[type] || type;
  },
  
  calculateProgress: (completed, total) => {
    if (total === 0) return 0;
    return Math.round((completed / total) * 100);
  }
};

describe('Validation Utils', () => {
  describe('isValidEmail', () => {
    test('должен валидировать корректные email адреса', () => {
      expect(validationUtils.isValidEmail('test@example.com')).toBe(true);
      expect(validationUtils.isValidEmail('user.name@domain.co.uk')).toBe(true);
      expect(validationUtils.isValidEmail('user+tag@example.org')).toBe(true);
    });

    test('должен отклонять некорректные email адреса', () => {
      expect(validationUtils.isValidEmail('invalid-email')).toBe(false);
      expect(validationUtils.isValidEmail('test@')).toBe(false);
      expect(validationUtils.isValidEmail('@example.com')).toBe(false);
      expect(validationUtils.isValidEmail('')).toBe(false);
    });
  });

  describe('isValidTelegramId', () => {
    test('должен валидировать корректные Telegram ID', () => {
      expect(validationUtils.isValidTelegramId(123456789)).toBe(true);
      expect(validationUtils.isValidTelegramId(987654321)).toBe(true);
      expect(validationUtils.isValidTelegramId(555666777)).toBe(true);
    });

    test('должен отклонять некорректные Telegram ID', () => {
      expect(validationUtils.isValidTelegramId(12345)).toBe(false);
      expect(validationUtils.isValidTelegramId(-123456789)).toBe(false);
      expect(validationUtils.isValidTelegramId('123456789')).toBe(false);
      expect(validationUtils.isValidTelegramId(null)).toBe(false);
    });
  });

  describe('sanitizeInput', () => {
    test('должен очищать пользовательский ввод', () => {
      expect(validationUtils.sanitizeInput('<script>alert("xss")</script>')).toBe('scriptalert("xss")/script');
      expect(validationUtils.sanitizeInput('  hello world  ')).toBe('hello world');
      expect(validationUtils.sanitizeInput('normal text')).toBe('normal text');
    });

    test('должен обрабатывать нестроковые входные данные', () => {
      expect(validationUtils.sanitizeInput(123)).toBe('');
      expect(validationUtils.sanitizeInput(null)).toBe('');
      expect(validationUtils.sanitizeInput(undefined)).toBe('');
    });
  });

  describe('formatExamType', () => {
    test('должен форматировать типы экзаменов', () => {
      expect(validationUtils.formatExamType('ege')).toBe('ЕГЭ');
      expect(validationUtils.formatExamType('oge')).toBe('ОГЭ');
      expect(validationUtils.formatExamType('EGE')).toBe('ЕГЭ');
      expect(validationUtils.formatExamType('OGE')).toBe('ОГЭ');
      expect(validationUtils.formatExamType('unknown')).toBe('unknown');
    });
  });

  describe('calculateProgress', () => {
    test('должен корректно вычислять прогресс', () => {
      expect(validationUtils.calculateProgress(5, 10)).toBe(50);
      expect(validationUtils.calculateProgress(3, 10)).toBe(30);
      expect(validationUtils.calculateProgress(10, 10)).toBe(100);
      expect(validationUtils.calculateProgress(0, 10)).toBe(0);
    });

    test('должен обрабатывать деление на ноль', () => {
      expect(validationUtils.calculateProgress(5, 0)).toBe(0);
    });
  });
});

// Тестируем функции работы с данными
const dataUtils = {
  sortTasksByDifficulty: (tasks) => {
    const difficultyOrder = { 'легкий': 1, 'средний': 2, 'сложный': 3 };
    return tasks.sort((a, b) => difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty]);
  },
  
  filterTasksBySubject: (tasks, subject) => {
    return tasks.filter(task => 
      task.subject.toLowerCase().includes(subject.toLowerCase())
    );
  },
  
  groupTasksByTopic: (tasks) => {
    return tasks.reduce((groups, task) => {
      const topic = task.topic || 'Общее';
      if (!groups[topic]) {
        groups[topic] = [];
      }
      groups[topic].push(task);
      return groups;
    }, {});
  }
};

describe('Data Utils', () => {
  const mockTasks = [
    { id: 1, title: 'Задача 1', difficulty: 'сложный', subject: 'Математика', topic: 'Алгебра' },
    { id: 2, title: 'Задача 2', difficulty: 'легкий', subject: 'Математика', topic: 'Геометрия' },
    { id: 3, title: 'Задача 3', difficulty: 'средний', subject: 'Русский язык', topic: 'Орфография' },
    { id: 4, title: 'Задача 4', difficulty: 'средний', subject: 'Математика', topic: 'Алгебра' },
  ];

  describe('sortTasksByDifficulty', () => {
    test('должен сортировать задачи по сложности', () => {
      const sorted = dataUtils.sortTasksByDifficulty([...mockTasks]);
      expect(sorted[0].difficulty).toBe('легкий');
      expect(sorted[1].difficulty).toBe('средний');
      expect(sorted[2].difficulty).toBe('средний');
      expect(sorted[3].difficulty).toBe('сложный');
    });
  });

  describe('filterTasksBySubject', () => {
    test('должен фильтровать задачи по предмету', () => {
      const mathTasks = dataUtils.filterTasksBySubject(mockTasks, 'математика');
      expect(mathTasks).toHaveLength(3);
      expect(mathTasks.every(task => task.subject === 'Математика')).toBe(true);
    });
  });

  describe('groupTasksByTopic', () => {
    test('должен группировать задачи по темам', () => {
      const grouped = dataUtils.groupTasksByTopic(mockTasks);
      expect(grouped['Алгебра']).toHaveLength(2);
      expect(grouped['Геометрия']).toHaveLength(1);
      expect(grouped['Орфография']).toHaveLength(1);
    });
  });
});
