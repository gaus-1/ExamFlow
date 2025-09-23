/**
 * 🚀 ExamFlow - Основной JavaScript модуль
 * Современная интерактивность для образовательной платформы
 * ES2025+ стандарты с современными API
 */

class ExamFlowApp {
  #isLoading = false;  // Приватное поле
  #aiChat = null;
  #intersectionObserver = null;
  #abortController = new AbortController();

  constructor() {
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setupIntersectionObserver();
    this.setupKeyboardNavigation();
    this.initializeComponents();
  }

  // ===== НАСТРОЙКА СОБЫТИЙ =====
  setupEventListeners() {
    // AI интерфейс
    const aiInput = document.getElementById('aiInput');
    const aiSendBtn = document.querySelector('.ai-send-btn');
    
    if (aiInput) {
      aiInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendAIQuery();
        }
      });
      
      // Автоматическое изменение размера
      aiInput.addEventListener('input', this.autoResizeInput.bind(this));
    }
    
    if (aiSendBtn) {
      aiSendBtn.addEventListener('click', () => this.sendAIQuery());
    }

    // Быстрые вопросы
    document.querySelectorAll('.ai-suggestion').forEach(btn => {
      btn.addEventListener('click', () => {
        const question = btn.textContent.trim();
        this.askQuestion(question);
      });
    });

    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = anchor.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });

    // Мобильное меню
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileToggle) {
      mobileToggle.addEventListener('click', this.toggleMobileMenu.bind(this));
    }

    // Закрытие мобильного меню при клике вне его
    document.addEventListener('click', (e) => {
      const mobileMenu = document.getElementById('mobileMenuOverlay');
      const toggle = document.querySelector('.mobile-menu-toggle');
      
      if (mobileMenu && mobileMenu.classList.contains('active') && 
          !mobileMenu.contains(e.target) && !toggle.contains(e.target)) {
        this.toggleMobileMenu();
      }
    });
  }

  // ===== AI ФУНКЦИОНАЛЬНОСТЬ =====
  async sendAIQuery() {
    const input = document.getElementById('aiInput');
    const chat = document.getElementById('aiChat');
    
    if (!input || !input.value.trim() || this.#isLoading) return;
    
    const question = input.value.trim();
    input.value = '';
    this.#isLoading = true;
    
    // Показываем чат если скрыт
    if (chat) {
      chat.style.display = 'block';
    }
    
    // Добавляем вопрос пользователя
    this.addMessage('user', question);
    
    // Показываем индикатор загрузки
    const loadingId = this.addMessage('assistant', 'Анализирую ваш вопрос...', true);
    
    try {
      // Совместимость: пробуем модульный эндпоинт /ai/api/ (app ai) и core-эндпоинт /core/ai/api/
      const response = await fetch('/ai/api/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({ prompt: question, query: question })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      // Удаляем индикатор загрузки
      this.removeMessage(loadingId);
      
      if (data.answer) {
        this.addMessage('assistant', data.answer);
        
        // Добавляем источники если есть
        if (data.sources && data.sources.length > 0) {
          const sourcesText = '📚 Источники:\n' + data.sources.slice(0, 3).join('\n');
          this.addMessage('assistant', sourcesText, false, 'sources');
        }
      } else if (data.error) {
        this.addMessage('assistant', `❌ Ошибка: ${data.error}`);
      } else {
        this.addMessage('assistant', 'Извините, не удалось получить ответ. Попробуйте переформулировать вопрос.');
      }
      
    } catch (error) {
      console.error('AI API Error:', error);
      this.removeMessage(loadingId);
      
      // Пробуем экстренный API
      try {
        console.log('🚨 Пробуем экстренный AI API...');
        const emergencyResponse = await fetch('/ai/emergency/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify({ prompt: question, query: question })
        });
        
        if (emergencyResponse.ok) {
          const emergencyData = await emergencyResponse.json();
          if (emergencyData.answer) {
            this.addMessage('assistant', `🚨 ${emergencyData.answer}`);
            
            if (emergencyData.sources && emergencyData.sources.length > 0) {
              const sourcesText = '📚 Источники:\n' + emergencyData.sources.slice(0, 3).map(s => s.title).join('\n');
              this.addMessage('assistant', sourcesText, false, 'sources');
            }
          } else {
            this.addMessage('assistant', '❌ Экстренный сервис также недоступен. Попробуйте позже.');
          }
        } else {
          // Третий уровень fallback
          try {
            console.log('🚨 Пробуем fallback AI API...');
            const fallbackResponse = await fetch('/fallback/ai/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
              },
              body: JSON.stringify({ prompt: question, query: question })
            });
            
            if (fallbackResponse.ok) {
              const fallbackData = await fallbackResponse.json();
              this.addMessage('assistant', `🔧 ${fallbackData.answer || 'Fallback ответ получен'}`);
            } else {
              this.addMessage('assistant', '❌ Произошла ошибка соединения. Попробуйте позже.');
            }
          } catch (fallbackError) {
            this.addMessage('assistant', '❌ Произошла ошибка соединения. Попробуйте позже.');
          }
        }
      } catch (emergencyError) {
        console.error('Emergency AI API Error:', emergencyError);
        this.addMessage('assistant', '❌ Все сервисы ИИ временно недоступны. Попробуйте позже или воспользуйтесь материалами ФИПИ.');
      }
    } finally {
      this.#isLoading = false;
    }
  }

  askQuestion(question) {
    const input = document.getElementById('aiInput');
    if (input) {
      input.value = question;
      input.focus();
      
      // Небольшая задержка для UX
      setTimeout(() => {
        this.sendAIQuery();
      }, 200);
    }
  }

  addMessage(type, text, isLoading = false, messageType = 'default') {
    const chat = document.getElementById('aiChat');
    if (!chat) return null;
    
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `ai-message ${type} ${messageType}`;
    
    if (isLoading) {
      messageDiv.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="animate-pulse">🤖</div>
          <span class="loading-text">${text}</span>
          <div class="loading-dots">
            <span>.</span><span>.</span><span>.</span>
          </div>
        </div>
      `;
    } else {
      const icon = type === 'user' ? '👤' : '🤖';
      const formattedText = this.formatMessage(text);
      
      messageDiv.innerHTML = `
        <div class="message-header">
          <span class="message-icon">${icon}</span>
          <span class="message-type">${type === 'user' ? 'Вы' : 'ИИ-ассистент'}</span>
        </div>
        <div class="message-content">${formattedText}</div>
      `;
    }
    
    chat.appendChild(messageDiv);
    
    // Плавная анимация появления
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    requestAnimationFrame(() => {
      messageDiv.style.transition = 'all 0.3s ease-out';
      messageDiv.style.opacity = '1';
      messageDiv.style.transform = 'translateY(0)';
    });
    
    // Прокрутка к новому сообщению
    setTimeout(() => {
      messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
    
    return messageId;
  }

  removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
      message.style.transition = 'all 0.2s ease-out';
      message.style.opacity = '0';
      message.style.transform = 'translateY(-10px)';
      
      setTimeout(() => {
        message.remove();
      }, 200);
    }
  }

  formatMessage(text) {
    // Простое форматирование текста
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  // ===== УТИЛИТЫ =====
  autoResizeInput(e) {
    const input = e.target;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  }

  getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    
    // Fallback: поиск в мета-тегах
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    return csrfMeta ? csrfMeta.getAttribute('content') : '';
  }

  // ===== МОБИЛЬНОЕ МЕНЮ =====
  toggleMobileMenu() {
    const overlay = document.getElementById('mobileMenuOverlay');
    if (overlay) {
      overlay.classList.toggle('active');
      
      // Блокируем прокрутку body при открытом меню
      if (overlay.classList.contains('active')) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }
  }

  // ===== АНИМАЦИИ ПРИ СКРОЛЛЕ =====
  setupIntersectionObserver() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    this.#intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          
          // Добавляем задержку для каскадной анимации
          const delay = Array.from(entry.target.parentNode.children).indexOf(entry.target) * 100;
          entry.target.style.animationDelay = `${delay}ms`;
        }
      });
    }, observerOptions);
    
    // Наблюдаем за карточками и секциями
    document.querySelectorAll('.card, .feature-card, .stat-card').forEach(el => {
      this.#intersectionObserver.observe(el);
    });
  }

  // Очистка ресурсов
  destroy() {
    this.#abortController.abort();
    if (this.#intersectionObserver) {
      this.#intersectionObserver.disconnect();
    }
  }

  // ===== ДОСТУПНОСТЬ =====
  setupKeyboardNavigation() {
    // Отслеживание навигации с клавиатуры для улучшенного фокуса
    let isUsingKeyboard = false;
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        isUsingKeyboard = true;
        document.body.classList.add('using-keyboard');
      }
    });
    
    document.addEventListener('mousedown', () => {
      isUsingKeyboard = false;
      document.body.classList.remove('using-keyboard');
    });

    // Escape для закрытия модальных окон
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const mobileMenu = document.getElementById('mobileMenuOverlay');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
          this.toggleMobileMenu();
        }
      }
    });
  }

  // ===== ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ =====
  initializeComponents() {
    // Инициализация AI чата
    this.#aiChat = document.getElementById('aiChat');
    
    // Инициализация прогресс-баров с анимацией
    this.animateProgressBars();
    
    // Инициализация счетчиков
    this.animateCounters();
  }

  animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const bar = entry.target;
          const width = bar.style.width || bar.getAttribute('data-width') || '0%';
          
          bar.style.width = '0%';
          setTimeout(() => {
            bar.style.width = width;
          }, 200);
        }
      });
    });
    
    progressBars.forEach(bar => observer.observe(bar));
  }

  animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.animateCounter(entry.target);
        }
      });
    });
    
    counters.forEach(counter => observer.observe(counter));
  }

  animateCounter(element) {
    const text = element.textContent;
    const number = parseInt(text.replace(/[^\d]/g, ''));
    
    if (isNaN(number)) return;
    
    const duration = 2000;
    const steps = 60;
    const increment = number / steps;
    let current = 0;
    
    const timer = setInterval(() => {
      current += increment;
      
      if (current >= number) {
        current = number;
        clearInterval(timer);
      }
      
      const suffix = text.replace(/[\d,]/g, '');
      element.textContent = Math.floor(current).toLocaleString() + suffix;
    }, duration / steps);
  }

  // ===== УТИЛИТЫ =====
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-icon">${this.getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">✕</button>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, 5000);
  }

  getNotificationIcon(type) {
    const icons = {
      'info': 'ℹ️',
      'success': '✅',
      'warning': '⚠️',
      'error': '❌'
    };
    return icons[type] || icons.info;
  }

  // ===== ВНЕШНИЕ МЕТОДЫ =====
  focusAI() {
    const aiInput = document.getElementById('aiInput');
    if (aiInput) {
      aiInput.focus();
      aiInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
}

// ===== ГЛОБАЛЬНЫЕ ФУНКЦИИ =====

// Инициализация приложения
let examFlowApp;

document.addEventListener('DOMContentLoaded', () => {
  examFlowApp = new ExamFlowApp();
  console.log('🚀 ExamFlow приложение инициализировано');
});

// Глобальные функции для обратной совместимости
function focusAI() {
  if (examFlowApp) {
    examFlowApp.focusAI();
  }
}

function sendAIQuery() {
  if (examFlowApp) {
    examFlowApp.sendAIQuery();
  }
}

function askQuestion(question) {
  if (examFlowApp) {
    examFlowApp.askQuestion(question);
  }
}

function toggleMobileMenu() {
  if (examFlowApp) {
    examFlowApp.toggleMobileMenu();
  }
}

// ===== ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ =====

// Throttle функция для оптимизации производительности
function throttle(func, wait) {
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

// Debounce функция для поиска
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

// Проверка поддержки современных функций
function checkBrowserSupport() {
  const features = {
    fetch: typeof fetch !== 'undefined',
    intersectionObserver: 'IntersectionObserver' in window,
    customProperties: CSS.supports('color', 'var(--test)'),
    grid: CSS.supports('display', 'grid'),
    flexbox: CSS.supports('display', 'flex')
  };
  
  console.log('🔍 Поддержка браузера:', features);
  
  // Показываем предупреждение для старых браузеров
  const unsupported = Object.entries(features).filter(([key, value]) => !value);
  if (unsupported.length > 0) {
    console.warn('⚠️ Некоторые функции могут работать некорректно:', unsupported);
  }
  
  return features;
}

// Инициализация проверки браузера
document.addEventListener('DOMContentLoaded', checkBrowserSupport);

// ===== СЕРВИС ВОРКЕР (для PWA функциональности) =====
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/sw.js')
      .then((registration) => {
        console.log('🔧 Service Worker зарегистрирован:', registration.scope);
      })
      .catch((error) => {
        console.log('❌ Ошибка регистрации Service Worker:', error);
      });
  });
}
