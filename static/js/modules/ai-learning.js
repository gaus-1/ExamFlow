/**
 * 🤖 AI Learning System для ExamFlow
 * 
 * Система машинного обучения на JavaScript для:
 * - Анализа поведения пользователей
 * - Персональных рекомендаций
 * - Адаптивного контента
 * - Предсказания предпочтений
 */

class AILearningSystem {
    constructor() {
        this.userBehavior = {};
        this.learningModel = null;
        this.recommendations = {};
        this.isInitialized = false;
        
        this.init();
    }
    
    /**
     * Инициализация системы
     */
    async init() {
        try {
            // Загружаем сохраненные данные
            this.loadUserBehavior();
            
            // Инициализируем модель машинного обучения
            await this.initLearningModel();
            
            // Начинаем сбор данных о поведении
            this.startBehaviorTracking();
            
            this.isInitialized = true;
            console.log('🤖 AI Learning System инициализирована');
            
        } catch (error) {
            console.error('❌ Ошибка инициализации AI Learning System:', error);
        }
    }
    
    /**
     * Инициализация модели машинного обучения
     */
    async initLearningModel() {
        try {
            // Простая модель на основе правил и статистики
            this.learningModel = {
                // Веса для различных факторов
                weights: {
                    subject_preference: 0.3,
                    difficulty_level: 0.25,
                    time_pattern: 0.2,
                    interaction_frequency: 0.15,
                    success_rate: 0.1
                },
                
                // Пороги для классификации
                thresholds: {
                    high_preference: 0.8,
                    medium_preference: 0.5,
                    low_preference: 0.3
                },
                
                // История предсказаний
                predictionHistory: []
            };
            
            console.log('📊 Модель машинного обучения инициализирована');
            
        } catch (error) {
            console.error('❌ Ошибка инициализации модели:', error);
        }
    }
    
    /**
     * Начало отслеживания поведения пользователя
     */
    startBehaviorTracking() {
        // Отслеживаем клики
        this.trackClicks();
        
        // Отслеживаем время на страницах
        this.trackPageTime();
        
        // Отслеживаем скроллинг
        this.trackScrolling();
        
        // Отслеживаем взаимодействие с формами
        this.trackFormInteractions();
        
        // Отслеживаем навигацию
        this.trackNavigation();
        
        console.log('👁️ Отслеживание поведения запущено');
    }
    
    /**
     * Отслеживание кликов
     */
    trackClicks() {
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            // Анализируем клики по предметам
            if (target.closest('.subject-card')) {
                this.recordSubjectClick(target.closest('.subject-card'));
            }
            
            // Анализируем клики по заданиям
            if (target.closest('.task-item')) {
                this.recordTaskClick(target.closest('.task-item'));
            }
            
            // Анализируем клики по кнопкам
            if (target.closest('.btn')) {
                this.recordButtonClick(target.closest('.btn'));
            }
            
            // Анализируем клики по навигации
            if (target.closest('.nav-link')) {
                this.recordNavigationClick(target.closest('.nav-link'));
            }
        });
    }
    
    /**
     * Отслеживание времени на страницах
     */
    trackPageTime() {
        let startTime = Date.now();
        let isPageVisible = true;
        
        // Отслеживаем видимость страницы
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                isPageVisible = false;
                this.recordPageTime(startTime, Date.now());
            } else {
                isPageVisible = true;
                startTime = Date.now();
            }
        });
        
        // Отслеживаем уход со страницы
        window.addEventListener('beforeunload', () => {
            if (isPageVisible) {
                this.recordPageTime(startTime, Date.now());
            }
        });
        
        // Периодически записываем время
        setInterval(() => {
            if (isPageVisible) {
                this.recordPageTime(startTime, Date.now());
                startTime = Date.now();
            }
        }, 30000); // Каждые 30 секунд
    }
    
    /**
     * Отслеживание скроллинга
     */
    trackScrolling() {
        let scrollDepth = 0;
        let maxScrollDepth = 0;
        
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercentage = (currentScroll / documentHeight) * 100;
            
            scrollDepth = scrollPercentage;
            maxScrollDepth = Math.max(maxScrollDepth, scrollPercentage);
            
            // Записываем глубину скроллинга каждые 25%
            if (Math.floor(scrollPercentage / 25) > Math.floor((scrollPercentage - 1) / 25)) {
                this.recordScrollDepth(scrollPercentage);
            }
        });
        
        // Записываем финальную глубину при уходе со страницы
        window.addEventListener('beforeunload', () => {
            this.recordScrollDepth(maxScrollDepth, true);
        });
    }
    
    /**
     * Отслеживание взаимодействия с формами
     */
    trackFormInteractions() {
        // Отслеживаем фокус на полях ввода
        document.addEventListener('focusin', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                this.recordFormInteraction('focus', event.target);
            }
        });
        
        // Отслеживаем ввод текста
        document.addEventListener('input', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                this.recordFormInteraction('input', event.target);
            }
        });
        
        // Отслеживаем отправку форм
        document.addEventListener('submit', (event) => {
            this.recordFormInteraction('submit', event.target);
        });
    }
    
    /**
     * Отслеживание навигации
     */
    trackNavigation() {
        // Отслеживаем переходы по страницам
        let currentUrl = window.location.href;
        
        setInterval(() => {
            if (window.location.href !== currentUrl) {
                this.recordPageNavigation(currentUrl, window.location.href);
                currentUrl = window.location.href;
            }
        }, 1000);
        
        // Отслеживаем использование кнопок браузера
        window.addEventListener('popstate', () => {
            this.recordPageNavigation(currentUrl, window.location.href);
            currentUrl = window.location.href;
        });
    }
    
    /**
     * Запись поведения пользователя
     */
    recordBehavior(type, data) {
        if (!this.userBehavior[type]) {
            this.userBehavior[type] = [];
        }
        
        this.userBehavior[type].push(data);
        
        // Ограничиваем количество записей
        if (this.userBehavior[type].length > 100) {
            this.userBehavior[type] = this.userBehavior[type].slice(-50);
        }
        
        // Сохраняем в localStorage
        this.saveUserBehavior();
        
        // Анализируем поведение каждые 10 записей
        if (this.userBehavior[type].length % 10 === 0) {
            this.analyzeBehavior();
        }
    }
    
    /**
     * Сохранение поведения пользователя
     */
    saveUserBehavior() {
        try {
            localStorage.setItem('examflow_user_behavior', JSON.stringify(this.userBehavior));
        } catch (error) {
            console.error('❌ Ошибка сохранения поведения:', error);
        }
    }
    
    /**
     * Загрузка поведения пользователя
     */
    loadUserBehavior() {
        try {
            const saved = localStorage.getItem('examflow_user_behavior');
            if (saved) {
                this.userBehavior = JSON.parse(saved);
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки поведения:', error);
            this.userBehavior = {};
        }
    }
    
    /**
     * Анализ поведения пользователя
     */
    analyzeBehavior() {
        try {
            // Анализируем предпочтения по предметам
            const subjectPreferences = this.analyzeSubjectPreferences();
            
            // Анализируем предпочтения по сложности
            const difficultyPreferences = this.analyzeDifficultyPreferences();
            
            // Анализируем паттерны времени
            const timePatterns = this.analyzeTimePatterns();
            
            // Анализируем паттерны взаимодействия
            const interactionPatterns = this.analyzeInteractionPatterns();
            
            // Обновляем профиль пользователя
            this.updateUserProfile({
                subject_preferences: subjectPreferences,
                difficulty_preferences: difficultyPreferences,
                time_patterns: timePatterns,
                interaction_patterns: interactionPatterns,
                last_updated: Date.now()
            });
            
            // Генерируем рекомендации
            this.generateRecommendations();
            
        } catch (error) {
            console.error('❌ Ошибка анализа поведения:', error);
        }
    }
    
    /**
     * Анализ предпочтений по предметам
     */
    analyzeSubjectPreferences() {
        const subjectClicks = this.userBehavior.subject_click || [];
        const preferences = {};
        
        subjectClicks.forEach(click => {
            const subject = click.subject;
            if (!preferences[subject]) {
                preferences[subject] = {
                    clicks: 0,
                    last_click: 0,
                    exam_types: new Set()
                };
            }
            
            preferences[subject].clicks++;
            preferences[subject].last_click = Math.max(preferences[subject].last_click, click.timestamp);
            preferences[subject].exam_types.add(click.exam_type);
        });
        
        // Вычисляем оценку предпочтения
        const now = Date.now();
        Object.keys(preferences).forEach(subject => {
            const data = preferences[subject];
            const recency = Math.max(0, 1 - (now - data.last_click) / (7 * 24 * 60 * 60 * 1000)); // 7 дней
            const frequency = Math.min(1, data.clicks / 10); // Нормализуем к 10 кликам
            
            data.preference_score = (frequency * 0.6) + (recency * 0.4);
            data.exam_types = Array.from(data.exam_types);
        });
        
        return preferences;
    }
    
    /**
     * Анализ предпочтений по сложности
     */
    analyzeDifficultyPreferences() {
        const taskClicks = this.userBehavior.task_click || [];
        const preferences = {};
        
        taskClicks.forEach(click => {
            const difficulty = click.difficulty;
            if (!preferences[difficulty]) {
                preferences[difficulty] = {
                    clicks: 0,
                    last_click: 0
                };
            }
            
            preferences[difficulty].clicks++;
            preferences[difficulty].last_click = Math.max(preferences[difficulty].last_click, click.timestamp);
        });
        
        return preferences;
    }
    
    /**
     * Анализ паттернов времени
     */
    analyzeTimePatterns() {
        const pageTimes = this.userBehavior.page_time || [];
        const patterns = {
            total_time: 0,
            average_time: 0,
            preferred_hours: {},
            preferred_days: {}
        };
        
        pageTimes.forEach(timeData => {
            patterns.total_time += timeData.duration;
            
            const date = new Date(timeData.timestamp);
            const hour = date.getHours();
            const day = date.getDay();
            
            patterns.preferred_hours[hour] = (patterns.preferred_hours[hour] || 0) + 1;
            patterns.preferred_days[day] = (patterns.preferred_days[day] || 0) + 1;
        });
        
        if (pageTimes.length > 0) {
            patterns.average_time = patterns.total_time / pageTimes.length;
        }
        
        return patterns;
    }
    
    /**
     * Анализ паттернов взаимодействия
     */
    analyzeInteractionPatterns() {
        const buttonClicks = this.userBehavior.button_click || [];
        const formInteractions = this.userBehavior.form_interaction || [];
        const scrollDepths = this.userBehavior.scroll_depth || [];
        
        const patterns = {
            button_preferences: {},
            form_engagement: formInteractions.length,
            scroll_engagement: 0,
            interaction_frequency: buttonClicks.length + formInteractions.length
        };
        
        // Анализируем предпочтения по кнопкам
        buttonClicks.forEach(click => {
            const type = click.button_type;
            patterns.button_preferences[type] = (patterns.button_preferences[type] || 0) + 1;
        });
        
        // Анализируем вовлеченность в скроллинг
        if (scrollDepths.length > 0) {
            const avgDepth = scrollDepths.reduce((sum, scroll) => sum + scroll.depth, 0) / scrollDepths.length;
            patterns.scroll_engagement = avgDepth;
        }
        
        return patterns;
    }
    
    /**
     * Обновление профиля пользователя
     */
    updateUserProfile(profile) {
        this.userBehavior.profile = profile;
        this.saveUserBehavior();
        
        // Отправляем профиль на сервер
        this.sendProfileToServer(profile);
    }
    
    /**
     * Генерация рекомендаций
     */
    generateRecommendations() {
        try {
            const profile = this.userBehavior.profile;
            if (!profile) return;
            
            const recommendations = {
                subjects: this.recommendSubjects(profile),
                tasks: this.recommendTasks(profile),
                content: this.recommendContent(profile),
                timing: this.recommendTiming(profile)
            };
            
            this.recommendations = recommendations;
            this.applyRecommendations(recommendations);
            
        } catch (error) {
            console.error('❌ Ошибка генерации рекомендаций:', error);
        }
    }
    
    /**
     * Рекомендации по предметам
     */
    recommendSubjects(profile) {
        const subjectPrefs = profile.subject_preferences || {};
        const recommendations = [];
        
        // Рекомендуем предметы с высоким предпочтением
        Object.entries(subjectPrefs)
            .sort(([,a], [,b]) => b.preference_score - a.preference_score)
            .slice(0, 3)
            .forEach(([subject, data]) => {
                recommendations.push({
                    subject: subject,
                    reason: `Вы часто изучаете ${subject} (${data.clicks} раз)`,
                    priority: 'high'
                });
            });
        
        return recommendations;
    }
    
    /**
     * Рекомендации по заданиям
     */
    recommendTasks(profile) {
        const difficultyPrefs = profile.difficulty_preferences || {};
        const recommendations = [];
        
        // Рекомендуем задания подходящей сложности
        const preferredDifficulty = Object.keys(difficultyPrefs)
            .sort((a, b) => difficultyPrefs[b].clicks - difficultyPrefs[a].clicks)[0];
        
        if (preferredDifficulty) {
            recommendations.push({
                difficulty: preferredDifficulty,
                reason: `Вы предпочитаете задания сложности ${preferredDifficulty}`,
                priority: 'medium'
            });
        }
        
        return recommendations;
    }
    
    /**
     * Рекомендации по контенту
     */
    recommendContent(profile) {
        const interactionPatterns = profile.interaction_patterns || {};
        const recommendations = [];
        
        // Рекомендации на основе вовлеченности
        if (interactionPatterns.scroll_engagement > 70) {
            recommendations.push({
                type: 'detailed_content',
                reason: 'Вы внимательно изучаете контент',
                priority: 'high'
            });
        }
        
        if (interactionPatterns.form_engagement > 5) {
            recommendations.push({
                type: 'interactive_content',
                reason: 'Вы активно взаимодействуете с формами',
                priority: 'medium'
            });
        }
        
        return recommendations;
    }
    
    /**
     * Рекомендации по времени
     */
    recommendTiming(profile) {
        const timePatterns = profile.time_patterns || {};
        const recommendations = [];
        
        // Рекомендации на основе предпочитаемого времени
        if (timePatterns.preferred_hours) {
            const bestHour = Object.entries(timePatterns.preferred_hours)
                .sort(([,a], [,b]) => b - a)[0];
            
            if (bestHour) {
                recommendations.push({
                    type: 'optimal_time',
                    hour: parseInt(bestHour[0]),
                    reason: `Лучшее время для изучения: ${bestHour[0]}:00`,
                    priority: 'medium'
                });
            }
        }
        
        return recommendations;
    }
    
    /**
     * Применение рекомендаций
     */
    applyRecommendations(recommendations) {
        try {
            // Применяем рекомендации по предметам
            this.applySubjectRecommendations(recommendations.subjects);
            
            // Применяем рекомендации по заданиям
            this.applyTaskRecommendations(recommendations.tasks);
            
            // Применяем рекомендации по контенту
            this.applyContentRecommendations(recommendations.content);
            
            // Применяем рекомендации по времени
            this.applyTimingRecommendations(recommendations.timing);
            
        } catch (error) {
            console.error('❌ Ошибка применения рекомендаций:', error);
        }
    }
    
    /**
     * Применение рекомендаций по предметам
     */
    applySubjectRecommendations(subjectRecommendations) {
        subjectRecommendations.forEach(rec => {
            // Подсвечиваем рекомендуемые предметы
            const subjectElements = document.querySelectorAll(`[data-subject="${rec.subject}"]`);
            subjectElements.forEach(element => {
                element.classList.add('recommended');
                element.setAttribute('title', rec.reason);
            });
        });
    }
    
    /**
     * Применение рекомендаций по заданиям
     */
    applyTaskRecommendations(taskRecommendations) {
        taskRecommendations.forEach(rec => {
            // Подсвечиваем задания подходящей сложности
            const taskElements = document.querySelectorAll(`[data-difficulty="${rec.difficulty}"]`);
            taskElements.forEach(element => {
                element.classList.add('recommended-difficulty');
                element.setAttribute('title', rec.reason);
            });
        });
    }
    
    /**
     * Применение рекомендаций по контенту
     */
    applyContentRecommendations(contentRecommendations) {
        contentRecommendations.forEach(rec => {
            if (rec.type === 'detailed_content') {
                // Показываем больше деталей
                document.body.classList.add('show-detailed-content');
            }
            
            if (rec.type === 'interactive_content') {
                // Добавляем интерактивные элементы
                document.body.classList.add('show-interactive-content');
            }
        });
    }
    
    /**
     * Применение рекомендаций по времени
     */
    applyTimingRecommendations(timingRecommendations) {
        timingRecommendations.forEach(rec => {
            if (rec.type === 'optimal_time') {
                // Показываем уведомление о лучшем времени
                this.showOptimalTimeNotification(rec);
            }
        });
    }
    
    /**
     * Показ уведомления о лучшем времени
     */
    showOptimalTimeNotification(timingRec) {
        const currentHour = new Date().getHours();
        const isOptimalTime = Math.abs(currentHour - timingRec.hour) <= 1;
        
        if (isOptimalTime) {
            this.showNotification(
                `🎯 Оптимальное время для изучения!`,
                timingRec.reason,
                'success'
            );
        }
    }
    
    /**
     * Показ уведомления
     */
    showNotification(title, message, type = 'info') {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `ai-notification ai-notification-${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <strong>${title}</strong>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
        `;
        
        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#d4edda' : '#d1ecf1'};
            border: 1px solid ${type === 'success' ? '#c3e6cb' : '#bee5eb'};
            border-radius: 8px;
            padding: 15px;
            max-width: 300px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
        `;
        
        // Добавляем на страницу
        document.body.appendChild(notification);
        
        // Обработчик закрытия
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    /**
     * Отправка профиля на сервер
     */
    async sendProfileToServer(profile) {
        try {
            const response = await fetch('/api/update-user-profile/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(profile)
            });
            
            if (response.ok) {
                console.log('✅ Профиль отправлен на сервер');
            }
            
        } catch (error) {
            console.error('❌ Ошибка отправки профиля:', error);
        }
    }
    
    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    /**
     * Получение рекомендаций
     */
    getRecommendations() {
        return this.recommendations;
    }
    
    /**
     * Получение профиля пользователя
     */
    getUserProfile() {
        return this.userBehavior.profile;
    }
    
    /**
     * Сброс данных пользователя
     */
    resetUserData() {
        this.userBehavior = {};
        this.recommendations = {};
        localStorage.removeItem('examflow_user_behavior');
        console.log('🔄 Данные пользователя сброшены');
    }
}

// Инициализируем систему при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.aiLearningSystem = new AILearningSystem();
});

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AILearningSystem;
}
