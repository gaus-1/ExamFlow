/**
 * PremiumContentWrapper - компонент для работы с премиум-контентом
 */

class PremiumContentWrapper {
    constructor() {
        this.isPremium = false;
        this.userFeatures = [];
        this.usageLimits = {};
        this.usageStats = {};
        
        this.init();
    }
    
    init() {
        // Получаем данные о премиум статусе из Django
        this.loadPremiumStatus();
        this.setupEventListeners();
    }
    
    loadPremiumStatus() {
        // Данные передаются из Django в HTML
        const premiumData = window.premiumData || {};
        this.isPremium = premiumData.is_premium || false;
        this.userFeatures = premiumData.user_features || ['basic'];
        this.usageLimits = premiumData.usage_limits || {};
        this.usageStats = premiumData.usage_stats || {};
    }
    
    setupEventListeners() {
        // Обработчики для премиум-контента
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('premium-content-trigger')) {
                this.handlePremiumContentClick(e);
            }
        });
        
        // Обработчик для кнопок обновления
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('upgrade-to-premium')) {
                this.showUpgradeModal();
            }
        });
    }
    
    canAccessFeature(feature) {
        return this.userFeatures.includes(feature);
    }
    
    wrapContent(content, feature = 'premium_content', previewLength = 200) {
        if (this.canAccessFeature(feature)) {
            return {
                content: content,
                isPremium: true,
                accessGranted: true
            };
        } else {
            const preview = this.getPreviewContent(content, previewLength);
            return {
                content: preview,
                isPremium: true,
                accessGranted: false,
                upgradeMessage: 'Для доступа к полному контенту требуется премиум-подписка',
                upgradeUrl: '/auth/subscribe/'
            };
        }
    }
    
    getPreviewContent(content, previewLength = 200) {
        if (typeof content === 'string') {
            return content.length > previewLength 
                ? content.substring(0, previewLength) + '...' 
                : content;
        } else if (typeof content === 'object' && content.text) {
            const text = content.text;
            return text.length > previewLength 
                ? text.substring(0, previewLength) + '...' 
                : text;
        } else {
            return String(content).substring(0, previewLength) + '...';
        }
    }
    
    handlePremiumContentClick(event) {
        const element = event.target;
        const feature = element.dataset.feature || 'premium_content';
        
        if (!this.canAccessFeature(feature)) {
            event.preventDefault();
            this.showPremiumRequiredModal(feature);
        }
    }
    
    showPremiumRequiredModal(feature) {
        const modal = this.createPremiumModal(feature);
        document.body.appendChild(modal);
        modal.style.display = 'block';
        
        // Анимация появления
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }
    
    createPremiumModal(feature) {
        const modal = document.createElement('div');
        modal.className = 'premium-modal';
        modal.innerHTML = `
            <div class="premium-modal-overlay">
                <div class="premium-modal-content">
                    <div class="premium-modal-header">
                        <h3>🔒 Премиум-контент</h3>
                        <button class="premium-modal-close">&times;</button>
                    </div>
                    <div class="premium-modal-body">
                        <div class="premium-icon">⭐</div>
                        <p>Для доступа к этому контенту требуется премиум-подписка</p>
                        <div class="premium-benefits">
                            <h4>Преимущества премиум-подписки:</h4>
                            <ul>
                                <li>✅ Полный доступ ко всем материалам</li>
                                <li>✅ Экспорт в PDF</li>
                                <li>✅ Расширенный поиск</li>
                                <li>✅ Персональные рекомендации</li>
                                <li>✅ Сравнение версий</li>
                                <li>✅ Приоритетная поддержка</li>
                            </ul>
                        </div>
                    </div>
                    <div class="premium-modal-footer">
                        <button class="btn btn-secondary premium-modal-close">Позже</button>
                        <a href="/auth/subscribe/" class="btn btn-primary">Оформить подписку</a>
                    </div>
                </div>
            </div>
        `;
        
        // Обработчики закрытия
        modal.querySelectorAll('.premium-modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal(modal));
        });
        
        modal.querySelector('.premium-modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeModal(modal);
            }
        });
        
        return modal;
    }
    
    closeModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 300);
    }
    
    showUpgradeModal() {
        const modal = this.createUpgradeModal();
        document.body.appendChild(modal);
        modal.style.display = 'block';
        
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }
    
    createUpgradeModal() {
        const modal = document.createElement('div');
        modal.className = 'premium-modal upgrade-modal';
        modal.innerHTML = `
            <div class="premium-modal-overlay">
                <div class="premium-modal-content">
                    <div class="premium-modal-header">
                        <h3>🚀 Обновление до премиум</h3>
                        <button class="premium-modal-close">&times;</button>
                    </div>
                    <div class="premium-modal-body">
                        <div class="upgrade-pricing">
                            <div class="pricing-card">
                                <h4>Премиум</h4>
                                <div class="price">₽299<span>/месяц</span></div>
                                <ul class="features">
                                    <li>✅ Неограниченные запросы</li>
                                    <li>✅ Экспорт в PDF</li>
                                    <li>✅ Расширенный поиск</li>
                                    <li>✅ Персональные рекомендации</li>
                                    <li>✅ Сравнение версий</li>
                                    <li>✅ Приоритетная поддержка</li>
                                </ul>
                                <a href="/auth/subscribe/" class="btn btn-primary">Оформить подписку</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Обработчики закрытия
        modal.querySelectorAll('.premium-modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal(modal));
        });
        
        modal.querySelector('.premium-modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeModal(modal);
            }
        });
        
        return modal;
    }
    
    trackUsage(action, count = 1) {
        if (!this.isPremium) {
            // Отправляем запрос на сервер для отслеживания использования
            fetch('/api/usage/track/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    count: count
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateUsageStats(action, data.stats);
                }
            })
            .catch(error => {
                console.error('Ошибка отслеживания использования:', error);
            });
        }
    }
    
    updateUsageStats(action, stats) {
        this.usageStats[action] = stats;
        this.updateUsageDisplay(action);
    }
    
    updateUsageDisplay(action) {
        const stats = this.usageStats[action];
        if (!stats) return;
        
        const displayElement = document.querySelector(`[data-usage="${action}"]`);
        if (displayElement) {
            displayElement.innerHTML = `
                <span class="usage-current">${stats.current}</span>
                <span class="usage-separator">/</span>
                <span class="usage-limit">${stats.limit}</span>
                <span class="usage-remaining">(${stats.remaining} осталось)</span>
            `;
            
            // Обновляем прогресс-бар
            const progressBar = displayElement.querySelector('.usage-progress');
            if (progressBar) {
                progressBar.style.width = `${stats.percentage}%`;
            }
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Методы для работы с конкретными функциями
    canExportPDF() {
        return this.canAccessFeature('pdf_export');
    }
    
    canAdvancedSearch() {
        return this.canAccessFeature('advanced_search');
    }
    
    canPersonalizedRecommendations() {
        return this.canAccessFeature('personalized_recommendations');
    }
    
    canVersionComparison() {
        return this.canAccessFeature('version_comparison');
    }
    
    // Утилиты для отображения
    showPremiumBadge(element) {
        if (!this.isPremium) {
            const badge = document.createElement('span');
            badge.className = 'premium-badge';
            badge.innerHTML = '⭐ Premium';
            element.appendChild(badge);
        }
    }
    
    hidePremiumContent(element) {
        if (!this.isPremium) {
            element.style.display = 'none';
        }
    }
    
    showUpgradePrompt(element, feature) {
        if (!this.canAccessFeature(feature)) {
            const prompt = document.createElement('div');
            prompt.className = 'upgrade-prompt';
            prompt.innerHTML = `
                <div class="upgrade-prompt-content">
                    <span class="upgrade-icon">🔒</span>
                    <span class="upgrade-text">Требуется премиум-подписка</span>
                    <button class="upgrade-btn upgrade-to-premium">Обновить</button>
                </div>
            `;
            element.appendChild(prompt);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.premiumContentWrapper = new PremiumContentWrapper();
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PremiumContentWrapper;
}
