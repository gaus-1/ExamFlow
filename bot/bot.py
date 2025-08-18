import os
import django
import logging
from datetime import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from core.models import Subject, Task, UserProgress
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count, Q

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_or_create_user(telegram_user):
    """Получить или создать пользователя Django"""
    username = f"tg_{telegram_user.id}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': telegram_user.first_name or '',
            'last_name': telegram_user.last_name or '',
        }
    )
    return user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = get_or_create_user(update.effective_user)
    
    keyboard = [
        [InlineKeyboardButton("📚 Выбрать предмет", callback_data="subjects")],
        [InlineKeyboardButton("🎯 Случайное задание", callback_data="random_task")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
        [InlineKeyboardButton("🏆 Рейтинг", callback_data="rating")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎓 Добро пожаловать в ExamFlow, {update.effective_user.first_name}!\n\n"
        "Я помогу вам эффективно подготовиться к ЕГЭ и ОГЭ с использованием "
        "официальных материалов ФИПИ.\n\n"
        "🎯 Решайте задания\n"
        "📊 Отслеживайте прогресс\n"
        "🏆 Соревнуйтесь с друзьями\n"
        "💡 Получайте рекомендации\n\n"
        "Выберите действие:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)


async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора предметов"""
    query = update.callback_query
    await query.answer()
    
    subjects = Subject.objects.all()[:10]
    
    keyboard = []
    for i in range(0, len(subjects), 2):
        row = []
        for j in range(2):
            if i + j < len(subjects):
                subject = subjects[i + j]
                tasks_count = Task.objects.filter(subject=subject).count()
                
                # Эмодзи для предметов
                subject_emoji = {
                    'Математика': '🧮',
                    'Русский язык': '📝',
                    'Физика': '⚛️',
                    'Химия': '🧪',
                    'Биология': '🧬',
                    'История': '🏛️',
                    'Обществознание': '👥',
                    'Информатика': '💻',
                    'Литература': '📚',
                    'География': '🌍'
                }.get(subject.name, '📖')
                
                row.append(InlineKeyboardButton(
                    f"{subject_emoji} {subject.name} ({tasks_count})", 
                    callback_data=f"subject_{subject.id}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 Выберите предмет для изучения:\n\n"
        "В скобках указано количество доступных заданий.",
        reply_markup=reply_markup
    )


async def subject_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать детали предмета и задания"""
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[1])
    subject = Subject.objects.get(id=subject_id)
    user = get_or_create_user(update.effective_user)
    
    total_tasks = Task.objects.filter(subject=subject).count()
    solved_tasks = UserProgress.objects.filter(user=user, task__subject=subject).count()
    correct_tasks = UserProgress.objects.filter(user=user, task__subject=subject, is_correct=True).count()
    
    accuracy = round((correct_tasks / solved_tasks * 100) if solved_tasks > 0 else 0, 1)
    
    keyboard = [
        [InlineKeyboardButton("🎯 Решать задания", callback_data=f"solve_{subject.id}")],
        [InlineKeyboardButton("🎲 Случайное задание", callback_data=f"random_subject_{subject.id}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{subject.id}")],
        [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Эмодзи для предметов
    subject_emoji = {
        'Математика': '🧮',
        'Русский язык': '📝',
        'Физика': '⚛️',
        'Химия': '🧪',
        'Биология': '🧬',
        'История': '🏛️',
        'Обществознание': '👥',
        'Информатика': '💻',
        'Литература': '📚',
        'География': '🌍'
    }.get(subject.name, '📖')
    
    progress_bar = "🟩" * (correct_tasks // 2) + "🟨" * ((solved_tasks - correct_tasks) // 2) + "⬜" * ((total_tasks - solved_tasks) // 2)
    
    text = (
        f"{subject_emoji} {subject.name}\n"
        f"🎓 {subject.exam_type}\n\n"
        f"📊 Ваша статистика:\n"
        f"📝 Всего заданий: {total_tasks}\n"
        f"✅ Решено: {solved_tasks}\n"
        f"🎯 Правильно: {correct_tasks}\n"
        f"📈 Точность: {accuracy}%\n\n"
        f"Прогресс: {progress_bar[:10]}\n\n"
        f"Готовы продолжить подготовку?"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def solve_subject_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать решение заданий по предмету"""
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[1])
    user = get_or_create_user(update.effective_user)
    
    # Найти нерешённое задание или случайное
    solved_task_ids = UserProgress.objects.filter(
        user=user, 
        task__subject_id=subject_id
    ).values_list('task_id', flat=True)
    
    unsolved_task = Task.objects.filter(subject_id=subject_id).exclude(
        id__in=solved_task_ids
    ).first()
    
    if not unsolved_task:
        unsolved_task = Task.objects.filter(subject_id=subject_id).order_by('?').first()
    
    if unsolved_task:
        await show_task(query, unsolved_task, user)
    else:
        await query.edit_message_text(
            "❌ Задания по этому предмету пока не загружены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{subject_id}")
            ]])
        )


async def random_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать случайное задание"""
    query = update.callback_query
    await query.answer()
    
    user = get_or_create_user(update.effective_user)
    task = Task.objects.order_by('?').first()
    
    if task:
        await show_task(query, task, user)
    else:
        await query.edit_message_text(
            "❌ Задания пока не загружены. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
            ]])
        )


async def random_subject_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайное задание по предмету"""
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[2])
    user = get_or_create_user(update.effective_user)
    task = Task.objects.filter(subject_id=subject_id).order_by('?').first()
    
    if task:
        await show_task(query, task, user)
    else:
        await query.edit_message_text(
            "❌ Задания по этому предмету пока не загружены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{subject_id}")
            ]])
        )


async def show_task(query, task, user):
    """Показать задание пользователю"""
    difficulty_stars = "⭐" * task.difficulty
    difficulty_text = ["Лёгкое", "Среднее", "Сложное"][task.difficulty - 1] if task.difficulty <= 3 else "Очень сложное"
    
    # Проверить, решал ли пользователь это задание
    progress = UserProgress.objects.filter(user=user, task=task).first()
    
    keyboard = [
        [InlineKeyboardButton("✅ Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("👍 Знаю", callback_data=f"correct_{task.id}")],
        [InlineKeyboardButton("👎 Не знаю", callback_data=f"incorrect_{task.id}")],
        [InlineKeyboardButton("🎯 Другое задание", callback_data="random_task")],
        [InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{task.subject.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_text = ""
    if progress:
        if progress.is_correct:
            status_text = "✅ Вы уже правильно решили это задание\n\n"
        else:
            status_text = "❌ Вы решали это задание неправильно\n\n"
    
    text = (
        f"📝 {task.title}\n\n"
        f"{task.description}\n\n"
        f"{status_text}"
        f"📚 Предмет: {task.subject.name}\n"
        f"🎯 Сложность: {difficulty_text} {difficulty_stars}\n\n"
        f"Выберите действие:"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ответ к заданию"""
    query = update.callback_query
    await query.answer()
    
    task_id = int(query.data.split('_')[1])
    task = Task.objects.get(id=task_id)
    user = get_or_create_user(update.effective_user)
    
    keyboard = [
        [InlineKeyboardButton("👍 Понял", callback_data=f"understood_{task.id}")],
        [InlineKeyboardButton("👎 Не понял", callback_data=f"not_understood_{task.id}")],
        [InlineKeyboardButton("🎯 Другое задание", callback_data="random_task")],
        [InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{task.subject.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"📝 {task.title}\n\n"
        f"{task.description}\n\n"
        f"✅ Ответ: {task.answer or 'Ответ будет добавлен позже'}\n\n"
        f"📚 Предмет: {task.subject.name}\n\n"
        f"Понятно ли вам решение?"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def mark_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить задание как правильно решённое"""
    query = update.callback_query
    await query.answer("✅ Отлично! Задание засчитано.")
    
    task_id = int(query.data.split('_')[1])
    task = Task.objects.get(id=task_id)
    user = get_or_create_user(update.effective_user)
    
    progress, created = UserProgress.objects.get_or_create(
        user=user, 
        task=task,
        defaults={'is_correct': True, 'attempts': 1}
    )
    if not created:
        progress.is_correct = True
        progress.attempts += 1
        progress.save()
    
    # Показать следующее задание
    next_task = Task.objects.filter(subject=task.subject).exclude(id=task.id).order_by('?').first()
    if next_task:
        await show_task(query, next_task, user)
    else:
        keyboard = [[InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{task.subject.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎉 Отлично! Вы решили задание правильно.\n\n"
            f"Продолжайте изучать {task.subject.name}!",
            reply_markup=reply_markup
        )


async def mark_incorrect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить задание как неправильно решённое"""
    query = update.callback_query
    await query.answer("📚 Не расстраивайтесь, продолжайте изучать!")
    
    task_id = int(query.data.split('_')[1])
    task = Task.objects.get(id=task_id)
    user = get_or_create_user(update.effective_user)
    
    progress, created = UserProgress.objects.get_or_create(
        user=user, 
        task=task,
        defaults={'is_correct': False, 'attempts': 1}
    )
    if not created:
        progress.attempts += 1
        progress.save()
    
    # Показать ответ
    await show_answer(update, context)


async def mark_understood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить как понятое"""
    query = update.callback_query
    await query.answer("👍 Отлично!")
    
    task_id = int(query.data.split('_')[1])
    user = get_or_create_user(update.effective_user)
    task = Task.objects.get(id=task_id)
    
    progress, created = UserProgress.objects.get_or_create(
        user=user, 
        task=task,
        defaults={'is_correct': True, 'attempts': 1}
    )
    if not created:
        progress.is_correct = True
        progress.save()
    
    # Показать следующее задание
    next_task = Task.objects.filter(subject=task.subject).exclude(id=task.id).order_by('?').first()
    if next_task:
        await show_task(query, next_task, user)


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать прогресс пользователя"""
    query = update.callback_query
    await query.answer()
    
    user = get_or_create_user(update.effective_user)
    
    total_solved = UserProgress.objects.filter(user=user).count()
    correct_solved = UserProgress.objects.filter(user=user, is_correct=True).count()
    accuracy = round((correct_solved / total_solved * 100) if total_solved > 0 else 0, 1)
    
    # Статистика по предметам (топ 5)
    subjects_stats = []
    for subject in Subject.objects.all()[:5]:
        subject_solved = UserProgress.objects.filter(user=user, task__subject=subject).count()
        if subject_solved > 0:
            subject_correct = UserProgress.objects.filter(
                user=user, task__subject=subject, is_correct=True
            ).count()
            subject_accuracy = round((subject_correct / subject_solved * 100), 1)
            
            emoji = {
                'Математика': '🧮', 'Русский язык': '📝', 'Физика': '⚛️',
                'Химия': '🧪', 'Биология': '🧬', 'История': '🏛️',
                'Обществознание': '👥', 'Информатика': '💻'
            }.get(subject.name, '📖')
            
            subjects_stats.append(f"{emoji} {subject.name}: {subject_correct}/{subject_solved} ({subject_accuracy}%)")
    
    keyboard = [
        [InlineKeyboardButton("🏆 Рейтинг", callback_data="rating")],
        [InlineKeyboardButton("📈 Детальная статистика", callback_data="detailed_stats")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    subjects_text = "\n".join(subjects_stats) if subjects_stats else "Начните решать задания!"
    
    level = "🥉 Новичок"
    if total_solved >= 100:
        level = "🏆 Эксперт"
    elif total_solved >= 50:
        level = "🥈 Продвинутый"
    elif total_solved >= 20:
        level = "🥉 Практик"
    
    text = (
        f"📊 Ваш прогресс\n\n"
        f"🎯 Всего решено: {total_solved}\n"
        f"✅ Правильных ответов: {correct_solved}\n"
        f"📈 Общая точность: {accuracy}%\n"
        f"🏅 Уровень: {level}\n\n"
        f"📚 По предметам:\n{subjects_text}\n\n"
        f"💡 Продолжайте решать задания для улучшения результатов!"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать рейтинг пользователей"""
    query = update.callback_query
    await query.answer()
    
    # Топ пользователей по количеству правильных ответов
    top_users = User.objects.annotate(
        correct_answers=Count('userprogress', filter=Q(userprogress__is_correct=True))
    ).order_by('-correct_answers')[:10]
    
    current_user = get_or_create_user(update.effective_user)
    current_position = 0
    
    rating_text = ""
    for i, user in enumerate(top_users, 1):
        if user == current_user:
            current_position = i
            rating_text += f"👑 {i}. Вы - {user.correct_answers} ✅\n"
        else:
            name = user.first_name or f"Пользователь {user.id}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            rating_text += f"{medal} {i}. {name} - {user.correct_answers} ✅\n"
    
    keyboard = [[InlineKeyboardButton("🔙 К прогрессу", callback_data="progress")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"🏆 Рейтинг лучших\n\n"
        f"{rating_text}\n"
        f"Ваша позиция: {current_position or 'не в топ-10'}\n\n"
        f"Решайте больше заданий, чтобы подняться в рейтинге!"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о боте"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌐 Открыть сайт", url="https://examflow.ru")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "ℹ️ О ExamFlow\n\n"
        "🎯 Официальные задания ФИПИ\n"
        "📊 Персональный прогресс\n"
        "🏆 Система рейтингов\n"
        "🎓 Подготовка к ЕГЭ и ОГЭ\n"
        "💯 Абсолютно бесплатно\n\n"
        "🌐 Сайт: https://examflow.ru\n"
        "📧 Поддержка: @ExamFlowSupport\n\n"
        "Версия: 2.0\n"
        "Обновлено: январь 2025"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)


def main():
    """Запуск бота"""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в настройках Django")
        return
    
    application = Application.builder().token(token).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики callback-кнопок
    application.add_handler(CallbackQueryHandler(subjects_menu, pattern="subjects"))
    application.add_handler(CallbackQueryHandler(subject_detail, pattern="subject_\d+"))
    application.add_handler(CallbackQueryHandler(solve_subject_tasks, pattern="solve_\d+"))
    application.add_handler(CallbackQueryHandler(random_task, pattern="random_task"))
    application.add_handler(CallbackQueryHandler(random_subject_task, pattern="random_subject_\d+"))
    application.add_handler(CallbackQueryHandler(show_answer, pattern="answer_\d+"))
    application.add_handler(CallbackQueryHandler(mark_correct, pattern="correct_\d+"))
    application.add_handler(CallbackQueryHandler(mark_incorrect, pattern="incorrect_\d+"))
    application.add_handler(CallbackQueryHandler(mark_understood, pattern="understood_\d+"))
    application.add_handler(CallbackQueryHandler(start, pattern="main_menu"))
    application.add_handler(CallbackQueryHandler(about, pattern="about"))
    application.add_handler(CallbackQueryHandler(progress, pattern="progress"))
    application.add_handler(CallbackQueryHandler(rating, pattern="rating"))
    
    # Запуск бота
    logger.info("🤖 ExamFlow Bot запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()