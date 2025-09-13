/**
 * Гостевой доступ для ExamFlow
 * Сохранение данных в localStorage
 */

class GuestAccess {
    constructor() {
        this.storageKey = 'examflow_guest_data';
        this.init();
    }

    init() {
        // Проверяем, есть ли сохраненные данные гостя
        this.loadGuestData();
        
        // Обрабатываем кнопки входа
        this.bindAuthButtons();
        
        // Обрабатываем формы
        this.bindForms();
    }

    loadGuestData() {
        const guestData = localStorage.getItem(this.storageKey);
        if (guestData) {
            try {
                const data = JSON.parse(guestData);
                this.fillForms(data);
                this.showGuestNotification();
            } catch (e) {
                console.error('Ошибка загрузки данных гостя:', e);
            }
        }
    }

    saveGuestData(data) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(data));
            this.showSaveNotification();
        } catch (e) {
            console.error('Ошибка сохранения данных гостя:', e);
        }
    }

    fillForms(data) {
        // Заполняем формы сохраненными данными
        const emailInputs = document.querySelectorAll('input[type="email"]');
        const nameInputs = document.querySelectorAll('input[name*="name"]');
        
        emailInputs.forEach(input => {
            if (data.email && !input.value) {
                input.value = data.email;
            }
        });
        
        nameInputs.forEach(input => {
            if (data.name && !input.value) {
                input.value = data.name;
            }
        });
    }

    bindAuthButtons() {
        // Обрабатываем кнопки OAuth
        const oauthButtons = document.querySelectorAll('[href*="auth:"]');
        oauthButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Сохраняем текущие данные перед переходом
                this.saveCurrentFormData();
            });
        });
    }

    bindForms() {
        // Обрабатываем отправку форм
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.saveCurrentFormData();
            });
        });

        // Обрабатываем изменения в полях
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.saveCurrentFormData();
            });
        });
    }

    saveCurrentFormData() {
        const formData = {};
        
        // Собираем данные из всех форм
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const formDataObj = new FormData(form);
            for (let [key, value] of formDataObj.entries()) {
                if (value && value.trim()) {
                    formData[key] = value.trim();
                }
            }
        });

        // Собираем данные из отдельных полей
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            if (input.value && input.value.trim()) {
                formData.email = input.value.trim();
            }
        });

        const nameInputs = document.querySelectorAll('input[name*="name"]');
        nameInputs.forEach(input => {
            if (input.value && input.value.trim()) {
                formData.name = input.value.trim();
            }
        });

        if (Object.keys(formData).length > 0) {
            this.saveGuestData(formData);
        }
    }

    showGuestNotification() {
        // Показываем уведомление о гостевом доступе
        const notification = document.createElement('div');
        notification.className = 'guest-notification';
        notification.innerHTML = `
            <div class="guest-notification__content">
                <i class="fas fa-info-circle"></i>
                <span>Вы используете гостевой доступ. Данные сохраняются локально.</span>
                <button class="guest-notification__close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    showSaveNotification() {
        // Показываем уведомление о сохранении
        const notification = document.createElement('div');
        notification.className = 'save-notification';
        notification.innerHTML = `
            <div class="save-notification__content">
                <i class="fas fa-check-circle"></i>
                <span>Данные сохранены локально</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    clearGuestData() {
        localStorage.removeItem(this.storageKey);
        this.showClearNotification();
    }

    showClearNotification() {
        const notification = document.createElement('div');
        notification.className = 'clear-notification';
        notification.innerHTML = `
            <div class="clear-notification__content">
                <i class="fas fa-trash"></i>
                <span>Гостевые данные очищены</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }
}

// Инициализируем при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.guestAccess = new GuestAccess();
});

// Экспортируем для использования в других скриптах
window.GuestAccess = GuestAccess;
