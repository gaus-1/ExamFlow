/* ========================================
 * Геймификация ExamFlow 2.0
 * 
  ======================================== */
class ExamFlowGamification {
  constructor() {
    this.userData = this.loadUserData();
    this.init();
  }
  
  init() {
    this.updateProgressDisplay();
    this.updateAchievementsDisplay();
    this.setupEventListeners();
  }
  
  loadUserData() {
    const saved = localStorage.getItem('examflow_user_data');
    if (saved) {
      return JSON.parse(saved);
    }
    
    // Данные по умолчанию для демонстрации
    return {
      level: 5,
      xp: 750,
      totalXp: 1250,
      solvedTasks: 47,
      achievements: 12,
      achievementsList: [
        { id: 'first_task', name: 'Первая задача', icon: '🎯', earned: true },
        { id: 'streak_5', name: 'Серия успехов', icon: '🔥', earned: true },
        { id: 'ai_questions_10', name: 'Любознательный', icon: '🧠', earned: true },
        { id: 'speed_30s', name: 'Скорость', icon: '⚡', earned: true },
        { id: 'master_100', name: 'Мастер', icon: '🏆', earned: false },
        { id: 'expert_level_10', name: 'Эксперт', icon: '🌟', earned: false },
        { id: 'all_subjects', name: 'Эрудит', icon: '📚', earned: false },
        { id: 'all_achievements', name: 'Легенда', icon: '💎', earned: false }
      ]
    };
  }
  
  saveUserData() {
    localStorage.setItem('examflow_user_data', JSON.stringify(this.userData));
  }
  
  addXP(amount, reason = '') {
    const oldLevel = this.userData.level;
    this.userData.xp += amount;
    this.userData.totalXp += amount;
    
    // Проверяем повышение уровня
    const newLevel = this.calculateLevel(this.userData.totalXp);
    if (newLevel > oldLevel) {
      this.userData.level = newLevel;
      this.showLevelUpNotification(newLevel);
    }
    
    this.saveUserData();
    this.updateProgressDisplay();
    
    // Показываем уведомление о получении XP
    this.showXPNotification(amount, reason);
  }
  
  calculateLevel(totalXp) {
    // Формула: каждый уровень требует level * 200 XP
    return Math.floor(Math.sqrt(totalXp / 200)) + 1;
  }
  
  getLevelInfo(level) {
    const levelNames = {
      1: 'Новичок',
      2: 'Ученик',
      3: 'Студент',
      4: 'Знаток',
      5: 'Опытный ученик',
      6: 'Специалист',
      7: 'Мастер',
      8: 'Эксперт',
      9: 'Гуру',
      10: 'Легенда'
    };
    
    return {
      name: levelNames[level] || `Уровень ${level}`,
      xpRequired: level * level * 200,
      xpForNext: (level + 1) * (level + 1) * 200
    };
  }
  
  updateProgressDisplay() {
    const levelInfo = this.getLevelInfo(this.userData.level);
    const progressPercent = ((this.userData.totalXp - levelInfo.xpRequired) / (levelInfo.xpForNext - levelInfo.xpRequired)) * 100;
    
    // Обновляем отображение уровня
    const levelBadge = document.querySelector('.level-badge');
    const levelTitle = document.querySelector('.level-title');
    const levelSubtitle = document.querySelector('.level-subtitle');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-label span:last-child');
    
    if (levelBadge) levelBadge.textContent = `Уровень ${this.userData.level}`;
    if (levelTitle) levelTitle.textContent = levelInfo.name;
    if (levelSubtitle) levelSubtitle.textContent = `До следующего уровня: ${levelInfo.xpForNext - this.userData.totalXp} XP`;
    if (progressBar) progressBar.style.width = `${Math.min(progressPercent, 100)}%`;
    if (progressText) progressText.textContent = `${this.userData.totalXp} / ${levelInfo.xpForNext} XP`;
    
    // Обновляем статистику
    const xpStat = document.querySelector('.stats-grid .stat-item:nth-child(1) .stat-number');
    const tasksStat = document.querySelector('.stats-grid .stat-item:nth-child(2) .stat-number');
    const achievementsStat = document.querySelector('.stats-grid .stat-item:nth-child(3) .stat-number');
    
    if (xpStat) xpStat.textContent = this.userData.totalXp.toLocaleString();
    if (tasksStat) tasksStat.textContent = this.userData.solvedTasks;
    if (achievementsStat) achievementsStat.textContent = this.userData.achievements;
  }
  
  updateAchievementsDisplay() {
    const achievementsGrid = document.querySelector('.achievements-grid');
    if (!achievementsGrid) return;
    
    achievementsGrid.innerHTML = '';
    
    this.userData.achievementsList.forEach(achievement => {
      const achievementEl = document.createElement('div');
      achievementEl.className = `achievement-item text-center p-4 rounded-lg ${
        achievement.earned 
          ? 'bg-success/10 border border-success/20' 
          : 'bg-gray-100 border border-gray-200 opacity-50'
      }`;
      
      achievementEl.innerHTML = `
        <div class="achievement-icon text-3xl mb-2">${achievement.icon}</div>
        <div class="achievement-title text-sm font-medium">${achievement.name}</div>
        <div class="achievement-desc text-xs text-muted">${this.getAchievementDescription(achievement.id)}</div>
      `;
      
      achievementsGrid.appendChild(achievementEl);
    });
  }
  
  getAchievementDescription(achievementId) {
    const descriptions = {
      'first_task': 'Решите первую задачу',
      'streak_5': '5 правильных ответов подряд',
      'ai_questions_10': 'Задайте 10 вопросов ИИ',
      'speed_30s': 'Решите задачу за 30 секунд',
      'master_100': 'Решите 100 задач',
      'expert_level_10': 'Достигните 10 уровня',
      'all_subjects': 'Изучите все предметы',
      'all_achievements': 'Получите все достижения'
    };
    
    return descriptions[achievementId] || 'Неизвестное достижение';
  }
  
  checkAchievements() {
    let newAchievements = 0;
    
    // Проверяем достижения
    if (this.userData.solvedTasks >= 1 && !this.hasAchievement('first_task')) {
      this.unlockAchievement('first_task');
      newAchievements++;
    }
    
    if (this.userData.solvedTasks >= 100 && !this.hasAchievement('master_100')) {
      this.unlockAchievement('master_100');
      newAchievements++;
    }
    
    if (this.userData.level >= 10 && !this.hasAchievement('expert_level_10')) {
      this.unlockAchievement('expert_level_10');
      newAchievements++;
    }
    
    if (newAchievements > 0) {
      this.showAchievementNotification(newAchievements);
      this.updateAchievementsDisplay();
    }
  }
  
  hasAchievement(achievementId) {
    const achievement = this.userData.achievementsList.find(a => a.id === achievementId);
    return achievement ? achievement.earned : false;
  }
  
  unlockAchievement(achievementId) {
    const achievement = this.userData.achievementsList.find(a => a.id === achievementId);
    if (achievement && !achievement.earned) {
      achievement.earned = true;
      this.userData.achievements++;
      this.saveUserData();
    }
  }
  
  showXPNotification(amount, reason) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-success text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-slide-in';
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-lg">+${amount} XP</span>
        ${reason ? `<span class="text-sm opacity-90">(${reason})</span>` : ''}
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  showLevelUpNotification(level) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-primary text-white px-6 py-4 rounded-xl shadow-2xl z-50 animate-scale-in';
    notification.innerHTML = `
      <div class="text-center">
        <div class="text-4xl mb-2">🎉</div>
        <div class="text-xl font-bold mb-1">Поздравляем!</div>
        <div class="text-lg">Вы достигли ${level} уровня!</div>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 4000);
  }
  
  showAchievementNotification(count) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 left-4 bg-accent text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-slide-in';
    notification.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-lg">🏆</span>
        <span>Получено ${count} новое достижение!</span>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  setupEventListeners() {
    // Слушаем события от AI ассистента
    document.addEventListener('aiQuestionAsked', () => {
      this.addXP(5, 'Вопрос ИИ');
      this.checkAchievements();
    });
    
    // Слушаем события решения задач
    document.addEventListener('taskSolved', (event) => {
      const { correct, time } = event.detail;
      if (correct) {
        this.userData.solvedTasks++;
        this.addXP(20, 'Правильный ответ');
        
        if (time && time < 30) {
          this.addXP(10, 'Быстрый ответ');
        }
      }
      this.checkAchievements();
    });
  }
}

// Инициализация геймификации
let gamification;
document.addEventListener('DOMContentLoaded', () => {
  gamification = new ExamFlowGamification();
});
