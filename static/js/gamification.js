/**
 * ExamFlow Gamification - Система геймификации
 * Реализует очки, уровни, достижения и прогресс
 */

class ExamFlowGamification {
    constructor() {
        this.userData = this.loadUserData();
        this.init();
    }

    init() {
        this.setupProgressBars();
        this.setupAchievements();
        this.setupDailyChallenges();
        this.setupLeaderboard();
        this.updateUI();
    }

    loadUserData() {
        const saved = localStorage.getItem('examflow_user_data');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Ошибка загрузки данных пользователя:', e);
            }
        }
        
        // Данные по умолчанию для нового пользователя
        return {
            level: 1,
            experience: 0,
            totalPoints: 0,
            subjects: {},
            achievements: [],
            dailyChallenges: [],
            lastLogin: new Date().toISOString(),
            streak: 0
        };
    }

    saveUserData() {
        try {
            localStorage.setItem('examflow_user_data', JSON.stringify(this.userData));
        } catch (e) {
            console.error('Ошибка сохранения данных пользователя:', e);
        }
    }

    getAchievements() {
        return [
            { id: 'first_task', name: 'Первое задание', description: 'Решите первое задание', points: 10 },
            { id: 'subject_master', name: 'Мастер предмета', description: 'Изучите 5 тем по предмету', points: 50 },
            { id: 'streak_7', name: 'Неделя обучения', description: 'Занимайтесь 7 дней подряд', points: 100 },
            { id: 'level_5', name: 'Опытный ученик', description: 'Достигните 5 уровня', points: 200 },
            { id: 'perfect_score', name: 'Отличник', description: 'Получите 100% по теме', points: 150 }
        ];
    }

    addExperience(amount, subject = null) {
        this.userData.experience += amount;
        this.userData.totalPoints += amount;
        
        if (subject) {
            if (!this.userData.subjects[subject]) {
                this.userData.subjects[subject] = { experience: 0, topics: [] };
            }
            this.userData.subjects[subject].experience += amount;
        }
        
        this.checkLevelUp();
        this.checkAchievements();
        this.saveUserData();
        this.updateUI();
    }

    checkLevelUp() {
        const currentLevel = this.userData.level;
        const requiredExp = currentLevel * 100; // 100 XP на уровень
        
        if (this.userData.experience >= requiredExp) {
            this.userData.level++;
            this.showNotification(`🎉 Поздравляем! Вы достигли ${this.userData.level} уровня!`);
        }
    }

    checkAchievements() {
        const achievements = this.getAchievements();
        const unlocked = new Set(this.userData.achievements);
        
        achievements.forEach(achievement => {
            if (unlocked.has(achievement.id)) return;
            
            let shouldUnlock = false;
            
            switch (achievement.id) {
                case 'first_task':
                    shouldUnlock = this.userData.totalPoints >= 10;
                    break;
                case 'subject_master':
                    shouldUnlock = Object.values(this.userData.subjects).some(subject => 
                        subject.topics && subject.topics.length >= 5
                    );
                    break;
                case 'streak_7':
                    shouldUnlock = this.userData.streak >= 7;
                    break;
                case 'level_5':
                    shouldUnlock = this.userData.level >= 5;
                    break;
                case 'perfect_score':
                    shouldUnlock = Object.values(this.userData.subjects).some(subject => 
                        subject.topics && subject.topics.some(topic => topic.score === 100)
                    );
                    break;
            }
            
            if (shouldUnlock) {
                this.userData.achievements.push(achievement.id);
                this.addExperience(achievement.points);
                this.showNotification(`🏆 Достижение разблокировано: ${achievement.name}!`);
            }
        });
    }

    getSubjectProgress(subject) {
        const subjectData = this.userData.subjects[subject];
        if (!subjectData) return 0;
        
        return Math.min(100, Math.floor((subjectData.experience / 100) * 100));
    }

    setupProgressBars() {
        // Основной прогресс-бар уровня
        const levelProgress = document.querySelector('.level-progress-bar');
        if (levelProgress) {
            const progress = (this.userData.experience % 100) / 100 * 100;
            levelProgress.style.width = `${progress}%`;
        }
        
        // Прогресс-бары по предметам
        const subjectProgressBars = document.querySelectorAll('.subject-progress');
        subjectProgressBars.forEach(bar => {
            const subject = bar.dataset.subject;
            if (subject) {
                const progress = this.getSubjectProgress(subject);
                bar.style.width = `${progress}%`;
            }
        });
    }

    setupAchievements() {
        const container = document.querySelector('.achievements-container');
        if (!container) return;
        
        const achievements = this.getAchievements();
        const unlocked = new Set(this.userData.achievements);
        
        achievements.forEach(achievement => {
            const isUnlocked = unlocked.has(achievement.id);
            const element = this.createAchievementElement(achievement, isUnlocked);
            container.appendChild(element);
        });
    }

    createAchievementElement(achievement, unlocked) {
        const div = document.createElement('div');
        div.className = `achievement ${unlocked ? 'unlocked' : 'locked'}`;
        div.innerHTML = `
            <div class="achievement-icon">${unlocked ? '🏆' : '🔒'}</div>
            <div class="achievement-info">
                <h4>${achievement.name}</h4>
                <p>${achievement.description}</p>
                <span class="points">+${achievement.points} XP</span>
            </div>
        `;
        return div;
    }

    setupDailyChallenges() {
        this.generateDailyChallenges();
        this.displayDailyChallenges();
    }

    generateDailyChallenges() {
        const today = new Date().toDateString();
        if (this.userData.dailyChallenges.length === 0 || 
            this.userData.dailyChallenges[0].date !== today) {
            
            this.userData.dailyChallenges = [
                { id: 'solve_5', text: 'Решить 5 заданий', target: 5, current: 0, points: 25, date: today },
                { id: 'study_2_topics', text: 'Изучить 2 новые темы', target: 2, current: 0, points: 30, date: today },
                { id: 'perfect_score', text: 'Получить 100% по одной теме', target: 1, current: 0, points: 50, date: today }
            ];
        }
    }

    displayDailyChallenges() {
        const container = document.querySelector('.daily-challenges');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.userData.dailyChallenges.forEach(challenge => {
            const element = this.createChallengeElement(challenge);
            container.appendChild(element);
        });
    }

    createChallengeElement(challenge) {
        const div = document.createElement('div');
        div.className = 'daily-challenge';
        const progress = Math.min(100, (challenge.current / challenge.target) * 100);
        const completed = challenge.current >= challenge.target;
        
        div.innerHTML = `
            <div class="challenge-progress">
                <div class="progress-bar" style="width: ${progress}%"></div>
            </div>
            <div class="challenge-info">
                <span class="challenge-text">${challenge.text}</span>
                <span class="challenge-status">${challenge.current}/${challenge.target}</span>
                <span class="challenge-points">+${challenge.points} XP</span>
            </div>
            ${completed ? '<span class="completed">✓</span>' : ''}
        `;
        
        return div;
    }

    setupLeaderboard() {
        const container = document.querySelector('.leaderboard');
        if (!container) return;
        
        // Имитируем таблицу лидеров (в реальной версии будет API)
        const mockLeaderboard = [
            { name: 'Алексей', level: 8, points: 1250 },
            { name: 'Мария', level: 7, points: 1100 },
            { name: 'Дмитрий', level: 6, points: 950 },
            { name: 'Анна', level: 5, points: 800 },
            { name: 'Сергей', level: 4, points: 650 }
        ];
        
        mockLeaderboard.forEach((user, index) => {
            const div = document.createElement('div');
            div.className = 'leaderboard-item';
            div.innerHTML = `
                <span class="rank">${index + 1}</span>
                <span class="name">${user.name}</span>
                <span class="level">Ур. ${user.level}</span>
                <span class="points">${user.points} XP</span>
            `;
            container.appendChild(div);
        });
    }

    calculateUserRank() {
        // Простая логика ранжирования
        if (this.userData.level >= 8) return 'Эксперт';
        if (this.userData.level >= 5) return 'Продвинутый';
        if (this.userData.level >= 3) return 'Средний';
        return 'Начинающий';
    }

    updateUI() {
        // Обновляем уровень и опыт
        const levelElement = document.querySelector('.user-level');
        if (levelElement) {
            levelElement.textContent = `Уровень ${this.userData.level}`;
        }
        
        const expElement = document.querySelector('.user-experience');
        if (expElement) {
            expElement.textContent = `${this.userData.experience} XP`;
        }
        
        const rankElement = document.querySelector('.user-rank');
        if (rankElement) {
            rankElement.textContent = this.calculateUserRank();
        }
        
        // Обновляем прогресс-бары
        this.setupProgressBars();
        
        // Обновляем достижения
        this.setupAchievements();
        
        // Обновляем ежедневные задания
        this.displayDailyChallenges();
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'gamification-notification';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    resetProgress() {
        if (confirm('Вы уверены, что хотите сбросить весь прогресс? Это действие нельзя отменить.')) {
            this.userData = {
                level: 1,
                experience: 0,
                totalPoints: 0,
                subjects: {},
                achievements: [],
                dailyChallenges: [],
                lastLogin: new Date().toISOString(),
                streak: 0
            };
            this.saveUserData();
            this.updateUI();
            this.showNotification('Прогресс сброшен');
        }
    }

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

// Инициализация геймификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.examflowGamification = new ExamFlowGamification();
});

// Экспорт для использования в других модулях
window.ExamFlowGamification = ExamFlowGamification;
