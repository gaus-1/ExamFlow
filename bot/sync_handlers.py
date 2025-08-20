import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore

logger = logging.getLogger(__name__)


def _menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Выбрать предмет", callback_data="subjects")],
        [InlineKeyboardButton("🎯 Случайное задание", callback_data="random_task")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
        [InlineKeyboardButton("🏆 Рейтинг", callback_data="rating")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
    ])


def start_sync(update, bot):
    text = (
        "🎓 Добро пожаловать в ExamFlow!\n\n"
        "Решайте задания, следите за прогрессом и готовьтесь к ЕГЭ/ОГЭ."
    )
    chat_id = update.effective_chat.id
    bot.send_message(chat_id=chat_id, text=text, reply_markup=_menu_keyboard())


def subjects_menu_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text="📚 Выберите предмет (в разработке)",
        reply_markup=_menu_keyboard()
    )


def random_task_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text="🎲 Случайное задание (в разработке)",
        reply_markup=_menu_keyboard()
    )


def progress_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text="📊 Ваш прогресс (в разработке)",
        reply_markup=_menu_keyboard()
    )


def rating_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text="🏆 Рейтинг (в разработке)",
        reply_markup=_menu_keyboard()
    )


def about_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text=(
            "ℹ️ О ExamFlow\n\n"
            "Материалы на основе ФИПИ. Мы не являемся официальным партнёром ФИПИ."
        ),
        reply_markup=_menu_keyboard()
    )


def handle_unknown_callback_sync(update, bot):
    chat_id = update.effective_chat.id
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        text="🤔 Неизвестная команда. Возвращаюсь в главное меню.",
        reply_markup=_menu_keyboard()
    )
"""
Синхронные обработчики для Telegram бота в webhook режиме

Эти функции работают без asyncio и могут быть вызваны из Django views
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from core.models import Subject, Task, UserProgress, UserRating, Achievement, UserProfile, Subscription
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


def get_or_create_user(telegram_user):
    """Получить или создать пользователя Django с профилем"""
    username = f"tg_{telegram_user.id}"
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': telegram_user.first_name or '',
            'last_name': telegram_user.last_name or '',
        }
    )
    
    # Создаем или получаем профиль
    profile, profile_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'telegram_id': str(telegram_user.id)
        }
    )
    
    # Создаем рейтинг если нужно
    rating, rating_created = UserRating.objects.get_or_create(user=user)
    
    # Добавляем достижение за первый запуск
    if created:
        Achievement.objects.create(
            user=user,
            name='Первые шаги',
            description='Запуск Telegram бота ExamFlow',
            icon='fas fa-rocket',
            color='#00ff88'
        )
    
    return user


def start_sync(update: Update, bot):
    """Синхронная версия команды /start"""
    try:
        user = get_or_create_user(update.effective_user)
        logger.info(f"Пользователь {update.effective_user.username or update.effective_user.id} запустил бота")
        
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
            "Я помогу вам эффективно подготовиться к ЕГЭ и ОГЭ с заданиями "
            "на основе открытых материалов ФИПИ.\n\n"
            "🎯 Решайте задания\n"
            "📊 Отслеживайте прогресс\n"
            "🏆 Соревнуйтесь с друзьями\n"
            "💡 Получайте рекомендации\n\n"
            "Выберите действие:"
        )
        
        if update.message:
            bot.send_message(
                chat_id=update.message.chat_id,
                text=welcome_text,
                reply_markup=reply_markup
            )
        elif update.callback_query:
            bot.edit_message_text(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id,
                text=welcome_text,
                reply_markup=reply_markup
            )
            update.callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в start_sync: {str(e)}")
        error_text = "❌ Произошла ошибка. Попробуйте позже или обратитесь в поддержку."
        try:
            if update.message:
                bot.send_message(chat_id=update.message.chat_id, text=error_text)
            elif update.callback_query:
                bot.edit_message_text(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=update.callback_query.message.message_id,
                    text=error_text
                )
        except:
            pass


def subjects_menu_sync(update: Update, bot):
    """Синхронная версия меню предметов"""
    try:
        query = update.callback_query
        query.answer()
        logger.info(f"Пользователь {update.effective_user.username or update.effective_user.id} открыл меню предметов")
        
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
        
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="📚 Выберите предмет для изучения:\n\nВ скобках указано количество доступных заданий.",
            reply_markup=reply_markup
        )
            
    except Exception as e:
        logger.error(f"Ошибка в subjects_menu_sync: {str(e)}")
        try:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="❌ Ошибка загрузки предметов. Попробуйте позже."
            )
        except:
            pass


def about_sync(update: Update, bot):
    """Синхронная версия информации о боте"""
    try:
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🌐 Открыть сайт", url="https://examflow.ru")],
            [InlineKeyboardButton("💳 Подписка", callback_data="subscription")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "ℹ️ О ExamFlow\n\n"
            "🎯 Задания на основе материалов ФИПИ\n"
            "🎤 Голосовые подсказки (Premium)\n"
            "🤖 ИИ персонализация (Premium)\n"
            "📊 Персональный прогресс\n"
            "🏆 Система рейтингов\n"
            "🎓 Подготовка к ЕГЭ и ОГЭ\n\n"
            "🆓 Бесплатно: 5 заданий/день\n"
            "👑 Premium: безлимитные задания\n\n"
            "🌐 Сайт: https://examflow.ru\n"
            "📧 Поддержка: @ExamFlowSupport\n\n"
            "Версия: 3.0\n"
            "Обновлено: январь 2025"
        )
        
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка в about_sync: {str(e)}")


def progress_sync(update: Update, bot):
    """Синхронная версия прогресса пользователя"""
    try:
        query = update.callback_query
        query.answer()
        
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
        
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка в progress_sync: {str(e)}")


def rating_sync(update: Update, bot):
    """Синхронная версия рейтинга пользователей"""
    try:
        query = update.callback_query
        query.answer()
        
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
        
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка в rating_sync: {str(e)}")


def random_task_sync(update: Update, bot):
    """Синхронная версия случайного задания"""
    try:
        query = update.callback_query
        query.answer()
        
        user = get_or_create_user(update.effective_user)
        task = Task.objects.order_by('?').first()
        
        if task:
            show_task_sync(query, task, user, bot)
        else:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="❌ Задания пока не загружены. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
                ]])
            )
        
    except Exception as e:
        logger.error(f"Ошибка в random_task_sync: {str(e)}")


def show_task_sync(query, task, user, bot):
    """Синхронная версия показа задания"""
    try:
        difficulty_stars = "⭐" * task.difficulty
        difficulty_text = ["Лёгкое", "Среднее", "Сложное"][task.difficulty - 1] if task.difficulty <= 3 else "Очень сложное"
        
        # Проверить, решал ли пользователь это задание
        progress = UserProgress.objects.filter(user=user, task=task).first()
        
        # Проверяем подписку и лимиты
        profile = UserProfile.objects.get(user=user)
        
        keyboard = [
            [InlineKeyboardButton("✅ Показать ответ", callback_data=f"answer_{task.id}")],
            [InlineKeyboardButton("👍 Знаю", callback_data=f"correct_{task.id}")],
            [InlineKeyboardButton("👎 Не знаю", callback_data=f"incorrect_{task.id}")],
        ]
        
        # Добавляем кнопку голосовой подсказки
        if profile.is_premium:
            keyboard.append([InlineKeyboardButton("🎤 Голосовая подсказка", callback_data="voice_hint")])
        else:
            keyboard.append([InlineKeyboardButton("🎤 Голос (Premium)", callback_data="voice_hint")])
        
        keyboard.extend([
            [InlineKeyboardButton("🎯 Другое задание", callback_data="random_task")],
            [InlineKeyboardButton("🔙 К предмету", callback_data=f"subject_{task.subject.id}")]
        ])
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
        
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_task_sync: {str(e)}")


def handle_unknown_callback_sync(update: Update, bot):
    """Синхронная версия обработчика неизвестных callback'ов"""
    try:
        query = update.callback_query
        query.answer("🤔 Неизвестная команда, возвращаюсь в главное меню...")
        
        logger.warning(f"Unknown callback data: {query.data}")
        
        # Перенаправляем в главное меню
        start_sync(update, bot)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_unknown_callback_sync: {str(e)}")
