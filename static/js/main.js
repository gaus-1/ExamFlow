/**
 * 🚀 ExamFlow 2.0 - Главный JavaScript модуль
 * 
 * Современный ES6+ код с модульной архитектурой
 * Включает все основные функции платформы
 */

// ===== КОНФИГУРАЦИЯ =====
const CONFIG = {
    API_BASE_URL: '/api/',
    ROUTES: {
        TASKS: '/tasks/',
        TOPICS: '/topics/',
        PRACTICE: '/practice/',
        THEORY: '/theory/',
        AI_CHAT: '/ai/chat/',
        SUBJECTS: '/subjects/'
    },
    ANIMATION_DURATION: 300,
    NOTIFICATION_DURATION: 5000,
    THEME_CHECK_INTERVAL: 5 * 60 * 1000, // 5 минут
    STORAGE_KEYS: {
        USER_DATA: 'examflow_user_data',
        THEME: 'examflow-theme',
        BEHAVIOR: 'examflow_user_behavior'
    }
};

// ===== УТИЛИТЫ =====
class Utils {
    /**
     * Показывает уведомление пользователю
     * @param {string} message - Сообщение
     * @param {string} type - Тип уведомления (info, success, warning, error)
     * @param {number} duration - Длительность показа в мс
     */
    static showNotification(message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Закрыть">&times;</button>
            </div>
        `;
        
        // Стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            font-family: var(--font-primary);
        `;
        
        document.body.appendChild(notification);
        
        // Анимация появления
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
        });
        
        // Обработчик закрытия
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        // Автоматическое скрытие
        setTimeout(() => this.hideNotification(notification), duration);
    }
    
    static hideNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }
    
    static getNotificationIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        return icons[type] || icons.info;
    }
    
    static getNotificationColor(type) {
        const colors = {
            info: '#3B82F6',
            success: '#10B981',
            warning: '#F59E0B',
            error: '#EF4444'
        };
        return colors[type] || colors.info;
    }
    
    /**
     * Выполняет навигацию с проверкой
     * @param {string} url - URL для перехода
     * @param {boolean} newTab - Открыть в новой вкладке
     */
    static navigate(url, newTab = false) {
        try {
            if (newTab) {
                window.open(url, '_blank');
            } else {
                window.location.href = url;
            }
        } catch (error) {
            console.error('Navigation error:', error);
            this.showNotification('Ошибка навигации', 'error');
        }
    }
    
    /**
     * Дебаунс функция для оптимизации
     * @param {Function} func - Функция для выполнения
     * @param {number} wait - Время ожидания в мс
     * @returns {Function} - Дебаунсированная функция
     */
    static debounce(func, wait) {
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
     * Получает CSRF токен
     * @returns {string} - CSRF токен
     */
    static getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    /**
     * Проверяет, является ли устройство мобильным
     * @returns {boolean} - true если мобильное устройство
     */
    static isMobile() {
        return window.innerWidth <= 768;
    }
    
    /**
     * Анимация появления элемента
     * @param {HTMLElement} element - Элемент для анимации
     * @param {string} animation - Тип анимации
     */
    static animateElement(element, animation = 'fadeInUp') {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        
        requestAnimationFrame(() => {
            element.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        });
    }
}

// ===== МЕНЕДЖЕР ТЕМ =====
class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.init();
    }
    
    init() {
        this.loadTheme();
        this.setupThemeToggle();
        this.setupAutoTheme();
    }
    
    loadTheme() {
        const savedTheme = localStorage.getItem(CONFIG.STORAGE_KEYS.THEME);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const shouldBeDark = savedTheme ? savedTheme === 'dark' : prefersDark;
        
        this.setTheme(shouldBeDark ? 'dark' : 'light');
    }
    
    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
        localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, theme);
        this.updateThemeColor();
    }
    
    updateThemeColor() {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        metaThemeColor.content = this.currentTheme === 'dark' ? '#1a1a1a' : '#faf7f0';
    }
    
    setupThemeToggle() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
                this.updateToggleIcon(toggle, newTheme);
            });
        }
    }
    
    updateToggleIcon(toggle, theme) {
        toggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
        toggle.style.transform = 'scale(1.2) rotate(180deg)';
        setTimeout(() => {
            toggle.style.transform = 'scale(1) rotate(0deg)';
        }, CONFIG.ANIMATION_DURATION);
    }
    
    setupAutoTheme() {
        // Проверяем время и переключаем тему автоматически
        const checkTime = () => {
            const hour = new Date().getHours();
            const shouldBeDark = hour < 9 || hour >= 21;
            const newTheme = shouldBeDark ? 'dark' : 'light';
            
            if (newTheme !== this.currentTheme) {
                this.setTheme(newTheme);
                Utils.showNotification(
                    `Переключено на ${shouldBeDark ? 'темную' : 'светлую'} тему`,
                    'info'
                );
            }
        };
        
        checkTime();
        setInterval(checkTime, CONFIG.THEME_CHECK_INTERVAL);
    }
}

// ===== МЕНЕДЖЕР АНИМАЦИЙ =====
class AnimationManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupScrollAnimations();
        this.setupPageLoadAnimations();
        this.setupAccordions();
    }
    
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(el => observer.observe(el));
    }
    
    setupPageLoadAnimations() {
        const elements = document.querySelectorAll('.ai-chat-container, .fipi-tab, .accordion, .gamification');
        
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                Utils.animateElement(element);
            }, index * 200);
        });
    }
    
    setupAccordions() {
        const accordionItems = document.querySelectorAll('.accordion-item');
        
        accordionItems.forEach(item => {
            const header = item.querySelector('.accordion-header');
            const content = item.querySelector('.accordion-content');
            
            if (header && content) {
                header.addEventListener('click', () => {
                    const isActive = item.classList.contains('active');
                    
                    // Закрываем все аккордеоны
                    accordionItems.forEach(otherItem => {
                        otherItem.classList.remove('active');
                        const otherContent = otherItem.querySelector('.accordion-content');
                        if (otherContent) {
                            otherContent.style.maxHeight = '0';
                        }
                    });
                    
                    // Открываем текущий, если он был закрыт
                    if (!isActive) {
                        item.classList.add('active');
                        content.style.maxHeight = content.scrollHeight + 'px';
                        
                        // Плавная анимация содержимого
                        content.style.opacity = '0';
                        content.style.transform = 'translateY(-10px)';
                        
                        setTimeout(() => {
                            content.style.transition = 'all 0.3s ease';
                            content.style.opacity = '1';
                            content.style.transform = 'translateY(0)';
                        }, 100);
                    }
                });
            }
        });
    }
}

// ===== МЕНЕДЖЕР МОБИЛЬНОГО МЕНЮ =====
class MobileMenuManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupBurgerMenu();
        this.setupResponsiveHandling();
    }
    
    setupBurgerMenu() {
        const burger = document.getElementById('navbar-burger');
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileClose = document.getElementById('mobile-menu-close');
        
        if (burger && mobileMenu) {
            const toggle = (open) => {
                if (open) {
                    mobileMenu.classList.add('open');
                    burger.setAttribute('aria-expanded', 'true');
                    mobileMenu.setAttribute('aria-hidden', 'false');
                    document.body.classList.add('no-scroll');
                } else {
                    mobileMenu.classList.remove('open');
                    burger.setAttribute('aria-expanded', 'false');
                    mobileMenu.setAttribute('aria-hidden', 'true');
                    document.body.classList.remove('no-scroll');
                }
            };
            
            burger.addEventListener('click', () => toggle(!mobileMenu.classList.contains('open')));
            
            if (mobileClose) {
                mobileClose.addEventListener('click', () => toggle(false));
            }
            
            // Закрытие по клику вне меню
            document.addEventListener('click', (e) => {
                if (!mobileMenu.contains(e.target) && !burger.contains(e.target)) {
                    toggle(false);
                }
            });
        }
    }
    
    setupResponsiveHandling() {
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1024) {
                const mobileMenu = document.getElementById('mobile-menu');
                if (mobileMenu) {
                    mobileMenu.classList.remove('open');
                    document.body.classList.remove('no-scroll');
                }
            }
        });
    }
}

// ===== ОСНОВНЫЕ ФУНКЦИИ EXAMFLOW =====
class ExamFlowCore {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupAI();
        this.setupGamification();
    }
    
    setupEventListeners() {
        // Обработчики для кнопок
        this.addButtonHandlers();
        
        // Обработчики для форм
        this.addFormHandlers();
        
        // Обработчики для навигации
        this.addNavigationHandlers();
    }
    
    addButtonHandlers() {
        // Кнопки "Скоро будет"
        document.querySelectorAll('[onclick*="alert"]').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => {
                Utils.showNotification('Функция будет добавлена в следующем обновлении', 'info');
            });
        });
        
        // Кнопки задач
        document.querySelectorAll('[onclick*="startTask"]').forEach(btn => {
            const taskId = this.extractId(btn, 'data-task-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => this.startTask(taskId));
        });
        
        // Кнопки тем
        document.querySelectorAll('[onclick*="continueTopic"]').forEach(btn => {
            const topicId = this.extractId(btn, 'data-topic-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => this.continueTopic(topicId));
        });
        
        // Кнопки фильтров
        document.querySelectorAll('[onclick*="filterTasks"]').forEach(btn => {
            const difficulty = btn.getAttribute('data-difficulty') || 'all';
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => this.filterTasks(difficulty));
        });
    }
    
    addFormHandlers() {
        // Обработка отправки форм
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('ai-chat-form')) {
                e.preventDefault();
                this.handleAIChat(form);
            }
        });
    }
    
    addNavigationHandlers() {
        // Обработка кликов по ссылкам
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && !link.href.startsWith('http')) {
                // Внутренняя навигация
                e.preventDefault();
                Utils.navigate(link.href);
            }
        });
    }
    
    setupAI() {
        // Инициализация AI чата
        const aiContainer = document.querySelector('.ai-chat-container');
        if (aiContainer) {
            this.setupAIChat(aiContainer);
        }
    }
    
    setupAIChat(container) {
        const input = container.querySelector('.ai-chat-input');
        const submitBtn = container.querySelector('.ai-chat-submit');
        
        if (input && submitBtn) {
            const handleSubmit = () => {
                const message = input.value.trim();
                if (message) {
                    this.sendAIMessage(message);
                    input.value = '';
                }
            };
            
            submitBtn.addEventListener('click', handleSubmit);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                }
            });
        }
    }
    
    setupGamification() {
        // Инициализация геймификации
        if (window.ExamFlowGamification) {
            window.gamification = new window.ExamFlowGamification();
        }
    }
    
    // Основные функции
    startTask(taskId) {
        console.log('Запуск задачи:', taskId);
        Utils.navigate(`${CONFIG.ROUTES.TASKS}${taskId}/`);
    }
    
    continueTopic(topicId) {
        console.log('Продолжение темы:', topicId);
        Utils.navigate(`${CONFIG.ROUTES.TOPICS}${topicId}/continue/`);
    }
    
    filterTasks(difficulty) {
        console.log('Фильтрация задач по сложности:', difficulty);
        this.updateActiveFilterButton(difficulty);
        this.filterTaskCards(difficulty);
    }
    
    updateActiveFilterButton(difficulty) {
        const buttons = document.querySelectorAll('.btn-outline-secondary, .btn-outline-success, .btn-outline-warning, .btn-outline-danger');
        
        buttons.forEach(btn => {
            btn.className = btn.className.replace(/btn-outline-(secondary|success|warning|danger)/g, 'btn-outline-secondary');
        });
        
        const activeButton = event?.target;
        if (activeButton) {
            const difficultyClasses = {
                easy: 'btn-outline-success',
                medium: 'btn-outline-warning',
                hard: 'btn-outline-danger',
                all: 'btn-outline-secondary'
            };
            
            if (difficultyClasses[difficulty]) {
                activeButton.classList.remove('btn-outline-secondary');
                activeButton.classList.add(difficultyClasses[difficulty]);
            }
        }
    }
    
    filterTaskCards(difficulty) {
        const taskCards = document.querySelectorAll('.task-card');
        
        taskCards.forEach(card => {
            const cardDifficulty = card.dataset.difficulty;
            const shouldShow = difficulty === 'all' || cardDifficulty === difficulty;
            
            card.style.display = shouldShow ? 'block' : 'none';
            
            if (shouldShow) {
                Utils.animateElement(card);
            }
        });
    }
    
    async sendAIMessage(message) {
        try {
            Utils.showNotification('AI обрабатывает ваш вопрос...', 'info', 2000);
            
            const response = await fetch(CONFIG.ROUTES.AI_CHAT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Utils.getCSRFToken()
                },
                body: JSON.stringify({ message })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayAIResponse(data.response);
            } else {
                throw new Error('Ошибка API');
            }
        } catch (error) {
            console.error('AI Error:', error);
            Utils.showNotification('Ошибка при обращении к AI', 'error');
        }
    }
    
    displayAIResponse(response) {
        // Создаем элемент ответа
        const responseEl = document.createElement('div');
        responseEl.className = 'ai-response';
        responseEl.innerHTML = `
            <div class="ai-response-content">
                <div class="ai-response-text">${response}</div>
                <div class="ai-response-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        // Добавляем в контейнер
        const container = document.querySelector('.ai-chat-container .ai-responses');
        if (container) {
            container.appendChild(responseEl);
            container.scrollTop = container.scrollHeight;
        }
    }
    
    extractId(element, attribute) {
        return element.getAttribute(attribute) || 
               element.closest(`[${attribute}]`)?.dataset[attribute.replace('data-', '').replace('-', '')] || 
               null;
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 ExamFlow 2.0 инициализируется...');
    
    try {
        // Инициализируем все менеджеры
        window.themeManager = new ThemeManager();
        window.animationManager = new AnimationManager();
        window.mobileMenuManager = new MobileMenuManager();
        window.examFlowCore = new ExamFlowCore();
        
        console.log('✅ ExamFlow 2.0 успешно инициализирован!');
    } catch (error) {
        console.error('❌ Ошибка инициализации ExamFlow:', error);
    }
});

// Экспорт для использования в других модулях
window.ExamFlow = {
    Utils,
    ThemeManager,
    AnimationManager,
    MobileMenuManager,
    ExamFlowCore,
    CONFIG
};
