/* ========================================
   EXAMFLOW 2.0 - СОВРЕМЕННЫЙ JAVASCRIPT
   ======================================== */

// ========================================
// УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ========================================

/**
 * Утилита для объединения CSS классов
 */
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Утилита для получения CSRF токена
 */
function getCSRFToken() {
  const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (token) return token;
  
  // Fallback - поиск в cookies
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Утилита для debounce
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Утилита для throttle
 */
function throttle(func, limit) {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Утилита для анимации при скролле
 */
function animateOnScroll() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
      }
    });
  });

  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
  });
}

// ========================================
// КОМПОНЕНТЫ - КНОПКИ
// ========================================

/**
 * Инициализация кнопок с эффектами
 */
function initButtons() {
  document.querySelectorAll('.btn').forEach(button => {
    // Добавляем ripple эффект
    button.addEventListener('click', function(e) {
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('ripple');
      
      this.appendChild(ripple);
      
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
}

// ========================================
// КОМПОНЕНТЫ - ПОЛЯ ВВОДА
// ========================================

/**
 * Инициализация полей ввода с анимацией
 */
function initInputs() {
  document.querySelectorAll('.input').forEach(input => {
    // Добавляем класс при фокусе
    input.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
      if (!this.value) {
        this.parentElement.classList.remove('focused');
      }
    });
    
    // Автоматическое изменение размера для textarea
    if (input.tagName === 'TEXTAREA') {
      input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
      });
    }
  });
}

// ========================================
// КОМПОНЕНТЫ - МОДАЛЬНЫЕ ОКНА
// ========================================

/**
 * Класс для управления модальными окнами
 */
class Modal {
  constructor(modalId) {
    this.modal = document.getElementById(modalId);
    this.overlay = this.modal?.querySelector('.modal-overlay');
    this.content = this.modal?.querySelector('.modal');
    this.isOpen = false;
    
    this.init();
  }
  
  init() {
    if (!this.modal) return;
    
    // Закрытие по клику на overlay
    this.overlay?.addEventListener('click', () => this.close());
    
    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }
  
  open() {
    if (!this.modal) return;
    
    this.modal.style.display = 'flex';
    this.isOpen = true;
    document.body.style.overflow = 'hidden';
    
    // Анимация появления
    setTimeout(() => {
      this.content?.classList.add('scale-in');
    }, 10);
  }
  
  close() {
    if (!this.modal) return;
    
    this.content?.classList.remove('scale-in');
    
    setTimeout(() => {
      this.modal.style.display = 'none';
      this.isOpen = false;
      document.body.style.overflow = '';
    }, 300);
  }
}

// ========================================
// КОМПОНЕНТЫ - ТАБЫ
// ========================================

/**
 * Инициализация табов
 */
function initTabs() {
  document.querySelectorAll('.tabs').forEach(tabContainer => {
    const tabs = tabContainer.querySelectorAll('.tab');
    const contents = tabContainer.parentElement.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        // Убираем активный класс у всех табов
        tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));
        
        // Добавляем активный класс к выбранному табу
        tab.classList.add('active');
        if (contents[index]) {
          contents[index].classList.add('active');
        }
      });
    });
  });
}

// ========================================
// КОМПОНЕНТЫ - ТУЛТИПЫ
// ========================================

/**
 * Инициализация тултипов
 */
function initTooltips() {
  document.querySelectorAll('.tooltip').forEach(tooltip => {
    const content = tooltip.querySelector('.tooltip-content');
    
    if (content) {
      tooltip.addEventListener('mouseenter', () => {
        content.style.opacity = '1';
        content.style.visibility = 'visible';
      });
      
      tooltip.addEventListener('mouseleave', () => {
        content.style.opacity = '0';
        content.style.visibility = 'hidden';
      });
    }
  });
}

// ========================================
// AI АССИСТЕНТ - ОСНОВНОЙ КОМПОНЕНТ
// ========================================

/**
 * Класс AI ассистента
 */
class AIAssistant {
  constructor() {
    this.input = document.querySelector('.ai-input');
    this.sendButton = document.querySelector('.ai-send-btn');
    this.chatContainer = document.querySelector('.ai-chat-container');
    this.isLoading = false;
    
    this.init();
  }
  
  init() {
    if (!this.input || !this.sendButton) return;
    
    // Обработчик отправки
    this.sendButton.addEventListener('click', () => this.sendMessage());
    
    // Отправка по Enter
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    // Автофокус на поле ввода
    this.input.focus();
  }
  
  async sendMessage() {
    const message = this.input.value.trim();
    if (!message || this.isLoading) return;
    
    // Добавляем сообщение пользователя
    this.addMessage(message, 'user');
    this.input.value = '';
    
    // Показываем индикатор загрузки
    this.showLoading();
    
    try {
      // Отправляем запрос к API
      const response = await this.callAIAPI(message);
      
      // Скрываем индикатор загрузки
      this.hideLoading();
      
      // Добавляем ответ AI
      this.addMessage(response.answer, 'ai', response.sources);
      
      // Предлагаем практику
      if (response.practice) {
        this.suggestPractice(response.practice);
      }
      
    } catch (error) {
      console.error('AI API Error:', error);
      this.hideLoading();
      this.addMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'error');
    }
  }
  
  async callAIAPI(message) {
    const response = await fetch('/ai/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ prompt: message })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  }
  
  addMessage(content, type, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ai-message-${type} fade-in`;
    
    let messageHTML = '';
    
    if (type === 'user') {
      messageHTML = `
        <div class="ai-message-content">
          <div class="ai-message-text">${this.escapeHtml(content)}</div>
          <div class="ai-message-time">${this.getCurrentTime()}</div>
        </div>
      `;
    } else if (type === 'ai') {
      messageHTML = `
        <div class="ai-message-content">
          <div class="ai-message-text">${this.formatAIResponse(content)}</div>
          ${sources ? this.formatSources(sources) : ''}
          <div class="ai-message-time">${this.getCurrentTime()}</div>
        </div>
      `;
    } else if (type === 'error') {
      messageHTML = `
        <div class="ai-message-content">
          <div class="ai-message-text text-error">${this.escapeHtml(content)}</div>
          <div class="ai-message-time">${this.getCurrentTime()}</div>
        </div>
      `;
    }
    
    messageDiv.innerHTML = messageHTML;
    this.chatContainer.appendChild(messageDiv);
    
    // Скролл к последнему сообщению
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }
  
  showLoading() {
    this.isLoading = true;
    this.sendButton.disabled = true;
    this.sendButton.innerHTML = '<div class="spinner"></div>';
  }
  
  hideLoading() {
    this.isLoading = false;
    this.sendButton.disabled = false;
    this.sendButton.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
      </svg>
    `;
  }
  
  suggestPractice(practiceData) {
    const practiceDiv = document.createElement('div');
    practiceDiv.className = 'ai-practice-suggestion fade-in';
    practiceDiv.innerHTML = `
      <div class="ai-practice-content">
        <h4>🎯 Практика по теме</h4>
        <p>${practiceData.description}</p>
        <button class="btn btn-primary" onclick="startPractice('${practiceData.topic}')">
          Начать практику
        </button>
      </div>
    `;
    
    this.chatContainer.appendChild(practiceDiv);
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }
  
  formatAIResponse(content) {
    // Простое форматирование Markdown
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  
  formatSources(sources) {
    if (!sources || sources.length === 0) return '';
    
    const sourcesHTML = sources.map(source => 
      `<a href="${source.url}" target="_blank" class="ai-source-link">${source.title}</a>`
    ).join('');
    
    return `<div class="ai-sources">Источники: ${sourcesHTML}</div>`;
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  getCurrentTime() {
    return new Date().toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
}

// ========================================
// РЕШЕНИЕ ЗАДАЧ - КОМПОНЕНТ ПРАКТИКИ
// ========================================

/**
 * Класс для решения задач
 */
class ProblemSolver {
  constructor() {
    this.currentProblem = null;
    this.userAnswers = [];
    this.progress = 0;
    
    this.init();
  }
  
  init() {
    // Инициализация компонента
  }
  
  async startPractice(topic) {
    try {
      // Получаем задачи по теме
      const problems = await this.getProblemsByTopic(topic);
      
      if (problems.length === 0) {
        this.showMessage('Задачи по данной теме не найдены', 'warning');
        return;
      }
      
      // Показываем первую задачу
      this.showProblem(problems[0]);
      
    } catch (error) {
      console.error('Error starting practice:', error);
      this.showMessage('Ошибка при загрузке задач', 'error');
    }
  }
  
  async getProblemsByTopic(topic) {
    const response = await fetch(`/ai/api/problems/?topic=${encodeURIComponent(topic)}`, {
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data.problems || [];
  }
  
  showProblem(problem) {
    this.currentProblem = problem;
    
    const problemContainer = document.querySelector('.problem-container');
    if (!problemContainer) return;
    
    problemContainer.innerHTML = `
      <div class="problem-card card fade-in">
        <div class="problem-header">
          <h3>Задача ${problem.id}</h3>
          <span class="badge badge-primary">${problem.subject}</span>
        </div>
        <div class="problem-content">
          <p>${problem.text}</p>
          ${problem.image ? `<img src="${problem.image}" alt="Изображение к задаче" class="problem-image">` : ''}
        </div>
        <div class="problem-options">
          ${this.renderOptions(problem.options)}
        </div>
        <div class="problem-actions">
          <button class="btn btn-primary" onclick="problemSolver.submitAnswer()">
            Проверить ответ
          </button>
          <button class="btn btn-secondary" onclick="problemSolver.showHint()">
            Подсказка
          </button>
        </div>
      </div>
    `;
  }
  
  renderOptions(options) {
    if (!options || options.length === 0) return '';
    
    return options.map((option, index) => `
      <label class="problem-option">
        <input type="radio" name="answer" value="${index}" class="problem-radio">
        <span class="option-text">${option}</span>
      </label>
    `).join('');
  }
  
  async submitAnswer() {
    const selectedAnswer = document.querySelector('input[name="answer"]:checked');
    
    if (!selectedAnswer) {
      this.showMessage('Выберите ответ', 'warning');
      return;
    }
    
    const answer = parseInt(selectedAnswer.value);
    const isCorrect = await this.checkAnswer(answer);
    
    if (isCorrect) {
      this.showMessage('Правильно! 🎉', 'success');
      this.progress += 1;
      this.updateProgress();
      
      // Переход к следующей задаче
      setTimeout(() => {
        this.nextProblem();
      }, 1500);
    } else {
      this.showMessage('Неправильно. Попробуйте еще раз!', 'error');
    }
  }
  
  async checkAnswer(answer) {
    try {
      const response = await fetch('/ai/api/problems/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
          problem_id: this.currentProblem.id,
          answer: answer
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      // Обновляем прогресс пользователя
      if (result.is_correct) {
        this.updateUserProgress(this.currentProblem.topic || 'general', true);
      }
      
      return result.is_correct;
      
    } catch (error) {
      console.error('Error checking answer:', error);
      return false;
    }
  }
  
  async updateUserProgress(subject, isCorrect) {
    try {
      const response = await fetch('/ai/api/user/profile/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
          action: 'solve_problem',
          problem_id: this.currentProblem.id,
          is_correct: isCorrect,
          subject: subject
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          // Обновляем UI с новым прогрессом
          this.updateProgressUI(result);
        }
      }
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  }
  
  updateProgressUI(progressData) {
    // Обновляем отображение прогресса
    const progressElement = document.querySelector('.user-progress');
    if (progressElement && progressData.new_level) {
      progressElement.innerHTML = `
        <div class="progress-info">
          <span class="level">Уровень ${progressData.new_level}</span>
          <span class="xp">XP: ${progressData.new_xp}</span>
          <span class="streak">Серия: ${progressData.streak}</span>
        </div>
      `;
    }
  }
  
  showHint() {
    if (!this.currentProblem.hint) {
      this.showMessage('Подсказка недоступна для этой задачи', 'info');
      return;
    }
    
    this.showMessage(`💡 Подсказка: ${this.currentProblem.hint}`, 'info');
  }
  
  async nextProblem() {
    // Получаем следующую задачу
    const nextProblem = await this.getNextProblem();
    
    if (nextProblem) {
      this.showProblem(nextProblem);
    } else {
      this.showPracticeComplete();
    }
  }
  
  async getNextProblem() {
    // Логика получения следующей задачи
    return null;
  }
  
  showPracticeComplete() {
    const problemContainer = document.querySelector('.problem-container');
    if (!problemContainer) return;
    
    problemContainer.innerHTML = `
      <div class="practice-complete card text-center fade-in">
        <h3>🎉 Практика завершена!</h3>
        <p>Вы решили ${this.progress} задач</p>
        <div class="practice-actions">
          <button class="btn btn-primary" onclick="problemSolver.startNewPractice()">
            Новая практика
          </button>
          <button class="btn btn-secondary" onclick="aiAssistant.focus()">
            Задать вопрос ИИ
          </button>
        </div>
      </div>
    `;
  }
  
  updateProgress() {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
      const percentage = (this.progress / 5) * 100; // Предполагаем 5 задач
      progressBar.style.width = `${Math.min(percentage, 100)}%`;
    }
  }
  
  showMessage(message, type = 'info') {
    // Показываем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fade-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Автоматически убираем через 3 секунды
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
}

// ========================================
// ГЕЙМИФИКАЦИЯ И ПРОГРЕСС
// ========================================

/**
 * Класс для управления геймификацией
 */
class GamificationEngine {
  constructor() {
    this.userProfile = null;
    this.achievements = [];
    this.dailyChallenges = [];
    
    this.init();
  }
  
  async init() {
    await this.loadUserProfile();
    this.setupDailyChallenges();
    this.checkAchievements();
  }
  
  async loadUserProfile() {
    try {
      const response = await fetch('/ai/api/user/profile/', {
        headers: {
          'X-CSRFToken': getCSRFToken()
        }
      });
      
      if (response.ok) {
        this.userProfile = await response.json();
        this.updateUI();
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
    }
  }
  
  setupDailyChallenges() {
    this.dailyChallenges = [
      {
        id: 'solve_10_math',
        title: 'Решите 10 задач по математике',
        description: 'Повысьте свой уровень в математике',
        target: 10,
        current: 0,
        reward: 50
      },
      {
        id: 'study_3_topics',
        title: 'Изучите 3 новые темы',
        description: 'Расширьте свои знания',
        target: 3,
        current: 0,
        reward: 30
      },
      {
        id: 'perfect_score',
        title: 'Получите 100% в тесте',
        description: 'Докажите свое мастерство',
        target: 1,
        current: 0,
        reward: 100
      }
    ];
    
    this.renderDailyChallenges();
  }
  
  renderDailyChallenges() {
    const container = document.querySelector('.daily-challenges');
    if (!container) return;
    
    container.innerHTML = this.dailyChallenges.map(challenge => `
      <div class="challenge-card card hover-lift">
        <div class="challenge-header">
          <h4>${challenge.title}</h4>
          <span class="badge badge-primary">+${challenge.reward} XP</span>
        </div>
        <p>${challenge.description}</p>
        <div class="challenge-progress">
          <div class="progress">
            <div class="progress-bar" style="width: ${(challenge.current / challenge.target) * 100}%"></div>
          </div>
          <span class="challenge-stats">${challenge.current}/${challenge.target}</span>
        </div>
      </div>
    `).join('');
  }
  
  checkAchievements() {
    if (!this.userProfile) return;
    
    const newAchievements = [];
    
    // Проверяем различные достижения
    if (this.userProfile.total_problems_solved >= 100) {
      newAchievements.push({
        id: 'problem_solver',
        title: 'Решатель задач',
        description: 'Решили 100 задач',
        icon: '🎯'
      });
    }
    
    if (this.userProfile.streak >= 7) {
      newAchievements.push({
        id: 'week_warrior',
        title: 'Недельный воин',
        description: '7 дней подряд обучения',
        icon: '🔥'
      });
    }
    
    if (this.userProfile.level >= 5) {
      newAchievements.push({
        id: 'expert',
        title: 'Эксперт ЕГЭ',
        description: 'Достигли 5 уровня',
        icon: '👑'
      });
    }
    
    // Показываем новые достижения
    newAchievements.forEach(achievement => {
      this.showAchievement(achievement);
    });
  }
  
  showAchievement(achievement) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification fade-in';
    notification.innerHTML = `
      <div class="achievement-content">
        <div class="achievement-icon">${achievement.icon}</div>
        <div class="achievement-info">
          <h4>${achievement.title}</h4>
          <p>${achievement.description}</p>
        </div>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматически убираем через 5 секунд
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
  
  updateUI() {
    if (!this.userProfile) return;
    
    // Обновляем уровень
    const levelElement = document.querySelector('.user-level');
    if (levelElement) {
      levelElement.textContent = `Уровень ${this.userProfile.level}`;
    }
    
    // Обновляем XP
    const xpElement = document.querySelector('.user-xp');
    if (xpElement) {
      xpElement.textContent = `${this.userProfile.xp} XP`;
    }
    
    // Обновляем прогресс до следующего уровня
    const progressElement = document.querySelector('.level-progress');
    if (progressElement) {
      const progress = (this.userProfile.xp % 1000) / 10;
      progressElement.style.width = `${progress}%`;
    }
  }
}

// ========================================
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ========================================

document.addEventListener('DOMContentLoaded', function() {
  // Инициализируем все компоненты
  initButtons();
  initInputs();
  initTabs();
  initTooltips();
  animateOnScroll();
  
  // Инициализируем AI ассистента
  window.aiAssistant = new AIAssistant();
  
  // Инициализируем решатель задач
  window.problemSolver = new ProblemSolver();
  
  // Инициализируем геймификацию
  window.gamification = new GamificationEngine();
  
  // Инициализируем модальные окна
  document.querySelectorAll('[data-modal]').forEach(modalTrigger => {
    const modalId = modalTrigger.dataset.modal;
    const modal = new Modal(modalId);
    
    modalTrigger.addEventListener('click', () => modal.open());
  });
  
  console.log('🚀 ExamFlow 2.0 инициализирован!');
});

// ========================================
// ГЛОБАЛЬНЫЕ ФУНКЦИИ ДЛЯ HTML
// ========================================

/**
 * Глобальная функция для начала практики
 */
window.startPractice = function(topic) {
  if (window.problemSolver) {
    window.problemSolver.startPractice(topic);
  }
};

/**
 * Глобальная функция для фокуса на AI ассистенте
 */
window.focusAI = function() {
  const aiInput = document.querySelector('.ai-input');
  if (aiInput) {
    aiInput.focus();
  }
};

// ========================================
// КОНЕЦ EXAMFLOW 2.0 JAVASCRIPT
// ========================================
