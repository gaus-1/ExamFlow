/**
 * Современные функции для ExamFlow 2.0
 * Использует ES6+ стандарты и современные подходы
 */

// ===== КОНСТАНТЫ =====
const CONFIG = {
    API_BASE_URL: '/api/',
    ROUTES: {
        TASKS: '/tasks/',
        TOPICS: '/topics/',
        PRACTICE: '/practice/',
        THEORY: '/theory/'
    },
    DIFFICULTY_CLASSES: {
        easy: 'btn-outline-success',
        medium: 'btn-outline-warning', 
        hard: 'btn-outline-danger',
        all: 'btn-outline-secondary'
    }
};

// ===== УТИЛИТЫ =====
const Utils = {
    /**
     * Показывает уведомление пользователю
     * @param {string} message - Сообщение
     * @param {string} type - Тип уведомления (info, success, warning, error)
     */
    showNotification(message, type = 'info') {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Добавляем в контейнер уведомлений
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },

    /**
     * Выполняет навигацию с проверкой
     * @param {string} url - URL для перехода
     * @param {boolean} newTab - Открыть в новой вкладке
     */
    navigate(url, newTab = false) {
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
    },

    /**
     * Дебаунс функция для оптимизации
     * @param {Function} func - Функция для выполнения
     * @param {number} wait - Время ожидания в мс
     * @returns {Function} - Дебаунсированная функция
     */
    debounce(func, wait) {
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
};

// ===== ОСНОВНЫЕ ФУНКЦИИ =====
const ExamFlow = {
    /**
     * Показывает уведомление о скором добавлении функции
     */
    showFeatureComingSoon() {
        Utils.showNotification('Функция будет добавлена в следующем обновлении', 'info');
    },

    /**
     * Запускает задачу
     * @param {string|number} taskId - ID задачи
     */
    startTask(taskId) {
        console.log('Запуск задачи:', taskId);
        const url = `${CONFIG.ROUTES.TASKS}${taskId}/`;
        Utils.navigate(url);
    },

    /**
     * Перезагружает страницу
     */
    reloadPage() {
        location.reload();
    },

    /**
     * Продолжает изучение темы
     * @param {string|number} topicId - ID темы
     */
    continueTopic(topicId) {
        console.log('Продолжение темы:', topicId);
        const url = `${CONFIG.ROUTES.TOPICS}${topicId}/continue/`;
        Utils.navigate(url);
    },

    /**
     * Начинает изучение темы
     * @param {string|number} topicId - ID темы
     */
    startTopic(topicId) {
        console.log('Начало темы:', topicId);
        const url = `${CONFIG.ROUTES.TOPICS}${topicId}/start/`;
        Utils.navigate(url);
    },

    /**
     * Начинает практику по теме
     * @param {string|number} topicId - ID темы
     */
    startPractice(topicId) {
        console.log('Начало практики по теме:', topicId);
        const url = `${CONFIG.ROUTES.PRACTICE}${topicId}/`;
        Utils.navigate(url);
    },

    /**
     * Показывает теорию по теме
     * @param {string|number} topicId - ID темы
     */
    showTheory(topicId) {
        console.log('Показать теорию по теме:', topicId);
        const url = `${CONFIG.ROUTES.THEORY}${topicId}/`;
        Utils.navigate(url);
    },

    /**
     * Фильтрует задачи по сложности
     * @param {string} difficulty - Уровень сложности
     */
    filterTasks(difficulty) {
        console.log('Фильтрация задач по сложности:', difficulty);
        
        // Обновляем активную кнопку
        this.updateActiveFilterButton(difficulty);
        
        // Фильтруем карточки задач
        this.filterTaskCards(difficulty);
    },

    /**
     * Обновляет активную кнопку фильтра
     * @param {string} difficulty - Уровень сложности
     */
    updateActiveFilterButton(difficulty) {
        const buttons = document.querySelectorAll('.btn-outline-secondary, .btn-outline-success, .btn-outline-warning, .btn-outline-danger');
        
        buttons.forEach(btn => {
            // Убираем все классы сложности
            Object.values(CONFIG.DIFFICULTY_CLASSES).forEach(cls => {
                btn.classList.remove(cls);
            });
            // Добавляем базовый класс
            btn.classList.add('btn-outline-secondary');
        });
        
        // Активируем выбранную кнопку
        const activeButton = event?.target;
        if (activeButton && CONFIG.DIFFICULTY_CLASSES[difficulty]) {
            activeButton.classList.remove('btn-outline-secondary');
            activeButton.classList.add(CONFIG.DIFFICULTY_CLASSES[difficulty]);
        }
    },

    /**
     * Фильтрует карточки задач
     * @param {string} difficulty - Уровень сложности
     */
    filterTaskCards(difficulty) {
        const taskCards = document.querySelectorAll('.task-card');
        
        taskCards.forEach(card => {
            const cardDifficulty = card.dataset.difficulty;
            const shouldShow = difficulty === 'all' || cardDifficulty === difficulty;
            
            card.style.display = shouldShow ? 'block' : 'none';
            
            // Добавляем анимацию появления
            if (shouldShow) {
                card.classList.add('fade-in');
            }
        });
    }
};

// ===== ОБРАБОТЧИКИ СОБЫТИЙ =====
const EventHandlers = {
    /**
     * Добавляет обработчики событий для всех интерактивных элементов
     */
    addEventListeners() {
        this.addComingSoonHandlers();
        this.addTaskHandlers();
        this.addTopicHandlers();
        this.addFilterHandlers();
    },

    /**
     * Обработчики для кнопок "Скоро будет"
     */
    addComingSoonHandlers() {
        document.querySelectorAll('[onclick*="alert"]').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', ExamFlow.showFeatureComingSoon);
        });
    },

    /**
     * Обработчики для задач
     */
    addTaskHandlers() {
        document.querySelectorAll('[onclick*="startTask"]').forEach(btn => {
            const taskId = this.extractId(btn, 'data-task-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.startTask(taskId));
        });
    },

    /**
     * Обработчики для тем
     */
    addTopicHandlers() {
        // Продолжение темы
        document.querySelectorAll('[onclick*="continueTopic"]').forEach(btn => {
            const topicId = this.extractId(btn, 'data-topic-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.continueTopic(topicId));
        });

        // Начало темы
        document.querySelectorAll('[onclick*="startTopic"]').forEach(btn => {
            const topicId = this.extractId(btn, 'data-topic-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.startTopic(topicId));
        });

        // Практика
        document.querySelectorAll('[onclick*="startPractice"]').forEach(btn => {
            const topicId = this.extractId(btn, 'data-topic-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.startPractice(topicId));
        });

        // Теория
        document.querySelectorAll('[onclick*="showTheory"]').forEach(btn => {
            const topicId = this.extractId(btn, 'data-topic-id');
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.showTheory(topicId));
        });
    },

    /**
     * Обработчики для фильтров
     */
    addFilterHandlers() {
        document.querySelectorAll('[onclick*="filterTasks"]').forEach(btn => {
            const difficulty = btn.getAttribute('data-difficulty') || 'all';
            btn.removeAttribute('onclick');
            btn.addEventListener('click', () => ExamFlow.filterTasks(difficulty));
        });
    },

    /**
     * Извлекает ID из элемента или его родителя
     * @param {HTMLElement} element - Элемент
     * @param {string} attribute - Атрибут с ID
     * @returns {string|null} - ID или null
     */
    extractId(element, attribute) {
        return element.getAttribute(attribute) || 
               element.closest(`[${attribute}]`)?.dataset[attribute.replace('data-', '').replace('-', '')] || 
               null;
    }
};

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('ExamFlow 2.0 Core Functions initialized');
    EventHandlers.addEventListeners();
});

// Экспорт для использования в других модулях
window.ExamFlow = ExamFlow;
window.Utils = Utils;