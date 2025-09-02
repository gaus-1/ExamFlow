/* ========================================
   EXAMFLOW 2.0 - СОВРЕМЕННЫЙ JAVASCRIPT
   Версия: 2.9 - Исправлены ошибки дублирования
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
    console.log('🔧 Создаем AI ассистента...');
    
    this.input = document.querySelector('.ai-input');
    this.sendButton = document.querySelector('.ai-send-btn');
    this.chatContainer = document.querySelector('.ai-chat-container');
    this.isLoading = false;
    
    console.log('🔍 Найденные элементы:', {
      input: this.input,
      sendButton: this.sendButton,
      chatContainer: this.chatContainer
    });
    
    this.init();
  }
  
  init() {
    console.log('🔧 Инициализируем AI ассистента...');
    
    if (!this.input || !this.sendButton) {
      console.error('❌ Не найдены необходимые элементы для AI ассистента');
      return;
    }
    
    console.log('✅ Элементы найдены, добавляем обработчики событий...');
    
    // Обработчик отправки
    this.sendButton.addEventListener('click', () => {
      console.log('🖱️ Клик по кнопке отправки');
      this.sendMessage();
    });
    
    // Отправка по Enter
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        console.log('⌨️ Нажата клавиша Enter');
        this.sendMessage();
      }
    });
    
    // Автофокус на поле ввода
    this.input.focus();
    console.log('✅ AI ассистент инициализирован');
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
      if (response.answer && typeof response.answer === 'string' && response.answer.trim()) {
        this.addMessage(response.answer, 'ai', response.sources);
      } else {
        console.error('AI Response missing answer or invalid format:', response);
        this.addMessage('Извините, произошла ошибка при получении ответа от ИИ. Попробуйте переформулировать вопрос.', 'error');
      }
      
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
      
      // Проверяем структуру ответа
      if (!data.answer) {
        console.error('AI API Response missing answer field:', data);
        throw new Error('Неправильный формат ответа от сервера');
      }
      
      return data;
      
    } catch (error) {
      console.error('AI API Call Error:', error);
      throw error;
    }
  }
  
  addMessage(content, type, sources = null) {
    // Проверяем, что content существует и не пустой
    if (!content || (typeof content === 'string' && !content.trim())) {
      console.error('addMessage: content is undefined, null or empty:', content);
      content = 'Сообщение недоступно';
    }
    
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
    // Проверяем, что content существует и является строкой
    if (!content || typeof content !== 'string' || !content.trim()) {
      console.warn('AI Response content is not a valid string:', content);
      return 'Извините, произошла ошибка при форматировании ответа.';
    }
    
    try {
      // Простое форматирование Markdown
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    } catch (error) {
      console.error('Error formatting AI response:', error);
      return this.escapeHtml(content);
    }
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

// Геймификация перенесена в отдельный файл gamification.js

// ========================================
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ========================================

console.log('📄 JavaScript файл загружен!');

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔍 Начинаем инициализацию ExamFlow 2.0...');
  
  try {
    // Инициализируем все компоненты
    console.log('🔧 Инициализируем компоненты...');
    initButtons();
    initInputs();
    initTabs();
    initTooltips();
    animateOnScroll();
    
    // Инициализируем AI ассистента
    console.log('🤖 Инициализируем AI ассистента...');
    window.aiAssistant = new AIAssistant();
    console.log('✅ AI ассистент инициализирован:', window.aiAssistant);
    
    // Инициализируем решатель задач
    console.log('🧮 Инициализируем решатель задач...');
    window.problemSolver = new ProblemSolver();
    
    // Инициализируем геймификацию
    console.log('🏆 Инициализируем геймификацию...');
    // Геймификация инициализируется в gamification.js
    
    // Инициализируем модальные окна
    document.querySelectorAll('[data-modal]').forEach(modalTrigger => {
      const modalId = modalTrigger.dataset.modal;
      const modal = new Modal(modalId);
      
      modalTrigger.addEventListener('click', () => modal.open());
    });
    
    console.log('🚀 ExamFlow 2.0 инициализирован!');
  } catch (error) {
    console.error('❌ Ошибка при инициализации ExamFlow 2.0:', error);
  }
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
