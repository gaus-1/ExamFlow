/**
 * ExamFlow Performance Optimizations
 * Современные техники оптимизации для UX/UI
 */

// ===== LAZY LOADING =====
class LazyLoader {
    constructor() {
        this.imageObserver = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            // Observe all images with data-src
            document.querySelectorAll('img[data-src]').forEach(img => {
                this.imageObserver.observe(img);
            });
        }
    }

    loadImage(img) {
        const src = img.dataset.src;
        if (src) {
            img.src = src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
        }
    }
}

// ===== DEBOUNCED SCROLL HANDLER =====
class ScrollOptimizer {
    constructor() {
        this.scrollTimeout = null;
        this.lastScrollTop = 0;
        this.header = document.querySelector('.header');
        this.init();
    }

    init() {
        // Debounced scroll handler
        window.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
    }

    handleScroll() {
        if (this.scrollTimeout) {
            cancelAnimationFrame(this.scrollTimeout);
        }

        this.scrollTimeout = requestAnimationFrame(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Header visibility
            if (scrollTop > this.lastScrollTop && scrollTop > 100) {
                // Scrolling down
                this.header.style.transform = 'translateY(-100%)';
            } else {
                // Scrolling up
                this.header.style.transform = 'translateY(0)';
            }
            
            this.lastScrollTop = scrollTop;
        });
    }
}

// ===== PERFORMANCE MONITORING =====
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        // Core Web Vitals
        this.measureCLS();
        this.measureFID();
        this.measureLCP();
        
        // Custom metrics
        this.measurePageLoad();
    }

    measureCLS() {
        if ('PerformanceObserver' in window) {
            const clsObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        this.metrics.cls = entry.value;
                    }
                }
            });
            
            clsObserver.observe({ entryTypes: ['layout-shift'] });
        }
    }

    measureFID() {
        if ('PerformanceObserver' in window) {
            const fidObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.metrics.fid = entry.processingStart - entry.startTime;
                }
            });
            
            fidObserver.observe({ entryTypes: ['first-input'] });
        }
    }

    measureLCP() {
        if ('PerformanceObserver' in window) {
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.lcp = lastEntry.startTime;
            });
            
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        }
    }

    measurePageLoad() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                this.metrics.pageLoad = navigation.loadEventEnd - navigation.fetchStart;
                
                // Log metrics (in production, send to analytics)
                console.log('Performance Metrics:', this.metrics);
            }, 0);
        });
    }
}

// ===== ACCESSIBILITY ENHANCEMENTS =====
class AccessibilityEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceFocusManagement();
        this.addSkipLinks();
        this.enhanceKeyboardNavigation();
        this.addAriaLiveRegions();
    }

    enhanceFocusManagement() {
        // Focus trap for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const focusableElements = document.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }

    addSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main';
        skipLink.textContent = 'Перейти к основному содержимому';
        skipLink.className = 'sr-only';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--color-primary-600);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 10000;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    enhanceKeyboardNavigation() {
        // Enhanced keyboard navigation for custom components
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open modals or dropdowns
                const openModals = document.querySelectorAll('[aria-modal="true"]');
                openModals.forEach(modal => {
                    modal.style.display = 'none';
                    modal.setAttribute('aria-hidden', 'true');
                });
            }
        });
    }

    addAriaLiveRegions() {
        // Add live regions for dynamic content updates
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        document.body.appendChild(liveRegion);
    }
}

// ===== FORM VALIDATION ENHANCEMENT =====
class FormValidator {
    constructor(form) {
        this.form = form;
        this.rules = {};
        this.init();
    }

    init() {
        this.setupValidation();
        this.addRealTimeValidation();
    }

    setupValidation() {
        // Custom validation rules
        this.rules = {
            required: (value) => value.trim() !== '',
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            minLength: (value, min) => value.length >= min,
            maxLength: (value, max) => value.length <= max
        };
    }

    addRealTimeValidation() {
        const inputs = this.form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
            
            input.addEventListener('input', this.debounce(() => {
                this.validateField(input);
            }, 300));
        });
    }

    validateField(field) {
        const value = field.value;
        const rules = field.dataset.validation ? field.dataset.validation.split('|') : [];
        
        for (const rule of rules) {
            const [ruleName, ...params] = rule.split(':');
            
            if (this.rules[ruleName]) {
                const isValid = this.rules[ruleName](value, ...params);
                
                if (!isValid) {
                    this.showFieldError(field, this.getErrorMessage(ruleName, params));
                    return false;
                }
            }
        }
        
        this.clearFieldError(field);
        return true;
    }

    showFieldError(field, message) {
        field.setAttribute('aria-invalid', 'true');
        
        let errorElement = field.parentNode.querySelector('.form-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'form-error';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        
        // Announce to screen readers
        this.announceToScreenReader(message);
    }

    clearFieldError(field) {
        field.removeAttribute('aria-invalid');
        
        const errorElement = field.parentNode.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    getErrorMessage(rule, params) {
        const messages = {
            required: 'Это поле обязательно для заполнения',
            email: 'Введите корректный email адрес',
            minLength: `Минимум ${params[0]} символов`,
            maxLength: `Максимум ${params[0]} символов`
        };
        
        return messages[rule] || 'Некорректное значение';
    }

    announceToScreenReader(message) {
        const liveRegion = document.getElementById('live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
        }
    }

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
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all optimizations
    new LazyLoader();
    new ScrollOptimizer();
    new PerformanceMonitor();
    new AccessibilityEnhancer();
    
    // Initialize form validation for all forms
    document.querySelectorAll('form').forEach(form => {
        new FormValidator(form);
    });
    
    // Add loading states for better UX
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        link.addEventListener('click', () => {
            link.style.opacity = '0.7';
            link.style.pointerEvents = 'none';
        });
    });
});

// ===== SERVICE WORKER REGISTRATION =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
