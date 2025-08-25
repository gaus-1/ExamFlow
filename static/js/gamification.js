/**
 * Система геймификации для ExamFlow
 * Очки, уровни, достижения, прогресс-бары
 */

class ExamFlowGamification {
    constructor() {
        this.userData = this.loadUserData();
        this.achievements = this.getAchievements();
        this.init();
    }

    init() {
        this.setupProgressBars();
        this.setupAchievements();
        this.setupDailyChallenges();
        this.setupLeaderboard();
        this.updateUI();
    }

    /**
     * Загрузка данных пользователя из localStorage
     */
    loadUserData() {
        const defaultData = {
            level: 1,
            experience: 0,
            totalScore: 0,
            tasksCompleted: 0,
            subjects: {},
            achievements: [],
            dailyChallenges: [],
            streak: 0,
            lastLogin: null
        };

        const saved = localStorage.getItem('examflow_user_data');
        if (saved) {
            try {
                return { ...defaultData, ...JSON.parse(saved) };
            } catch (e) {
                console.error('Ошибка загрузки данных пользователя:', e);
                return defaultData;
            }
        }
        return defaultData;
    }

    /**
     * Сохранение данных пользователя
     */
    saveUserData() {
        try {
            localStorage.setItem('examflow_user_data', JSON.stringify(this.userData));
        } catch (e) {
            console.error('Ошибка сохранения данных пользователя:', e);
        }
    }

    /**
     * Получение списка достижений
     */
    getAchievements() {
        return {
            first_task: {
                id: 'first_task',
                title: 'Первые шаги',
                description: 'Решил первую задачу',
                icon: '🎯',
                points: 10,
                condition: () => this.userData.tasksCompleted >= 1
            },
            math_master: {
                id: 'math_master',
                title: 'Мастер математики',
                description: 'Решил 50 задач по математике',
                icon: '📐',
                points: 100,
                condition: () => this.getSubjectProgress('Математика') >= 50
            },
            streak_7: {
                id: 'streak_7',
                title: 'Неделя обучения',
                description: 'Занимался 7 дней подряд',
                icon: '🔥',
                points: 50,
                condition: () => this.userData.streak >= 7
            },
            level_5: {
                id: 'level_5',
                title: 'Опытный ученик',
                description: 'Достиг 5 уровня',
                icon: '⭐',
                points: 200,
                condition: () => this.userData.level >= 5
            },
            subject_expert: {
                id: 'subject_expert',
                title: 'Эксперт по предмету',
                description: 'Решил 100 задач по одному предмету',
                icon: '🏆',
                points: 300,
                condition: () => Object.values(this.userData.subjects).some(progress => progress >= 100)
            }
        };
    }

    /**
     * Добавление опыта и очков
     */
    addExperience(points, subject = null) {
        this.userData.experience += points;
        this.userData.totalScore += points;
        this.userData.tasksCompleted++;

        // Обновляем прогресс по предмету
        if (subject) {
            if (!this.userData.subjects[subject]) {
                this.userData.subjects[subject] = 0;
            }
            this.userData.subjects[subject]++;
        }

        // Проверяем повышение уровня
        this.checkLevelUp();

        // Проверяем достижения
        this.checkAchievements();

        // Сохраняем данные
        this.saveUserData();

        // Обновляем UI
        this.updateUI();

        // Показываем уведомление
        this.showNotification(`+${points} очков!`, 'success');
    }

    /**
     * Проверка повышения уровня
     */
    checkLevelUp() {
        const currentLevel = this.userData.level;
        const requiredExp = currentLevel * 100; // 100 очков на уровень

        if (this.userData.experience >= requiredExp) {
            this.userData.level++;
            this.showNotification(`🎉 Уровень ${this.userData.level}!`, 'levelup');
            
            // Дополнительные бонусы за уровень
            const bonus = this.userData.level * 10;
            this.userData.totalScore += bonus;
            this.showNotification(`+${bonus} бонусных очков!`, 'bonus');
        }
    }

    /**
     * Проверка достижений
     */
    checkAchievements() {
        Object.values(this.achievements).forEach(achievement => {
            if (!this.userData.achievements.includes(achievement.id) && achievement.condition()) {
                this.userData.achievements.push(achievement.id);
                this.userData.totalScore += achievement.points;
                this.showNotification(`🏆 ${achievement.title}! +${achievement.points} очков`, 'achievement');
            }
        });
    }

    /**
     * Получение прогресса по предмету
     */
    getSubjectProgress(subject) {
        return this.userData.subjects[subject] || 0;
    }

    /**
     * Настройка прогресс-баров
     */
    setupProgressBars() {
        // Прогресс-бар уровня
        const levelProgress = document.querySelector('.level-progress');
        if (levelProgress) {
            const currentExp = this.userData.experience;
            const requiredExp = this.userData.level * 100;
            const progress = (currentExp % 100) / 100;
            
            levelProgress.style.width = `${progress * 100}%`;
        }

        // Прогресс-бары по предметам
        document.querySelectorAll('.subject-progress').forEach(bar => {
            const subject = bar.dataset.subject;
            const progress = this.getSubjectProgress(subject);
            const maxProgress = 100; // Максимум для предмета
            
            bar.style.width = `${Math.min(progress / maxProgress, 1) * 100}%`;
        });
    }

    /**
     * Настройка достижений
     */
    setupAchievements() {
        const achievementsContainer = document.querySelector('.achievements-container');
        if (achievementsContainer) {
            achievementsContainer.innerHTML = '';
            
            Object.values(this.achievements).forEach(achievement => {
                const isUnlocked = this.userData.achievements.includes(achievement.id);
                const achievementEl = this.createAchievementElement(achievement, isUnlocked);
                achievementsContainer.appendChild(achievementEl);
            });
        }
    }

    /**
     * Создание элемента достижения
     */
    createAchievementElement(achievement, isUnlocked) {
        const div = document.createElement('div');
        div.className = `achievement-item ${isUnlocked ? 'unlocked' : 'locked'}`;
        div.innerHTML = `
            <div class="achievement-icon">${achievement.icon}</div>
            <div class="achievement-info">
                <h4>${achievement.title}</h4>
                <p>${achievement.description}</p>
                <span class="achievement-points">+${achievement.points} очков</span>
            </div>
            <div class="achievement-status">
                ${isUnlocked ? '✅' : '🔒'}
            </div>
        `;
        return div;
    }

    /**
     * Настройка ежедневных заданий
     */
    setupDailyChallenges() {
        const today = new Date().toDateString();
        
        if (this.userData.lastLogin !== today) {
            this.userData.lastLogin = today;
            this.generateDailyChallenges();
        }

        this.displayDailyChallenges();
    }

    /**
     * Генерация ежедневных заданий
     */
    generateDailyChallenges() {
        const challenges = [
            { id: 'solve_5_tasks', title: 'Решить 5 задач', target: 5, current: 0, reward: 25 },
            { id: 'practice_math', title: 'Практиковать математику', target: 3, current: 0, reward: 20 },
            { id: 'maintain_streak', title: 'Поддерживать серию', target: 1, current: 0, reward: 15 }
        ];

        this.userData.dailyChallenges = challenges;
    }

    /**
     * Отображение ежедневных заданий
     */
    displayDailyChallenges() {
        const container = document.querySelector('.daily-challenges');
        if (container && this.userData.dailyChallenges.length > 0) {
            container.innerHTML = '';
            
            this.userData.dailyChallenges.forEach(challenge => {
                const challengeEl = this.createChallengeElement(challenge);
                container.appendChild(challengeEl);
            });
        }
    }

    /**
     * Создание элемента задания
     */
    createChallengeElement(challenge) {
        const div = document.createElement('div');
        div.className = 'challenge-item';
        const progress = Math.min(challenge.current / challenge.target, 1);
        
        div.innerHTML = `
            <div class="challenge-info">
                <h4>${challenge.title}</h4>
                <div class="challenge-progress">
                    <div class="challenge-bar" style="width: ${progress * 100}%"></div>
                </div>
                <span>${challenge.current}/${challenge.target}</span>
            </div>
            <div class="challenge-reward">
                +${challenge.reward} очков
            </div>
        `;
        return div;
    }

    /**
     * Настройка таблицы лидеров
     */
    setupLeaderboard() {
        // Здесь можно добавить интеграцию с сервером для реальной таблицы лидеров
        const leaderboard = document.querySelector('.leaderboard');
        if (leaderboard) {
            // Показываем локальный рейтинг пользователя
            const userRank = this.calculateUserRank();
            leaderboard.innerHTML = `
                <div class="user-rank">
                    <h3>Ваш рейтинг</h3>
                    <div class="rank-info">
                        <span class="rank-number">#${userRank}</span>
                        <span class="rank-score">${this.userData.totalScore} очков</span>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Расчёт рейтинга пользователя (упрощённо)
     */
    calculateUserRank() {
        // В реальном приложении это будет рассчитываться на сервере
        const score = this.userData.totalScore;
        if (score >= 1000) return 1;
        if (score >= 500) return 2;
        if (score >= 200) return 3;
        if (score >= 100) return 4;
        if (score >= 50) return 5;
        return 6;
    }

    /**
     * Обновление UI
     */
    updateUI() {
        // Обновляем уровень и опыт
        const levelEl = document.querySelector('.user-level');
        if (levelEl) {
            levelEl.textContent = `Уровень ${this.userData.level}`;
        }

        const expEl = document.querySelector('.user-experience');
        if (expEl) {
            expEl.textContent = `${this.userData.experience} опыта`;
        }

        const scoreEl = document.querySelector('.user-score');
        if (scoreEl) {
            scoreEl.textContent = `${this.userData.totalScore} очков`;
        }

        // Обновляем прогресс-бары
        this.setupProgressBars();
    }

    /**
     * Показ уведомлений
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Добавляем в DOM
        document.body.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Автоматическое скрытие
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);

        // Кнопка закрытия
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            });
        }
    }

    /**
     * Сброс прогресса (для тестирования)
     */
    resetProgress() {
        if (confirm('Вы уверены, что хотите сбросить весь прогресс?')) {
            localStorage.removeItem('examflow_user_data');
            location.reload();
        }
    }

    /**
     * Экспорт данных пользователя
     */
    exportUserData() {
        const dataStr = JSON.stringify(this.userData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'examflow_user_data.json';
        link.click();
        
        URL.revokeObjectURL(url);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.examFlowGamification = new ExamFlowGamification();
});

// Экспорт для использования в других модулях
window.ExamFlowGamification = ExamFlowGamification;
