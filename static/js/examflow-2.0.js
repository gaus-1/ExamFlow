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
  // Сначала ищем в скрытом поле
  const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (token) {
    console.log('CSRF токен найден в скрытом поле');
    return token;
  }
  
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
  
  if (cookieValue) {
    console.log('CSRF токен найден в cookies');
  } else {
    console.warn('CSRF токен не найден!');
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
    
    // Отправляем сообщение пользователя
    this.addMessage(message, 'user');
    
    // Показываем индикатор загрузки
    this.showLoading();
    
    // Отправляем запрос к API
    try {
      const response = await this.callAIAPI(message);
      
      // Скрываем индикатор загрузки
      this.hideLoading();
      
      // Добавляем ответ ИИ
      this.addMessage(response.response, 'ai', response.sources);
      
      // Генерируем событие для геймификации
      document.dispatchEvent(new CustomEvent('aiQuestionAsked', {
        detail: { question: message }
      }));
      
    } catch (error) {
      this.hideLoading();
      this.addMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'error');
      console.error('AI API Error:', error);
    }
  }
  
  async callAIAPI(message) {
    try {
      console.log('Отправляем запрос к AI API:', message);
      
      const response = await fetch('/ai/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ prompt: message })
      });
      
      console.log('AI API Response:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('AI API Error Response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('AI API Success Response:', data);
      return data;
      
    } catch (error) {
      console.error('AI API Call Error:', error);
      throw error;
    }
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

/**
 * Геймификация ExamFlow 2.0
 */
class ExamFlowGamification {
  constructor() {
    this.userData = this.loadUserData();
    this.init();
  }
  
  init() {
    this.updateProgressDisplay();
    this.updateAchievementsDisplay();
    this.setupEventListeners();
  }
  
  loadUserData() {
    const saved = localStorage.getItem('examflow_user_data');
    if (saved) {
      return JSON.parse(saved);
    }
    
    // Данные по умолчанию для демонстрации
    return {
      level: 5,
      xp: 750,
      totalXp: 1250,
      solvedTasks: 47,
      achievements: 12,
      achievementsList: [
        { id: 'first_task', name: 'Первая задача', icon: '🎯', earned: true },
        { id: 'streak_5', name: 'Серия успехов', icon: '🔥', earned: true },
        { id: 'ai_questions_10', name: 'Любознательный', icon: '🧠', earned: true },
        { id: 'speed_30s', name: 'Скорость', icon: '⚡', earned: true },
        { id: 'master_100', name: 'Мастер', icon: '🏆', earned: false },
        { id: 'expert_level_10', name: 'Эксперт', icon: '🌟', earned: false },
        { id: 'all_subjects', name: 'Эрудит', icon: '📚', earned: false },
        { id: 'all_achievements', name: 'Легенда', icon: '💎', earned: false }
      ]
    };
  }
  
  saveUserData() {
    localStorage.setItem('examflow_user_data', JSON.stringify(this.userData));
  }
  
  addXP(amount, reason = '') {
    const oldLevel = this.userData.level;
    this.userData.xp += amount;
    this.userData.totalXp += amount;
    
    // Проверяем повышение уровня
    const newLevel = this.calculateLevel(this.userData.totalXp);
    if (newLevel > oldLevel) {
      this.userData.level = newLevel;
      this.showLevelUpNotification(newLevel);
    }
    
    this.saveUserData();
    this.updateProgressDisplay();
    
    // Показываем уведомление о получении XP
    this.showXPNotification(amount, reason);
  }
  
  calculateLevel(totalXp) {
    // Формула: каждый уровень требует level * 200 XP
    return Math.floor(Math.sqrt(totalXp / 200)) + 1;
  }
  
  getLevelInfo(level) {
    const levelNames = {
      1: 'Новичок',
      2: 'Ученик',
      3: 'Студент',
      4: 'Знаток',
      5: 'Опытный ученик',
      6: 'Специалист',
      7: 'Мастер',
      8: 'Эксперт',
      9: 'Гуру',
      10: 'Легенда'
    };
    
    return {
      name: levelNames[level] || `Уровень ${level}`,
      xpRequired: level * level * 200,
      xpForNext: (level + 1) * (level + 1) * 200
    };
  }
  
  updateProgressDisplay() {
    const levelInfo = this.getLevelInfo(this.userData.level);
    const progressPercent = ((this.userData.totalXp - levelInfo.xpRequired) / (levelInfo.xpForNext - levelInfo.xpRequired)) * 100;
    
    // Обновляем отображение уровня
    const levelBadge = document.querySelector('.level-badge');
    const levelTitle = document.querySelector('.level-title');
    const levelSubtitle = document.querySelector('.level-subtitle');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-label span:last-child');
    
    if (levelBadge) levelBadge.textContent = `Уровень ${this.userData.level}`;
    if (levelTitle) levelTitle.textContent = levelInfo.name;
    if (levelSubtitle) levelSubtitle.textContent = `До следующего уровня: ${levelInfo.xpForNext - this.userData.totalXp} XP`;
    if (progressBar) progressBar.style.width = `${Math.min(progressPercent, 100)}%`;
    if (progressText) progressText.textContent = `${this.userData.totalXp} / ${levelInfo.xpForNext} XP`;
    
    // Обновляем статистику
    const xpStat = document.querySelector('.stats-grid .stat-item:nth-child(1) .stat-number');
    const tasksStat = document.querySelector('.stats-grid .stat-item:nth-child(2) .stat-number');
    const achievementsStat = document.querySelector('.stats-grid .stat-item:nth-child(3) .stat-number');
    
    if (xpStat) xpStat.textContent = this.userData.totalXp.toLocaleString();
    if (tasksStat) tasksStat.textContent = this.userData.solvedTasks;
    if (achievementsStat) achievementsStat.textContent = this.userData.achievements;
  }
  
  updateAchievementsDisplay() {
    const achievementsGrid = document.querySelector('.achievements-grid');
    if (!achievementsGrid) return;
    
    achievementsGrid.innerHTML = '';
    
    this.userData.achievementsList.forEach(achievement => {
      const achievementEl = document.createElement('div');
      achievementEl.className = `achievement-item text-center p-4 rounded-lg ${
        achievement.earned 
          ? 'bg-success/10 border border-success/20' 
          : 'bg-gray-100 border border-gray-200 opacity-50'
      }`;
      
      achievementEl.innerHTML = `
        <div class="achievement-icon text-3xl mb-2">${achievement.icon}</div>
        <div class="achievement-title text-sm font-medium">${achievement.name}</div>
        <div class="achievement-desc text-xs text-muted">${this.getAchievementDescription(achievement.id)}</div>
      `;
      
      achievementsGrid.appendChild(achievementEl);
    });
  }
  
  getAchievementDescription(achievementId) {
    const descriptions = {
      'first_task': 'Решите первую задачу',
      'streak_5': '5 правильных ответов подряд',
      'ai_questions_10': 'Задайте 10 вопросов ИИ',
      'speed_30s': 'Решите задачу за 30 секунд',
      'master_100': 'Решите 100 задач',
      'expert_level_10': 'Достигните 10 уровня',
      'all_subjects': 'Изучите все предметы',
      'all_achievements': 'Получите все достижения'
    };
    
    return descriptions[achievementId] || 'Неизвестное достижение';
  }
  
  checkAchievements() {
    let newAchievements = 0;
    
    // Проверяем достижения
    if (this.userData.solvedTasks >= 1 && !this.hasAchievement('first_task')) {
      this.unlockAchievement('first_task');
      newAchievements++;
    }
    
    if (this.userData.solvedTasks >= 100 && !this.hasAchievement('master_100')) {
      this.unlockAchievement('master_100');
      newAchievements++;
    }
    
    if (this.userData.level >= 10 && !this.hasAchievement('expert_level_10')) {
      this.unlockAchievement('expert_level_10');
      newAchievements++;
    }
    
    if (newAchievements > 0) {
      this.showAchievementNotification(newAchievements);
      this.updateAchievementsDisplay();
    }
  }
  
  hasAchievement(achievementId) {
    const achievement = this.userData.achievementsList.find(a => a.id === achievementId);
    return achievement ? achievement.earned : false;
  }
  
  unlockAchievement(achievementId) {
    const achievement = this.userData.achievementsList.find(a => a.id === achievementId);
    if (achievement && !achievement.earned) {
      achievement.earned = true;
      this.userData.achievements++;
      this.saveUserData();
    }
  }
  
  showXPNotification(amount, reason) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-success text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-slide-in';
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-lg">+${amount} XP</span>
        ${reason ? `<span class="text-sm opacity-90">(${reason})</span>` : ''}
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  showLevelUpNotification(level) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-primary text-white px-6 py-4 rounded-xl shadow-2xl z-50 animate-scale-in';
    notification.innerHTML = `
      <div class="text-center">
        <div class="text-4xl mb-2">🎉</div>
        <div class="text-xl font-bold mb-1">Поздравляем!</div>
        <div class="text-lg">Вы достигли ${level} уровня!</div>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 4000);
  }
  
  showAchievementNotification(count) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 left-4 bg-accent text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-slide-in';
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-lg">🏆</span>
        <span>Получено ${count} новое достижение!</span>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  setupEventListeners() {
    // Слушаем события от AI ассистента
    document.addEventListener('aiQuestionAsked', () => {
      this.addXP(5, 'Вопрос ИИ');
      this.checkAchievements();
    });
    
    // Слушаем события решения задач
    document.addEventListener('taskSolved', (event) => {
      const { correct, time } = event.detail;
      if (correct) {
        this.userData.solvedTasks++;
        this.addXP(20, 'Правильный ответ');
        
        if (time && time < 30) {
          this.addXP(10, 'Быстрый ответ');
        }
      }
      this.checkAchievements();
    });
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

/**
 * Глобальная функция для быстрых вопросов
 */
window.askQuestion = function(question) {
  const aiInput = document.querySelector('.ai-input');
  if (aiInput) {
    aiInput.value = question;
    aiInput.focus();
    
    // Автоматически отправляем вопрос
    const sendButton = document.querySelector('.ai-send-btn');
    if (sendButton) {
      sendButton.click();
    }
  }
};

/**
 * Мобильное меню
 */
window.toggleMobileMenu = function() {
  const overlay = document.getElementById('mobileMenuOverlay');
  const toggle = document.querySelector('.mobile-menu-toggle');
  
  if (overlay && toggle) {
    const isActive = overlay.classList.contains('active');
    
    if (isActive) {
      // Закрываем меню
      overlay.classList.remove('active');
      toggle.classList.remove('active');
      document.body.style.overflow = '';
    } else {
      // Открываем меню
      overlay.classList.add('active');
      toggle.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }
};

/**
 * Закрытие мобильного меню при клике вне его
 */
document.addEventListener('click', function(event) {
  const overlay = document.getElementById('mobileMenuOverlay');
  const toggle = document.querySelector('.mobile-menu-toggle');
  
  if (overlay && toggle && overlay.classList.contains('active')) {
    if (!overlay.contains(event.target) && !toggle.contains(event.target)) {
      toggleMobileMenu();
    }
  }
});

/**
 * Закрытие мобильного меню при нажатии Escape
 */
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    const overlay = document.getElementById('mobileMenuOverlay');
    if (overlay && overlay.classList.contains('active')) {
      toggleMobileMenu();
    }
  }
});

// ========================================
// КОНЕЦ EXAMFLOW 2.0 JAVASCRIPT
// ========================================
