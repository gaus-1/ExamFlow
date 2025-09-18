"""
Обработчики команд для Telegram бота

Содержит основную логику бота:
- Команды (/start, /help, /subjects, /stats)
- Обработку callback-запросов (кнопки)
- Решение заданий через бота
- Синхронизацию с веб-сайтом
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async
from telegram.ext import ContextTypes
from django.conf import settings
from learning.models import (
    Subject, Task, UserProgress, UserRating
)
from core.models import UnifiedProfile
from core.services.unified_profile import UnifiedProfileService
from core.services.chat_session import ChatSessionService
from django.utils import timezone
from ai.services import AiService
from .gamification import TelegramGamification
from .utils.text_utils import clean_markdown_text, clean_log_text, format_ai_response

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация системы геймификации
gamification = TelegramGamification()

# Функция clean_markdown_text перенесена в utils/text_utils.py

def create_standard_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """
    Создает стандартную кнопку бота в стиле 2025
    """
    return InlineKeyboardButton(
        text=text.upper(),  # Заглавные буквы для единообразия
        callback_data=callback_data
    )

def create_main_message(text: str) -> str:
    """
    Создает основное сообщение бота в стиле 2025
    """
    return "**{text}**"

def create_warning_message(text: str) -> str:
    """
    Создает предупреждающее сообщение бота в стиле 2025
    """
    return "⚠️ {text}"

# Синхронные функции БД, обёрнутые для безопасного вызова в async-контексте

@sync_to_async
def db_check_connection() -> bool:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return True

# Новые функции для работы с Unified Profile

@sync_to_async
def db_get_or_create_unified_profile(telegram_user):
    """Получает или создает UnifiedProfile для пользователя Telegram"""
    return UnifiedProfileService.get_or_create_profile(
        telegram_id=telegram_user.id,
        telegram_username=telegram_user.username,
        user=None  # Django User будет создан позже при необходимости
    )

@sync_to_async
def db_update_profile_activity(profile):
    """Обновляет время последней активности профиля"""
    profile.last_activity = timezone.now()
    profile.save()

@sync_to_async
def db_get_profile_progress(profile):
    """Получает сводку прогресса пользователя"""
    return {
        'level': profile.level,
        'experience_points': profile.experience_points,
        'total_solved': profile.total_solved,
        'current_streak': profile.current_streak,
        'best_streak': profile.best_streak,
        'achievements_count': len(profile.achievements) if profile.achievements else 0
    }

@sync_to_async
def db_get_or_create_chat_session(telegram_user, django_user=None):
    """Получает или создает сессию чата для пользователя"""
    return ChatSessionService.get_or_create_session(
        telegram_id=telegram_user.id,
        user=django_user
    )

@sync_to_async
def db_add_user_message_to_session(session, message):
    """Добавляет сообщение пользователя в сессию"""
    ChatSessionService.add_user_message(session, message)

@sync_to_async
def db_add_assistant_message_to_session(session, message):
    """Добавляет ответ ассистента в сессию"""
    ChatSessionService.add_assistant_message(session, message)

@sync_to_async
def db_create_enhanced_prompt(user_message, session):
    """Создает расширенный промпт с контекстом"""
    return ChatSessionService.create_enhanced_prompt(user_message, session)

@sync_to_async
def db_clear_chat_session_context(telegram_user):
    """Очищает контекст сессии пользователя"""
    session = ChatSessionService.get_or_create_session(telegram_id=telegram_user.id)
    ChatSessionService.clear_session_context(session)

# ИИ сервис для асинхронного использования

@sync_to_async
def get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:
    """Получает персонализированный ответ от ИИ с использованием RAG системы"""
    try:
        # Используем базовый AI-сервис
        from ai.services import AiService
        ai_service = AiService()

        # Получаем ответ от AI
        if user is None:
            return "❌ Ошибка: пользователь не определен"
        result = ai_service.ask(prompt, user)

        if 'error' in result:
            return f"❌ Ошибка: {result['error']}"

        response = result['response']

        # Убираем фразу о провайдере ИИ

        # Добавляем персональные рекомендации
        personalization_data = result.get('personalization_data', {})
        if personalization_data:
            # Добавляем слабые темы
            weak_topics = personalization_data.get('weak_topics', [])
            if weak_topics:
                response += "\n\n⚠️ **Ваши слабые темы:**"
                for topic in weak_topics[:2]:
                    subject = topic.get('subject', 'Неизвестно')
                    failed_tasks = topic.get('failed_tasks', 0)
                    response += "\n• {subject}: {failed_tasks} проваленных заданий"

            # Добавляем рекомендации
            recommendations = personalization_data.get('recommendations', [])
            if recommendations:
                response += "\n\n💡 **Персональные рекомендации:**"
                for rec in recommendations[:2]:
                    title = rec.get('title', 'Рекомендация')
                    action = rec.get('action', '')
                    response += "\n• {title}"
                    if action:
                        response += " - {action}"

        return response

    except Exception as e:
        logger.error("Ошибка при получении персонализированного ответа от ИИ: {e}")
        return "❌ Ошибка ИИ-ассистента: {str(e)}"

@sync_to_async
def db_get_all_subjects_with_tasks():
    """Получает все предметы с количеством заданий"""
    from django.db.models import Count
    subjects = Subject.objects.annotate(  # type: ignore
        tasks_count=Count('task')
    ).filter(tasks_count__gt=0).values('id', 'name', 'exam_type', 'tasks_count')  # type: ignore
    return list(subjects)

@sync_to_async
def db_get_subject_ids():
    return list(
        Task.objects.values_list(  # type: ignore
            'subject_id',
            flat=True).distinct())  # type: ignore

@sync_to_async
def db_get_subjects_by_ids(ids):
    return list(Subject.objects.filter(id__in=ids))  # type: ignore

@sync_to_async
def db_count_tasks_for_subject(subject_id: int) -> int:
    return Task.objects.filter(subject_id=subject_id).count()  # type: ignore  # type: ignore

@sync_to_async
def db_get_tasks_by_subject(subject_id: int):
    return list(Task.objects.filter(subject_id=subject_id))  # type: ignore

@sync_to_async
def db_get_all_tasks():
    return list(Task.objects.all())  # type: ignore

@sync_to_async
def db_get_subject_name_for_task(task):
    """Получает название предмета для задания"""
    return task.subject.name if task.subject else "Неизвестный предмет"

@sync_to_async
def db_get_subject_by_id(subject_id: int):
    """Получает предмет по ID"""
    try:
        return Subject.objects.get(id=subject_id)  # type: ignore
    except Subject.DoesNotExist:  # type: ignore
        return None

@sync_to_async
def db_get_subject_name(subject_id: int) -> str:
    name = Subject.objects.filter(  # type: ignore
        id=subject_id).values_list(
        'name', flat=True).first()  # type: ignore
    return name or "Предмет"

@sync_to_async
def db_set_current_task_id(user, task_id: int):
    set_current_task_id(user, task_id)

@sync_to_async
def db_get_or_create_user(telegram_user):
    return get_or_create_user(telegram_user)

@sync_to_async
def db_get_task_by_id(task_id: int):
    return Task.objects.get(id=task_id)  # type: ignore

@sync_to_async
def db_save_progress(user, task, user_answer: str, is_correct: bool):
    progress, created = UserProgress.objects.get_or_create(  # type: ignore
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
    return progress

@sync_to_async
def db_update_rating_points(user, is_correct: bool):
    rating, _ = UserRating.objects.get_or_create(user=user)  # type: ignore
    if is_correct:
        rating.total_points += 10
        rating.correct_answers += 1
    else:
        rating.incorrect_answers += 1
    rating.total_attempts += 1
    rating.save()
    return rating

# Функция для получения текущего задания пользователя из профиля

def get_current_task_id(user):
    """Получает ID текущего задания из профиля пользователя"""
    try:
        profile = UserProfile.objects.get(user=user)  # type: ignore
        return profile.current_task_id
    except UserProfile.DoesNotExist:  # type: ignore
        return None

def set_current_task_id(user, task_id):
    """Устанавливает ID текущего задания в профиле пользователя"""
    try:
        profile = UserProfile.objects.get(user=user)  # type: ignore
        profile.current_task_id = task_id
        profile.save()
        logger.info(
            "Установлен current_task_id: {task_id} для пользователя {user.username}")
    except Exception as e:
        logger.error("Профиль не найден для пользователя {user.username}: {e}")

def get_or_create_user(telegram_user):
    """
    Получить или создать пользователя Django с профилем

    Создает пользователя с telegram_id
    Автоматически создает профиль и рейтинг
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user, created = User.objects.get_or_create(  # type: ignore
        telegram_id=telegram_user.id,
        defaults={
            'telegram_first_name': telegram_user.first_name or '',
            'telegram_last_name': telegram_user.last_name or '',
            'telegram_username': telegram_user.username or '',
        }
    )

    # Создаем или получаем профиль (используем core.models.UserProfile)
    from core.models import UserProfile
    profile, profile_created = UserProfile.objects.get_or_create(  # type: ignore
        user=user,
        defaults={}
    )

    # Создаем рейтинг если нужно
    rating, rating_created = UserRating.objects.get_or_create(user=user)  # type: ignore

    return user, created

# ============================================================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start - приветствие и главное меню

    Создает пользователя если его нет
    Показывает основные возможности бота

    Работает как с командами, так и с callback-запросами
    """
    # Определяем тип обновления
    is_callback = update.callback_query is not None
    user = update.effective_user

    # Создаем нижнее закрепленное меню с 4 кнопками
    if not is_callback:  # Только при команде /start
        try:
            from telegram import ReplyKeyboardMarkup, KeyboardButton
            keyboard = [
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, resize_keyboard=True, one_time_keyboard=False)

            if update.message:  # type: ignore
                await update.message.reply_text(
                    "🎯 **Нижнее меню настроено!**\n\n"
                    "Теперь у вас есть быстрый доступ к основным функциям:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error("Ошибка создания нижнего меню: {e}")

    # Получаем или создаем UnifiedProfile
    try:
        profile = await db_get_or_create_unified_profile(user)
        await db_update_profile_activity(profile)
        logger.info("UnifiedProfile получен/создан для пользователя {user.id}")

        # Получаем прогресс пользователя для персонализации
        progress = await db_get_profile_progress(profile)

        # Формируем персонализированное приветствие
        level_info = "Уровень {progress['level']}" if progress.get(
            'level', 1) > 1 else "Новичок"
        xp_info = "• {progress['experience_points']} XP" if progress.get(
            'experience_points', 0) > 0 else ""
        solved_info = "• Решено: {progress['total_solved']}" if progress.get(
            'total_solved', 0) > 0 else ""

        stats_line = "\n{level_info} {xp_info} {solved_info}".strip() if any([
            progress.get('level', 1) > 1,
            progress.get('experience_points', 0) > 0,
            progress.get('total_solved', 0) > 0
        ]) else ""

        welcome_text = """
🎯 **ExamFlow 2.0**

Привет, {profile.display_name}!{stats_line}

Умная платформа подготовки к ЕГЭ с ИИ-ассистентом

🤖 **Задай любой вопрос** — получи персональный ответ
📚 **Практика** — тысячи заданий с проверкой
🏆 **Прогресс** — отслеживай достижения

Что тебя интересует?
"""

        keyboard = [
            [create_standard_button("🤖 СПРОСИТЬ ИИ", "ai_chat")],
            [create_standard_button("📚 ПРАКТИКА", "subjects"),
             create_standard_button("🏆 ПРОГРЕСС", "stats")],
            [InlineKeyboardButton(
                "🌐 САЙТ", url="https://examflow.onrender.com")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if is_callback:
            if update.callback_query:  # type: ignore
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            if update.message:  # type: ignore
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

        logger.info("Пользователь {user.id} запустил бота")

    except Exception as e:
        logger.error("Ошибка в команде start: {e}")
        error_text = "❌ Произошла ошибка. Попробуйте позже."
        if is_callback:
            if update.callback_query:  # type: ignore
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(error_text)
        else:
            if update.message:  # type: ignore
                await update.message.reply_text(error_text)

# ============================================================================
# ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ
# ============================================================================

# Импортируем обработчики персонализации

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Возвращает пользователя в главное меню
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    welcome_text = """
🎯 **ExamFlow 2.0**

Привет, {update.effective_user.first_name}!

Умная платформа подготовки к ЕГЭ с ИИ-ассистентом

🤖 **Задай любой вопрос** — получи мгновенный ответ
📚 **Практика** — тысячи заданий с проверкой
🏆 **Прогресс** — отслеживай достижения

Что тебя интересует?
"""

    keyboard = [
        [create_standard_button("🔐 ВОЙТИ ЧЕРЕЗ TELEGRAM", "telegram_auth")],
        [create_standard_button("🤖 СПРОСИТЬ ИИ", "ai_chat")],
        [create_standard_button("📚 ПРАКТИКА", "subjects"),
         create_standard_button("🏆 ПРОГРЕСС", "stats")],
        [InlineKeyboardButton(
            "🌐 САЙТ", url="https://examflow.onrender.com")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=None
        )
    except Exception as edit_err:
        logger.warning(
            "main_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode=None
            )
        except Exception as send_err:
            logger.error("main_menu: send_message тоже не удался: {send_err}")

async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает меню выбора предметов

    Отображает все доступные предметы с количеством заданий
    """
    try:
        query = update.callback_query
        if not query:  # type: ignore
            return
        await query.answer()

        # Получаем все предметы с количеством заданий
        try:
            subjects = await db_get_all_subjects_with_tasks()
            if not subjects:
                await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
                return
        except Exception as e:
            logger.error("subjects_menu: ошибка получения предметов: {e}")
            await query.edit_message_text("❌ Ошибка загрузки предметов. Попробуйте позже.")
            return

        if not subjects:
            await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
            return

        # Сортируем предметы по количеству заданий (больше заданий - выше)
        subjects_sorted = sorted(subjects, key=lambda x: x['tasks_count'], reverse=True)

        keyboard = []
        for subject in subjects_sorted[:15]:  # Показываем топ-15 предметов
            button_text = "{subject['name']} ({subject['tasks_count']} заданий)"
            keyboard.append([InlineKeyboardButton(
                button_text, callback_data="subject_{subject['id']}")])

        # Добавляем кнопки навигации
        keyboard.append([
            InlineKeyboardButton("🏠 Главная", callback_data="main_menu")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                "📚 **Практика по предметам**\n\n"
                "**{len(subjects)}** предметов • **{sum(s['tasks_count'] for s in subjects)}** заданий\n\n"
                "Выбери предмет для изучения:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as edit_err:
            logger.warning(
                "subjects_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,  # type: ignore
                    text="📚 **ВЫБЕРИТЕ ПРЕДМЕТ ДЛЯ ИЗУЧЕНИЯ**\n\n"
                         "Доступно **{len(subjects)} предметов** с **{sum(s['tasks_count'] for s in subjects)} заданиями**\n\n"
                         "Предметы отсортированы по количеству заданий:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as send_err:
                logger.error("subjects_menu: send_message тоже не удался: {send_err}")

    except Exception as e:
        logger.error("Ошибка в subjects_menu: {e}")
        try:
            await query.edit_message_text("❌ Не удалось загрузить предметы. Попробуйте позже.")  # type: ignore
        except Exception:
            pass

async def show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает случайное задание выбранного предмета
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    subject_id = int(query.data.split('_')[1])  # type: ignore

    # Получаем информацию о предмете
    subject = await db_get_subject_by_id(subject_id)
    if not subject:
        await query.edit_message_text("❌ Предмет не найден")  # type: ignore
        return

    # Получаем список заданий для предмета
    tasks = await db_get_tasks_by_subject(subject_id)
    if not tasks:
        await query.edit_message_text(  # type: ignore
            "❌ В предмете **{subject.name}** пока нет заданий",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
            ]]),
            parse_mode='Markdown'
        )
        return

    # Выбираем случайное задание
    import random
    task = random.choice(list(tasks))

    # Устанавливаем текущее задание в профиле пользователя
    user, _ = await db_get_or_create_user(update.effective_user)
    await db_set_current_task_id(user, task.id)
    logger.info("show_subject_topics: установлен current_task_id: {task.id}")

    # Формируем текст задания
    task_text = """
📝 **ЗАДАНИЕ №{task.id}**
📚 **Предмет:** {subject.name} ({subject.exam_type})

**{task.title}**

**Условие:**

**Сложность:** {'⭐' * task.difficulty} ({task.difficulty}/5)
**Источник:** {task.source or 'Не указан'}

💡 **Введите ваш ответ или используйте кнопки ниже:**
"""

    keyboard = [
    ]

    try:
        await query.edit_message_text(  # type: ignore
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as edit_err:
        logger.warning(
            "show_subject_topics: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as send_err:
            logger.error(
                "show_subject_topics: send_message тоже не удался: {send_err}")

async def random_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает случайное задание из всех доступных
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    # Получаем все задания
    tasks = await db_get_all_tasks()
    if not tasks:
        await query.edit_message_text("❌ Задания пока не загружены")
        return

    import random
    task = random.choice(list(tasks))

    # Сохраняем текущее задание в профиль пользователя
    try:
        user, _ = await db_get_or_create_user(update.effective_user)
        await db_set_current_task_id(user, task.id)
        logger.info(
            "random_task: установлен current_task_id: {task.id} для пользователя {user.username}")
    except Exception as prof_err:
        logger.warning("Не удалось сохранить current_task_id в профиль: {prof_err}")

    # Получаем название предмета безопасно
    subject_name = await db_get_subject_name_for_task(task)

    # Формируем текст задания
    task_text = """
📝 **Задание №{task.id}**
**Предмет:** {subject_name}

**Заголовок:** {task.title}

**Условие:**

Введите ваш ответ:
"""

    keyboard = [
    ]

    try:
        await query.edit_message_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_err:
        logger.warning(
            "random_task: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error("random_task: send_message тоже не удался: {send_err}")

async def show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает правильный ответ на задание
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    # Извлекаем ID задания из callback_data
    task_id = int(query.data.split('_')[1])  # type: ignore

    # Получаем задание
    try:
        task = await db_get_task_by_id(task_id)
    except Exception:
        await query.edit_message_text("❌ Задание не найдено")
        return

    # Получаем название предмета безопасно
    subject_name = await db_get_subject_name_for_task(task)

    answer_text = """
💡 **Ответ на задание №{task.id}**

**Предмет:** {subject_name}
**Заголовок:** {task.title}

✅ **Правильный ответ:** {task.answer or 'Ответ не указан'}

**Условие:**

**Источник:** {task.source or 'Не указан'}
"""

    keyboard = [
    ]

    try:
        await query.edit_message_text(
            answer_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_err:
        logger.warning(
            "show_answer: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=answer_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error("show_answer: send_message тоже не удался: {send_err}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает статистику пользователя из Unified Profile

    Отображает уровень, опыт, решенные задания, серии, достижения
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    # Получаем UnifiedProfile пользователя
    profile = await db_get_or_create_unified_profile(update.effective_user)
    await db_update_profile_activity(profile)

    # Получаем полную статистику
    await db_get_profile_progress(profile)

    # Подсчитываем количество достижений
    achievements_count = len(
        profile.achievements) if profile.achievements else 0  # type: ignore

    # Формируем красивую статистику в стиле ExamFlow 2.0
    stats_text = """
🏆 **Твой прогресс в ExamFlow**

👤 **{profile.display_name}**
🎯 **Уровень {profile.level}** • {profile.experience_points} XP
📈 **До следующего уровня:** {profile.experience_to_next_level} XP

📚 **Статистика решений:**
✅ Решено задач: **{profile.total_solved}**
🔥 Текущая серия: **{profile.current_streak} дней**
⭐ Лучшая серия: **{profile.best_streak} дней**

🏅 **Достижения:** {achievements_count}

💡 **Продолжай решать задания для роста!**
"""
    keyboard = [
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def learning_plan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает персональный план обучения пользователя

    Использует RAG систему для анализа прогресса и рекомендаций
    """
    try:
        query = update.callback_query
        if not query:  # type: ignore
            return
        await query.answer()

        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)
        if not user:
            await query.edit_message_text("❌ Не удалось получить данные пользователя.")
            return

        # Получаем план обучения через RAG
        ai_service = AiService()
        learning_plan = await sync_to_async(ai_service.get_personalized_learning_plan)(user)

        if 'error' in learning_plan:
            await query.edit_message_text("❌ Ошибка: {learning_plan['error']}")
            return

        # Формируем текст плана
        plan_text = """
🎓 **ТВОЙ ПЕРСОНАЛЬНЫЙ ПЛАН ОБУЧЕНИЯ**

📊 **Текущий уровень:** {learning_plan.get('current_level', 1)}/5
🎯 **Точность:** {learning_plan.get('accuracy', 0)}%
📚 **Решено заданий:** {learning_plan.get('total_tasks', 0)}

🔴 **Слабые темы:**
"""

        weak_topics = learning_plan.get('weak_topics', [])
        if weak_topics:
            for topic in weak_topics[:3]:
                plan_text += "• {topic}\n"
        else:
            plan_text += "• Нет данных\n"

        plan_text += "\n🟢 **Сильные темы:**\n"
        strong_topics = learning_plan.get('strong_topics', [])
        if strong_topics:
            for topic in strong_topics[:3]:
                plan_text += "• {topic}\n"
        else:
            plan_text += "• Нет данных\n"

        plan_text += "\n💡 **Рекомендации:**\n"
        recommendations = learning_plan.get('recommendations', [])
        if recommendations:
            for rec in recommendations[:3]:
                plan_text += "• {rec['title']}\n"
        else:
            plan_text += "• Начните с базовых заданий\n"

        plan_text += """

📅 **Цели:**
• Ежедневно: {learning_plan.get('daily_goal', 3)} заданий
• Еженедельно: {learning_plan.get('weekly_goal', 15)} заданий

🎯 **Следующие шаги:**\n"""

        next_steps = learning_plan.get('next_steps', [])
        if next_steps:
            for step in next_steps[:3]:
                plan_text += "• {step['description']}\n"
        else:
            plan_text += "• Продолжайте решать задания\n"

        # Кнопки для навигации
        keyboard = [
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            plan_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        logger.info("Пользователь {user.id} получил план обучения")

    except Exception as e:
        logger.error("Ошибка в learning_plan_menu: {e}")
        await query.edit_message_text(  # type: ignore
            "❌ Произошла ошибка при получении плана обучения. Попробуйте позже."
        )

# ============================================================================
# ИИ ОБРАБОТЧИКИ
# ============================================================================

async def ai_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для кнопки "Спросить ИИ" с персонализацией
    Показывает меню с возможностями ИИ или помогает с конкретным заданием

    Работает как с callback-запросами, так и с текстовыми сообщениями
    """
    try:
        # Определяем тип обновления
        is_callback = update.callback_query is not None

        if is_callback:
            query = update.callback_query
            if not query:  # type: ignore
                return
            await query.answer()
            user = update.effective_user
        else:
            query = None
            user = update.effective_user

        # Получаем UnifiedProfile пользователя
        profile = await db_get_or_create_unified_profile(user)
        await db_update_profile_activity(profile)

        # Проверяем формат callback_data (только для callback-запросов)
        if is_callback and query.data and query.data.startswith(  # type: ignore
                'ai_help_') and '_' in query.data:  # type: ignore
            # Помощь с конкретным заданием
            try:
                task_id = int(query.data.split('_')[2])  # type: ignore
                task = await db_get_task_by_id(task_id)

                if not task:
                    await query.edit_message_text("❌ Задание не найдено.")  # type: ignore
                    return

                # Показываем сообщение о том, что AI думает
                thinking_message = await query.edit_message_text(  # type: ignore
                    "🤔 AI анализирует задание и ваш прогресс...\n\n"
                    "Это может занять несколько секунд.",
                    parse_mode=None
                )

                # Получаем или создаем Django User для совместимости с AI сервисом
                django_user, created = await db_get_or_create_user(user)

                ai_response = await get_ai_response(
                    "Объясни, как решить это задание. Дай пошаговое решение с объяснением каждого шага. "
                    "Учитывай мой текущий уровень и слабые темы.",
                    task_type='task_help',
                    user=django_user,
                    task=task
                )

                # Формируем ответ с кнопками
                response_text = """
🤖 **AI ПОМОЩЬ ДЛЯ ЗАДАНИЯ №{task.id}**

---
💡 **Дополнительные возможности:**
"""

                keyboard = [
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Очищаем текст от проблемных символов Markdown
                clean_response = clean_markdown_text(response_text)

                await thinking_message.edit_text(  # type: ignore
                    clean_response,
                    reply_markup=None,
                    parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
                )

                logger.info(
                    "Пользователь {profile.telegram_id} получил персонализированную AI помощь для задания {task.id}")

            except (IndexError, ValueError) as e:
                logger.error("Ошибка парсинга task_id в ai_help_handler: {e}")
                await query.edit_message_text("❌ Ошибка формата данных. Попробуйте еще раз.")  # type: ignore
                return
        else:
            # Общее меню ИИ с персонализацией
            ai_menu_text = """
🤖 **ИИ-ассистент ExamFlow**

Задай любой вопрос по ЕГЭ — получи персональный ответ

💬 **Просто напиши сообщение** с вопросом
📚 **Объяснение тем** — с учетом твоего уровня
💡 **Помощь с заданиями** — пошаговые решения
🎯 **Советы по подготовке** — персональные рекомендации

**Пример вопросов:**
• Как решать квадратные уравнения?
• Объясни теорию вероятности
• Подготовка к ЕГЭ по физике
"""

            keyboard = [
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if is_callback:
                await query.edit_message_text(  # type: ignore
                    ai_menu_text,
                    reply_markup=reply_markup,
                    parse_mode=None
                )
            else:
                if update.message:  # type: ignore
                    await update.message.reply_text(
                        ai_menu_text,
                        reply_markup=reply_markup,
                        parse_mode=None
                    )

    except Exception as e:
        logger.error("Ошибка в ai_help_handler: {e}")
        if is_callback and query:
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore
        else:
            if update.message:  # type: ignore
                await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def ai_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для объяснения темы от ИИ
    """
    try:
        query = update.callback_query
        await query.answer()  # type: ignore

        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)

        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(  # type: ignore
            "🤔 AI анализирует ваш прогресс и готовит объяснение...\n\n"
            "Это может занять несколько секунд.",
            parse_mode=None
        )

        # Получаем объяснение от AI
        ai_response = await get_ai_response(
            "Объясни простыми словами основные темы по математике, которые нужны для ЕГЭ. "
            "Дай краткое, но понятное объяснение с примерами.",
            task_type='topic_explanation',
            user=user
        )

        # Формируем ответ с кнопками
        response_text = """
📚 **ОБЪЯСНЕНИЕ ТЕМ ОТ ИИ**

---
💡 **Хотите получить подсказку к конкретному заданию?**
"""

        keyboard = [
        ]
        InlineKeyboardMarkup(keyboard)

        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)

        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=None,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )

        logger.info("Пользователь {user.id} получил объяснение темы от ИИ")

    except Exception as e:
        logger.error("Ошибка в ai_explain_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

async def ai_personal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для персональных советов от ИИ
    """
    try:
        query = update.callback_query
        await query.answer()  # type: ignore    

        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)

        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(  # type: ignore
            "🎯 AI анализирует ваш прогресс и готовит персональные советы...\n\n"
            "Это может занять несколько секунд.",
            parse_mode=None
        )

        # Получаем персональные советы от AI
        ai_response = await get_ai_response(
            "Проанализируй мой прогресс в обучении и дай персональные советы "
            "по подготовке к ЕГЭ. Что мне нужно подтянуть? Какие темы повторить?",
            task_type='personal_advice',
            user=user
        )

        # Формируем ответ с кнопками
        response_text = """
**ПЕРСОНАЛЬНЫЕ СОВЕТЫ ОТ ИИ**

---
📚 **Хотите получить объяснение конкретной темы?**
"""

        keyboard = [
        ]
        InlineKeyboardMarkup(keyboard)

        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)

        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=None,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )

        logger.info("Пользователь {user.id} получил персональные советы от ИИ")

    except Exception as e:
        logger.error("Ошибка в ai_personal_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

async def ai_hint_general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Общий обработчик для подсказок от ИИ (когда нет конкретного задания)
    """
    try:
        query = update.callback_query
        await query.answer()  # type: ignore

        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)

        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(  # type: ignore
            "💡 AI готовит общую подсказку...\n\n"
            "Это может занять несколько секунд.",
            parse_mode=None
        )

        # Получаем общую подсказку от AI
        ai_response = await get_ai_response(
            "Дай общие советы по решению математических задач ЕГЭ. "
            "Какие подходы использовать? На что обращать внимание?",
            task_type='general_hint',
            user=user
        )

        # Формируем ответ с кнопками
        response_text = """
💡 **ОБЩИЕ ПОДСКАЗКИ ПО РЕШЕНИЮ ЗАДАЧ**

---
🎯 **Хотите получить персональные советы?**
"""

        keyboard = [
        ]
        InlineKeyboardMarkup(keyboard)

        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)

        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=None,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )

        logger.info("Пользователь {user.id} получил общую подсказку от ИИ")

    except Exception as e:
        logger.error("Ошибка в ai_hint_general_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

# ============================================================================
# ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================================================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для прямого общения с ИИ и нижнего меню
    """
    try:
        if not update.message:  # type: ignore
            return
        user_message = update.message.text
        if not user_message:
            return

        update.effective_user

        # Проверяем, что сообщение не является командой
        if user_message.startswith('/'):
            return

        # Обработка нижнего меню
        if user_message in ["🤖 ИИ", "📚 Практика", "🏆 Прогресс", "🎯 Главная"]:
            await handle_menu_button(update, context, user_message)
            return

        # Если это не кнопка меню, то это вопрос к ИИ
        await handle_ai_message(update, context)

    except Exception as e:
        logger.error("Ошибка в handle_text_message: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore       
                text="❌ Произошла ошибка. Попробуйте позже.",
                reply_to_message_id=update.message.message_id  # type: ignore
            )
        except Exception as send_err:
            logger.error("Не удалось отправить сообщение об ошибке: {send_err}")

async def handle_menu_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        button_text: str):
    """
    Обрабатывает нажатия кнопок нижнего меню
    """
    try:
        if button_text == "🎯 Главная":
            await start(update, context)
        elif button_text == "🤖 ИИ":
            await ai_help_handler(update, context)
        elif button_text == "📚 Практика":
            await subjects_menu(update, context)
        elif button_text == "🏆 Прогресс":
            await show_stats(update, context)
    except Exception as e:
        logger.error("Ошибка в handle_menu_button: {e}")
        if update.message:  # type: ignore
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для прямого общения с ИИ
    """
    try:
        if not update.message:  # type: ignore
            return
        user_message = update.message.text
        if not user_message:
            return

        user = update.effective_user

        # Получаем UnifiedProfile пользователя
        profile = await db_get_or_create_unified_profile(user)
        await db_update_profile_activity(profile)

        # Получаем или создаем Django User для совместимости с AI сервисом
        django_user, created = await db_get_or_create_user(user)

        # Получаем или создаем сессию чата
        chat_session = await db_get_or_create_chat_session(user, django_user)

        # Показываем сообщение о том, что AI думает
        thinking_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore
            text="🤔 AI анализирует ваш вопрос...\n\nЭто может занять несколько секунд.",
            reply_to_message_id=update.message.message_id
        )

        # Добавляем сообщение пользователя в контекст
        await db_add_user_message_to_session(chat_session, user_message)

        # Создаем расширенный промпт с контекстом
        enhanced_prompt = await db_create_enhanced_prompt(user_message, chat_session)


        # Получаем ответ от AI с контекстом
        ai_response = await get_ai_response(  # type: ignore
            await enhanced_prompt,  # type: ignore
            task_type='direct_question',
            user=django_user
        )

        # Добавляем ответ ассистента в контекст
        await db_add_assistant_message_to_session(chat_session, ai_response)

        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(ai_response)

        # Формируем ответ с кнопками
        response_text = """
**ОТВЕТ ИИ**

---
💡 **Дополнительные возможности:**
"""

        keyboard = [
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Обновляем сообщение с ответом
        await thinking_message.edit_text(  # type: ignore
            response_text,
            reply_markup=reply_markup,
            parse_mode=None
        )

        # Логируем с очищенным текстом
        clean_message = clean_log_text(user_message)
        logger.info(
            f"Пользователь {profile.telegram_id} получил прямой ответ от ИИ на вопрос: {clean_message}")

    except Exception as e:  # type: ignore
        logger.error("Ошибка в handle_ai_message: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text="❌ Произошла ошибка при обработке вашего вопроса. Попробуйте позже или используйте кнопку '🤖 Спросить ИИ'.",
                reply_to_message_id=update.message.message_id  # type: ignore
            )
        except Exception as send_err:
            logger.error("Не удалось отправить сообщение об ошибке: {send_err}")

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def search_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик поиска по предмету
    """
    query = update.callback_query
    await query.answer()  # type: ignore

    await query.edit_message_text(  # type: ignore
        "🔍 **ПОИСК ПО ПРЕДМЕТУ**\n\n"
        "Введите название предмета или его часть:",
        reply_markup=InlineKeyboardMarkup([[  # type: ignore
            InlineKeyboardButton("🔙 Назад", callback_data="subjects")
        ]]),
        parse_mode='Markdown'
    )

async def random_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик случайного предмета
    """
    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        # Получаем случайный предмет с заданиями
        subjects = await db_get_all_subjects_with_tasks()
        if not subjects:
            await query.edit_message_text("❌ Нет доступных предметов")  # type: ignore 
            return

        import random
        random_subject = random.choice(subjects)

        # Показываем случайный предмет
        await query.edit_message_text(  # type: ignore
            "🎯 **СЛУЧАЙНЫЙ ПРЕДМЕТ**\n\n"
            "📚 **{random_subject['name']}**\n"
            "📝 **Заданий:** {random_subject['tasks_count']}\n"
            "🎓 **Тип:** {random_subject['exam_type']}\n\n"
            "Хотите решить задание по этому предмету?",
            reply_markup=InlineKeyboardMarkup([  # type: ignore
            ]),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка в random_subject_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

async def show_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает задание по ID
    """
    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        task_id = int(query.data.split('_')[1])  # type: ignore
        task = await db_get_task_by_id(task_id)

        if not task:
            await query.edit_message_text("❌ Задание не найдено")  # type: ignore
            return

        # Получаем информацию о предмете
        subject = await db_get_subject_by_id(task.subject.id)
        subject_name = subject.name if subject else "Неизвестный предмет"

        # Формируем текст задания
        task_text = """
📝 **ЗАДАНИЕ №{task.id}**
📚 **Предмет:** {subject_name}

**{task.title}**

**Условие:**

**Сложность:** {'⭐' * task.difficulty} ({task.difficulty}/5)
**Источник:** {task.source or 'Не указан'}

💡 **Введите ваш ответ или используйте кнопки ниже:**
"""

        keyboard = [
        ]

        await query.edit_message_text(  # type: ignore
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),  # type: ignore
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка в show_task_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")  # type: ignore

async def clear_context_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для очистки контекста чата
    """
    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        user = update.effective_user

        # Очищаем контекст сессии
        await db_clear_chat_session_context(user)

        await query.edit_message_text(  # type: ignore
            "🧹 **Контекст очищен!**\n\n"
            "Теперь ИИ будет отвечать на ваши вопросы без учета предыдущего разговора.",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🏠 Главная", callback_data="main_menu")
            ]]),
            parse_mode='Markdown'
        )

        logger.info("Пользователь {user.id} очистил контекст чата")

    except Exception as e:
        logger.error("Ошибка при очистке контекста: {e}")
        await query.edit_message_text(  # type: ignore
            "❌ Произошла ошибка при очистке контекста. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🏠 Главная", callback_data="main_menu")
            ]])
        )

async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает неизвестные callback-запросы

    Логирует ошибку и показывает главное меню
    """
    query = update.callback_query
    await query.answer()  # type: ignore

    logger.warning("Неизвестный callback: {query.data}")

    await query.edit_message_text(  # type: ignore
        "❌ Неизвестная команда. Возвращаемся в главное меню.",
        reply_markup=InlineKeyboardMarkup([[  # type: ignore
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]])
    )

# 🔐 ОБРАБОТЧИКИ АУТЕНТИФИКАЦИИ

async def telegram_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Войти через Telegram"
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    user_id = update.effective_user.id  # type: ignore
    username = update.effective_user.username or "User"  # type: ignore
    first_name = update.effective_user.first_name or "User"  # type: ignore
    
    # Получаем настройки сайта
    from django.conf import settings
    site_url = getattr(settings, 'SITE_URL', 'https://examflow.ru')
    
    auth_text = f"""
🔐 **ВХОД ЧЕРЕЗ TELEGRAM**

Привет, {first_name}! 👋

Для полного доступа к функционалу ExamFlow необходимо авторизоваться через Telegram.

✨ **Что это даёт:**
• 🎯 Персональные рекомендации ИИ
• 📊 Отслеживание прогресса
• 🏆 Достижения и рейтинги
• 💎 Премиум функции

**Нажмите кнопку ниже для входа:**
"""

    keyboard = [
        [InlineKeyboardButton(
            "🚀 ВОЙТИ ЧЕРЕЗ TELEGRAM", 
            url=f"{site_url}/auth/telegram/login/?user_id={user_id}&username={username}&first_name={first_name}"
        )],
        [create_standard_button("🏠 Главное меню", "main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            auth_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в telegram_auth_handler: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[create_standard_button("🏠 Главное меню", "main_menu")]])
        )

async def auth_success_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает успешную аутентификацию пользователя
    """
    query = update.callback_query
    if not query:  # type: ignore
        return
    await query.answer()

    user_id = update.effective_user.id  # type: ignore
    
    success_text = f"""
✅ **АВТОРИЗАЦИЯ УСПЕШНА!**

Добро пожаловать в ExamFlow! 🎉

🎯 **Теперь вам доступно:**
• 🤖 Персональный ИИ-ассистент
• 📚 Тысячи заданий для практики
• 📊 Детальная статистика прогресса
• 🏆 Система достижений
• 💎 Премиум функции

Начните обучение прямо сейчас!
"""

    keyboard = [
        [create_standard_button("🤖 СПРОСИТЬ ИИ", "ai_chat")],
        [create_standard_button("📚 ПРАКТИКА", "subjects"),
         create_standard_button("🏆 ПРОГРЕСС", "stats")],
        [create_standard_button("🏠 Главное меню", "main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в auth_success_handler: {e}")

# 🎮 ОБРАБОТЧИКИ ГЕЙМИФИКАЦИИ

async def gamification_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню геймификации"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    keyboard = gamification.create_gamification_keyboard(user_id)

    await query.edit_message_text(  # type: ignore
        "🎮 **ГЕЙМИФИКАЦИЯ**\n\n"
        "Выберите, что хотите посмотреть:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def user_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    stats = await gamification.get_user_stats(user_id)

    if not stats.get('success'):
        await query.edit_message_text(  # type: ignore
            "❌ Ошибка: {stats.get('error', 'Неизвестная ошибка')}",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🔙 Назад", callback_data="gamification_{user_id}")
            ]])
        )
        return

    # Формируем текст статистики
    stats_text = """
📊 **ВАША СТАТИСТИКА**

🏆 **Уровень:** {stats['level']}
💎 **Очки:** {stats['points']}
🌟 **Всего очков:** {stats['total_points']}
🏅 **Ранг:** {stats['rank']}

📚 **Прогресс по предметам:**
"""

    for progress in stats['subjects_progress'][:3]:
        subject_name = progress.get('subject__name', 'Неизвестно')
        solved = progress.get('solved_tasks', 0)
        total = progress.get('total_tasks', 0)
        percentage = (solved / total * 100) if total > 0 else 0

        stats_text += "• {subject_name}: {solved}/{total} ({percentage:.1f}%)\n"

    if stats['achievements']:
        stats_text += "\n🏅 **Последние достижения:**\n"
        for achievement in stats['achievements'][:3]:
            title = achievement.get('title', 'Достижение')
            icon = achievement.get('icon', '🏆')
            stats_text += "{icon} {title}\n"

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        stats_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def achievements_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает достижения пользователя"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    stats = await gamification.get_user_stats(user_id)

    if not stats.get('success'):
        await query.edit_message_text(  # type: ignore
            "❌ Ошибка: {stats.get('error', 'Неизвестная ошибка')}",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🔙 Назад", callback_data="gamification_{user_id}")
            ]])
        )
        return

    achievements = stats.get('achievements', [])

    if not achievements:
        achievements_text = """
🏅 **ДОСТИЖЕНИЯ**

У вас пока нет достижений. Решайте задания, чтобы получить их!
"""
    else:
        achievements_text = "🏅 **ВАШИ ДОСТИЖЕНИЯ**\n\n"
        for achievement in achievements:
            title = achievement.get('title', 'Достижение')
            description = achievement.get('description', '')
            icon = achievement.get('icon', '🏆')
            date = achievement.get('date_earned', '')

            achievements_text += "{icon} **{title}**\n"
            if description:
                achievements_text += "   {description}\n"
            if date:
                achievements_text += "   📅 {date.strftime('%d.%m.%Y')}\n"
            achievements_text += "\n"

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        achievements_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает прогресс пользователя"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    keyboard = gamification.create_progress_keyboard(user_id)

    await query.edit_message_text(  # type: ignore  
        "📊 **ПРОГРЕСС ОБУЧЕНИЯ**\n\n"
        "Выберите тип прогресса для просмотра:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def overall_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает общий прогресс пользователя"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    stats = await gamification.get_user_stats(user_id)

    if not stats.get('success'):
        await query.edit_message_text(  # type: ignore
            "❌ Ошибка: {stats.get('error', 'Неизвестная ошибка')}",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🔙 Назад", callback_data="progress_{user_id}")
            ]])
        )
        return

    # Создаём визуальный прогресс-бар
    level = stats['level']
    points = stats['points']
    next_level_points = level * 100
    progress_percentage = (points % 100) / 100 * 100

    progress_bar = "█" * int(progress_percentage / 10) + "░" * (10 - int(progress_percentage / 10))

    progress_text = """
📈 **ОБЩИЙ ПРОГРЕСС**

🏆 **Текущий уровень:** {level}
💎 **Очки:** {points}
🎯 **До следующего уровня:** {next_level_points - points} очков

📊 **Детализация:**
• Уровень 1: 0-99 очков ✅
"""

    for i in range(2, min(level + 3, 11)):
        if i <= level:
            progress_text += "• Уровень {i}: {(i-1)*100}-{i*100-1} очков ✅\n"
        elif i == level + 1:
            progress_text += "• Уровень {i}: {(i-1)*100}-{i*100-1} очков 🔄\n"
        else:
            progress_text += "• Уровень {i}: {(i-1)*100}-{i*100-1} очков ⏳\n"

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        progress_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def subjects_progress_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает прогресс по предметам"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    stats = await gamification.get_user_stats(user_id)

    if not stats.get('success'):
        await query.edit_message_text(  # type: ignore
            "❌ Ошибка: {stats.get('error', 'Неизвестная ошибка')}",
            reply_markup=InlineKeyboardMarkup([[  # type: ignore
                InlineKeyboardButton("🔙 Назад", callback_data="progress_{user_id}")
            ]])
        )
        return

    subjects_progress = stats.get('subjects_progress', [])

    if not subjects_progress:
        progress_text = """
📚 **ПРОГРЕСС ПО ПРЕДМЕТАМ**

У вас пока нет прогресса по предметам. Начните решать задания!
"""
    else:
        progress_text = "📚 **ПРОГРЕСС ПО ПРЕДМЕТАМ**\n\n"

        for progress in subjects_progress:
            subject_name = progress.get('subject__name', 'Неизвестно')
            solved = progress.get('solved_tasks', 0)
            total = progress.get('total_tasks', 0)
            percentage = (solved / total * 100) if total > 0 else 0

            # Создаём прогресс-бар
            progress_bars = int(percentage / 10)
            progress_bar = "█" * progress_bars + "░" * (10 - progress_bars)

            progress_text += "**{subject_name}**\n"
            progress_text += "{progress_bar} {percentage:.1f}%\n"
            progress_text += "Решено: {solved}/{total}\n\n"

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        progress_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def daily_challenges_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает ежедневные задания"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore
    challenges = await gamification.get_daily_challenges(user_id)

    if not challenges:
        challenges_text = """
📅 **ЕЖЕДНЕВНЫЕ ЗАДАНИЯ**

У вас пока нет доступных ежедневных заданий.
Повышайте уровень, чтобы получить больше заданий!
"""
    else:
        challenges_text = "📅 **ЕЖЕДНЕВНЫЕ ЗАДАНИЯ**\n\n"

        for challenge in challenges:
            icon = challenge.get('icon', '📋')
            title = challenge.get('title', 'Задание')
            description = challenge.get('description', '')
            reward = challenge.get('reward', 0)
            progress = challenge.get('progress', 0)
            target = challenge.get('target', 1)

            challenges_text += "{icon} **{title}**\n"
            if description:
                challenges_text += "   {description}\n"
            challenges_text += "   💎 Награда: {reward} очков\n"
            challenges_text += "   📊 Прогресс: {progress}/{target}\n\n"

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        challenges_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает таблицу лидеров"""
    query = update.callback_query
    await query.answer()  # type: ignore

    leaderboard = await gamification.get_leaderboard(10)

    if not leaderboard:
        leaderboard_text = """
🏅 **ТАБЛИЦА ЛИДЕРОВ**

Пока нет данных для отображения.
Будьте первым в рейтинге!
"""
    else:
        leaderboard_text = "🏅 **ТАБЛИЦА ЛИДЕРОВ**\n\n"

        for user in leaderboard:
            rank = user.get('rank', 0)
            emoji = user.get('emoji', '📊')
            username = user.get('username', 'Неизвестно')
            level = user.get('level', 1)
            points = user.get('points', 0)

            leaderboard_text += "{emoji} **#{rank}** {username}\n"
            leaderboard_text += "   🏆 Уровень: {level} | 💎 Очки: {points}\n\n"

    # Получаем user_id для кнопки "Назад"
    user_id = update.effective_user.id  # type: ignore

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore
        leaderboard_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def bonus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает доступные бонусы"""
    query = update.callback_query
    await query.answer()  # type: ignore

    user_id = update.effective_user.id  # type: ignore

    bonus_text = """
🎁 **ДОСТУПНЫЕ БОНУСЫ**

💎 **Ежедневный бонус за вход** - 10 очков
🔥 **Серия правильных ответов** - 5 очков за каждое
⭐ **Повышение уровня** - 50 очков
🏆 **Первое достижение** - 25 очков
🌟 **Изучение нового предмета** - 100 очков

💡 **Советы для получения бонусов:**
• Решайте задания каждый день
• Старайтесь отвечать правильно подряд
• Изучайте разные предметы
• Достигайте новых уровней
"""

    keyboard = InlineKeyboardMarkup([
    ])

    await query.edit_message_text(  # type: ignore  
        bonus_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Совместимость с тестами: класс-обёртка с ссылками на хендлеры
class BotHandlers:  # type: ignore
    start = staticmethod(start)
    start_command = staticmethod(start)  # Алиас для тестов
    main_menu = staticmethod(main_menu)
    subjects_menu = staticmethod(subjects_menu)
    show_subject_topics = staticmethod(show_subject_topics)
    random_task = staticmethod(random_task)
    show_answer = staticmethod(show_answer)
    show_stats = staticmethod(show_stats)
    learning_plan_menu = staticmethod(learning_plan_menu)
    ai_help_handler = staticmethod(ai_help_handler)
    ai_explain_handler = staticmethod(ai_explain_handler)
    ai_personal_handler = staticmethod(ai_personal_handler)
    ai_hint_general_handler = staticmethod(ai_hint_general_handler)
    handle_text_message = staticmethod(handle_text_message)
    handle_message = staticmethod(handle_text_message)  # Алиас для тестов
    handle_menu_button = staticmethod(handle_menu_button)
    handle_ai_message = staticmethod(handle_ai_message)
    search_subject_handler = staticmethod(search_subject_handler)
    random_subject_handler = staticmethod(random_subject_handler)
    show_task_handler = staticmethod(show_task_handler)
    clear_context_handler = staticmethod(clear_context_handler)
    handle_unknown_callback = staticmethod(handle_unknown_callback)
    telegram_auth_handler = staticmethod(telegram_auth_handler)
    auth_success_handler = staticmethod(auth_success_handler)
    gamification_menu_handler = staticmethod(gamification_menu_handler)
    user_stats_handler = staticmethod(user_stats_handler)
    achievements_handler = staticmethod(achievements_handler)
    progress_handler = staticmethod(progress_handler)
    overall_progress_handler = staticmethod(overall_progress_handler)
    subjects_progress_handler = staticmethod(subjects_progress_handler)
    daily_challenges_handler = staticmethod(daily_challenges_handler)
    leaderboard_handler = staticmethod(leaderboard_handler)
    bonus_handler = staticmethod(bonus_handler)
    
    # Дополнительные методы для тестов
    @staticmethod
    def help_command(update, context):
        """Команда /help - показывает справку"""
        return handle_text_message(update, context)
    
    @staticmethod
    def search_command(update, context):
        """Команда /search - поиск по базе знаний"""
        return handle_ai_message(update, context)
    
    @staticmethod
    def fipi_command(update, context):
        """Команда /fipi - поиск в материалах ФИПИ"""
        return handle_ai_message(update, context)
    
    @staticmethod
    def _parse_search_command(text):
        """Парсинг команды поиска"""
        if text and text.startswith('/search '):
            return text[8:].strip()
        return None
    
    @staticmethod
    def _parse_fipi_command(text):
        """Парсинг команды ФИПИ"""
        if text and text.startswith('/fipi '):
            return text[6:].strip()
        return None
    
    @staticmethod
    def _format_rag_response(response):
        """Форматирование ответа RAG системы"""
        answer = response.get('answer', '')
        sources = response.get('sources', [])
        processing_time = response.get('processing_time', 0)
        
        formatted = f"🤖 {answer}\n\n"
        
        if sources:
            formatted += "📚 Источники:\n"
            for i, source in enumerate(sources[:3], 1):
                formatted += f"{i}. {source}\n"
        
        if processing_time:
            formatted += f"\n⏱️ Время обработки: {processing_time:.1f}с"
            
        return formatted
