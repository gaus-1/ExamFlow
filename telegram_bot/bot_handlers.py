"""
Обработчики команд для Telegram бота

Содержит основную логику бота:
- Команды (/start, /help, /subjects, /stats)
- Обработку callback-запросов (кнопки)
- Решение заданий через бота
- Синхронизацию с веб-сайтом
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from django.contrib.auth.models import User
from core.models import (
    Subject, Task, UserProgress, UserRating, 
    Achievement, Topic, UserProfile, Subscription
)
from django.db.models import Count, Q
from django.utils import timezone

# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения ID текущего задания
current_task_id = None


def get_or_create_user(telegram_user):
    """
    Получить или создать пользователя Django с профилем
    
    Создает пользователя с username = tg_{telegram_id}
    Автоматически создает профиль и рейтинг
    """
    username = f"tg_{telegram_user.id}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': telegram_user.first_name or '',
            'last_name': telegram_user.last_name or '',
        }
    )
    
    # Создаем или получаем профиль
    profile, profile_created = UserProfile.objects.get_or_create( # type: ignore
        user=user,
        defaults={
            'telegram_id': str(telegram_user.id)
        }
    )
    
    # Создаем рейтинг если нужно
    rating, rating_created = UserRating.objects.get_or_create(user=user) # type: ignore
    
    return user, created


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start - приветствие и главное меню
    
    Создает пользователя если его нет
    Показывает основные возможности бота
    """
    try:
        user, created = get_or_create_user(update.effective_user)
        
        welcome_text = f"""
🚀 **Добро пожаловать в ExamFlow!**

Привет, {update.effective_user.first_name}! 

Я помогу тебе подготовиться к ЕГЭ и ОГЭ:

✅ Решать задания по всем предметам
📊 Отслеживать прогресс
🏆 Зарабатывать достижения
🔊 Получать голосовые подсказки (Premium)

Выбери действие:
"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Предметы", callback_data="subjects"), InlineKeyboardButton("🎯 Случайное", callback_data="random_task")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats"), InlineKeyboardButton("🌐 Сайт", url="https://examflow.ru")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )


async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает меню выбора предметов
    
    Отображает все доступные предметы с количеством заданий
    """
    try:
        query = update.callback_query
        await query.answer()
        
        subjects = Subject.objects.annotate( # type: ignore
            tasks_count=Count('topics__tasks')
        ).filter(tasks_count__gt=0)
        
        if not subjects:
            await query.edit_message_text("📚 Предметы пока загружаются...")
            return
        
        keyboard = []
        for subject in subjects:
            button_text = f"{subject.name} ({subject.tasks_count} заданий)"
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"subject_{subject.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📚 **Выберите предмет:**\n\nДоступные предметы для изучения:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в subjects_menu: {e}")


async def show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает темы выбранного предмета
    
    Отображает список тем с количеством заданий в каждой
    """
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[1])
    subject = Subject.objects.get(id=subject_id) # type: ignore 
    
    topics = Topic.objects.filter(subject=subject).annotate( # type: ignore
        tasks_count=Count('tasks')
    ).filter(tasks_count__gt=0)
    
    if not topics:
        await query.edit_message_text(
            f"📖 **{subject.name}**\n\nТемы пока загружаются...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="subjects")
            ]])
        )
        return
    
    keyboard = []
    for topic in topics:
        button_text = f"{topic.name} ({topic.tasks_count})"
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"topic_{topic.id}"
        )])
    
    keyboard.extend([
        [InlineKeyboardButton("🎯 Случайное задание", callback_data=f"random_subject_{subject_id}")],
        [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📖 **{subject.name}**\n\nВыберите тему для изучения:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает задание пользователю
    
    Отображает условие задания и кнопки для ответа
    """
    global current_task_id
    
    query = update.callback_query
    await query.answer()
    
    # Получаем ID задания из callback_data
    if query.data.startswith('topic_'):
        topic_id = int(query.data.split('_')[1])
        topic = Topic.objects.get(id=topic_id) # type: ignore
        tasks = Task.objects.filter(topic=topic) # type: ignore
        
        if not tasks:
            await query.edit_message_text("❌ В этой теме пока нет заданий")
            return
            
        task = tasks.first()  # Берем первое задание
    else:
        # Случайное задание
        tasks = Task.objects.all() # type: ignore
        if not tasks:
            await query.edit_message_text("❌ Задания пока не загружены")
            return
        
        import random
        task = random.choice(tasks)
    
    current_task_id = task.id
    
    # Формируем текст задания
    task_text = f"""
📝 **Задание №{task.id}**
**Предмет:** {task.topic.subject.name}
**Тема:** {task.topic.name}

**Условие:**
{task.content}

Введите ваш ответ:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔊 Голосовая подсказка", callback_data=f"voice_{task.id}")],
        [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subjects")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        task_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ответ пользователя на задание
    
    Проверяет правильность ответа и сохраняет прогресс
    """
    global current_task_id
    
    if not current_task_id:
        await update.message.reply_text("❌ Сначала выберите задание!")
        return
    
    user, _ = get_or_create_user(update.effective_user)
    task = Task.objects.get(id=current_task_id) # type: ignore
    user_answer = update.message.text.strip()
    
    # Проверяем ответ
    is_correct = task.check_answer(user_answer)
    
    # Сохраняем прогресс
    progress, created = UserProgress.objects.get_or_create( # type: ignore
        user=user,
        task=task,
        defaults={
            'user_answer': user_answer,
            'is_correct': is_correct
        }
    )
    
    if not created:
        progress.user_answer = user_answer
        progress.is_correct = is_correct
        progress.save()
    
    # Формируем ответ
    if is_correct:
        response = f"✅ **Правильно!** 🎉\n\n"
        # Обновляем рейтинг
        rating, _ = UserRating.objects.get_or_create(user=user) # type: ignore
        rating.total_points += 10
        rating.correct_answers += 1
        rating.save()
    else:
        response = f"❌ **Неправильно**\n\n"
        response += f"**Правильный ответ:** {task.answer}\n\n"
    
    if task.explanation:
        response += f"**Объяснение:**\n{task.explanation}"
    
    keyboard = [
        [InlineKeyboardButton("🎯 Следующее задание", callback_data="random_task")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    current_task_id = None  # Сбрасываем текущее задание


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает статистику пользователя
    
    Отображает количество решенных заданий, точность, рейтинг
    """
    query = update.callback_query
    await query.answer()
    
    user, _ = get_or_create_user(update.effective_user)
    
    # Получаем статистику
    total_attempts = UserProgress.objects.filter(user=user).count() # type: ignore
    correct_answers = UserProgress.objects.filter(user=user, is_correct=True).count() # type: ignore
    accuracy = round((correct_answers / total_attempts * 100) if total_attempts > 0 else 0, 1)
    
    rating, _ = UserRating.objects.get_or_create(user=user) # type: ignore
    
    stats_text = f"""
📊 **Ваша статистика**

👤 **Пользователь:** {user.first_name or user.username}
✅ **Правильных ответов:** {correct_answers}
📝 **Всего попыток:** {total_attempts}
🎯 **Точность:** {accuracy}%
⭐ **Рейтинг:** {rating.total_points} очков

🏆 **Достижения:** {user.achievements.count()}

Продолжайте решать задания для улучшения результатов!
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Решить задание", callback_data="random_task")],
        [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def voice_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет голосовую подсказку для задания (Premium функция)
    
    Проверяет подписку пользователя и отправляет аудио
    """
    global current_task_id
    
    query = update.callback_query
    await query.answer()
    
    if not current_task_id:
        await query.edit_message_text("❌ Задание не найдено")
        return
    
    user, _ = get_or_create_user(update.effective_user)
    
    # Проверяем подписку
    subscription = Subscription.objects.filter(user=user, is_active=True).first() # type: ignore
    if not subscription:
        await query.edit_message_text(
            "🔊 **Голосовые подсказки доступны только в Premium**\n\n"
            "Оформите подписку на сайте для доступа к этой функции.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Оформить Premium", url="https://examflow.ru/dashboard/")
            ]])
        )
        return
    
    task = Task.objects.get(id=current_task_id) # type: ignore
    
    # Здесь должна быть логика отправки голосового файла
    # Пока отправляем текстовую подсказку
    await query.edit_message_text(
        f"🔊 **Голосовая подсказка для задания №{task.id}**\n\n"
        f"📝 {task.explanation or 'Подсказка пока не добавлена'}\n\n"
        "🎵 Голосовой файл будет добавлен в ближайшее время!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К заданию", callback_data=f"task_{task.id}")
        ]])
    )


async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает неизвестные callback-запросы
    
    Логирует ошибку и показывает главное меню
    """
    query = update.callback_query
    await query.answer()
    
    logger.warning(f"Неизвестный callback: {query.data}")
    
    await query.edit_message_text(
        "❌ Неизвестная команда. Возвращаемся в главное меню.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]])
    )
