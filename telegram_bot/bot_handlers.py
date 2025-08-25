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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
from telegram.ext import ContextTypes
from django.contrib.auth.models import User
from learning.models import (
    Subject, Task, UserProgress, UserRating, Achievement
)
from authentication.models import UserProfile, Subscription
from django.db.models import Count, Q
from django.utils import timezone
from ai.services import AiService
from ai.rag_service import rag_service

# Настройка логирования
logger = logging.getLogger(__name__)

def clean_markdown_text(text: str) -> str:
    """
    Очищает текст от проблемных символов Markdown для безопасной отправки в Telegram
    """
    return text.replace('*', '').replace('_', '').replace('`', '').replace('**', '').replace('__', '')

# Синхронные функции БД, обёрнутые для безопасного вызова в async-контексте
@sync_to_async
def db_check_connection() -> bool:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return True

# ИИ сервис для асинхронного использования
@sync_to_async
def get_ai_response(prompt: str, task_type: str = 'chat', user=None, task=None) -> str:
    """Получает персонализированный ответ от ИИ с использованием RAG системы"""
    try:
        from ai.personalized_ai_service import PersonalizedAiService
        
        # Используем персонализированный AI-сервис
        personalized_ai = PersonalizedAiService()
        
        # Получаем персонализированный ответ
        if user is None:
            return "❌ Ошибка: пользователь не определен"
        result = personalized_ai.get_personalized_response(prompt, user, task, task_type)
        
        if not result.get('success', False):
            return f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}"
        
        response = result['response']
        
        # Добавляем информацию о провайдере
        response += f"\n\n🤖 Ответ подготовлен с помощью ИИ"
        
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
                    response += f"\n• {subject}: {failed_tasks} проваленных заданий"
            
            # Добавляем рекомендации
            recommendations = personalization_data.get('recommendations', [])
            if recommendations:
                response += "\n\n💡 **Персональные рекомендации:**"
                for rec in recommendations[:2]:
                    title = rec.get('title', 'Рекомендация')
                    action = rec.get('action', '')
                    response += f"\n• {title}"
                    if action:
                        response += f" - {action}"
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при получении персонализированного ответа от ИИ: {e}")
        return f"❌ Ошибка ИИ-ассистента: {str(e)}"

@sync_to_async
def db_get_all_subjects_with_tasks():
    """Получает все предметы с количеством заданий"""
    from django.db.models import Count
    subjects = Subject.objects.annotate(  # type: ignore
        tasks_count=Count('task')
    ).filter(tasks_count__gt=0).values('id', 'name', 'exam_type', 'tasks_count')
    return list(subjects)

@sync_to_async
def db_get_subject_ids():
    return list(Task.objects.values_list('subject_id', flat=True).distinct())  # type: ignore

@sync_to_async
def db_get_subjects_by_ids(ids):
    return list(Subject.objects.filter(id__in=ids))  # type: ignore

@sync_to_async
def db_count_tasks_for_subject(subject_id: int) -> int:
    return Task.objects.filter(subject_id=subject_id).count()  # type: ignore

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
    name = Subject.objects.filter(id=subject_id).values_list('name', flat=True).first()  # type: ignore
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
        logger.info(f"Установлен current_task_id: {task_id} для пользователя {user.username}")
    except Exception as e:
        logger.error(f"Профиль не найден для пользователя {user.username}: {e}")

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
                [KeyboardButton("🚀 Старт"), KeyboardButton("🤖 Спросить ИИ")],
                [KeyboardButton("📚 Предметы"), KeyboardButton("📊 Статистика")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            
            await update.message.reply_text(
                "🎯 **Нижнее меню настроено!**\n\n"
                "Теперь у вас есть быстрый доступ к основным функциям:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка создания нижнего меню: {e}")
    
    # Проверяем соединение с базой данных (в async контексте)
    try:
        ok = await db_check_connection()
    except Exception as e:
        logger.error(f"Ошибка проверки БД: {e}")
        ok = False
    if not ok:
        error_text = "❌ Сервис временно недоступен. База данных не отвечает.\nПопробуйте через 1-2 минуты."
        if is_callback:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)
        return
    
    try:
        user_obj, created = await db_get_or_create_user(user)
        
        welcome_text = f"""
🚀 **Добро пожаловать в ExamFlow!**

Привет, {user.first_name}! 

Я помогу тебе подготовиться к ЕГЭ и ОГЭ:

✅ Решать задания по всем предметам
📊 Отслеживать прогресс
🏆 Зарабатывать достижения
🤖 Умный ИИ-помощник

Выбери действие:
"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Предметы", callback_data="subjects"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🎓 План обучения", callback_data="learning_plan"), InlineKeyboardButton("🎯 Персонализация", callback_data="personalization_menu")],
            [InlineKeyboardButton("🌐 Сайт", url="https://examflow.ru")],
            [InlineKeyboardButton("🔄 Начать заново", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        logger.info(f"Пользователь {user.id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        error_text = "❌ Произошла ошибка. Попробуйте позже."
        if is_callback:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

# ============================================================================
# ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ
# ============================================================================

# Импортируем обработчики персонализации
from .personalization_handlers import (
    personalization_menu,
    show_my_analytics,
    show_my_recommendations,
    show_study_plan,
    show_weak_topics
)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Возвращает пользователя в главное меню
    """
    query = update.callback_query
    await query.answer()
    
    welcome_text = f"""
🚀 **ГЛАВНОЕ МЕНЮ EXAMFLOW**

Привет, {update.effective_user.first_name}! 

Я помогу тебе подготовиться к ЕГЭ и ОГЭ:

✅ Решать задания по всем предметам
📊 Отслеживать прогресс
🏆 Зарабатывать достижения
🤖 Умный ИИ-помощник

Выбери действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("📚 Предметы", callback_data="subjects"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎓 План обучения", callback_data="learning_plan"), InlineKeyboardButton("🎯 Персонализация", callback_data="personalization_menu")],
        [InlineKeyboardButton("🌐 Сайт", url="https://examflow.ru")],
        [InlineKeyboardButton("🔄 Начать заново", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=None
        )
    except Exception as edit_err:
        logger.warning(f"main_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode=None
            )
        except Exception as send_err:
            logger.error(f"main_menu: send_message тоже не удался: {send_err}")

async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает меню выбора предметов
    
    Отображает все доступные предметы с количеством заданий
    """
    try:
        query = update.callback_query
        await query.answer()

        # Получаем все предметы с количеством заданий
        try:
            subjects = await db_get_all_subjects_with_tasks()
            if not subjects:
                await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
                return
        except Exception as e:
            logger.error(f"subjects_menu: ошибка получения предметов: {e}")
            await query.edit_message_text("❌ Ошибка загрузки предметов. Попробуйте позже.")
            return

        if not subjects:
            await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
            return

        # Сортируем предметы по количеству заданий (больше заданий - выше)
        subjects_sorted = sorted(subjects, key=lambda x: x['tasks_count'], reverse=True)

        keyboard = []
        for subject in subjects_sorted[:15]:  # Показываем топ-15 предметов
            button_text = f"{subject['name']} ({subject['tasks_count']} заданий)"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"subject_{subject['id']}")
            ])

        # Добавляем кнопки навигации
        keyboard.append([
            InlineKeyboardButton("🔍 Поиск по предмету", callback_data="search_subject"),
            InlineKeyboardButton("🎯 Случайный предмет", callback_data="random_subject")
        ])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                "📚 **ВЫБЕРИТЕ ПРЕДМЕТ ДЛЯ ИЗУЧЕНИЯ**\n\n"
                f"Доступно **{len(subjects)} предметов** с **{sum(s['tasks_count'] for s in subjects)} заданиями**\n\n"
                "Предметы отсортированы по количеству заданий:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as edit_err:
            logger.warning(f"subjects_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,  # type: ignore
                    text="📚 **ВЫБЕРИТЕ ПРЕДМЕТ ДЛЯ ИЗУЧЕНИЯ**\n\n"
                         f"Доступно **{len(subjects)} предметов** с **{sum(s['tasks_count'] for s in subjects)} заданиями**\n\n"
                         "Предметы отсортированы по количеству заданий:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as send_err:
                logger.error(f"subjects_menu: send_message тоже не удался: {send_err}")

    except Exception as e:
        logger.error(f"Ошибка в subjects_menu: {e}")
        try:
            await query.edit_message_text("❌ Не удалось загрузить предметы. Попробуйте позже.")
        except Exception:
            pass

async def show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает случайное задание выбранного предмета
    """
    query = update.callback_query
    await query.answer()

    subject_id = int(query.data.split('_')[1])
    
    # Получаем информацию о предмете
    subject = await db_get_subject_by_id(subject_id)
    if not subject:
        await query.edit_message_text("❌ Предмет не найден")
        return
    
    # Получаем список заданий для предмета
    tasks = await db_get_tasks_by_subject(subject_id)
    if not tasks:
        await query.edit_message_text(
            f"❌ В предмете **{subject.name}** пока нет заданий",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К предметам", callback_data="subjects")
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
    logger.info(f"show_subject_topics: установлен current_task_id: {task.id}")

    # Формируем текст задания
    task_text = f"""
📝 **ЗАДАНИЕ №{task.id}**
📚 **Предмет:** {subject.name} ({subject.exam_type})

**{task.title}**

**Условие:**
{task.description or 'Описание задания отсутствует'}

**Сложность:** {'⭐' * task.difficulty} ({task.difficulty}/5)
**Источник:** {task.source or 'Не указан'}

💡 **Введите ваш ответ или используйте кнопки ниже:**
"""

    keyboard = [
        [InlineKeyboardButton("🤖 Спросить ИИ", callback_data=f"ai_help_{task.id}")],
        [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("🎯 Следующее задание", callback_data=f"subject_{subject_id}")],
        [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
    ]

    try:
        await query.edit_message_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as edit_err:
        logger.warning(f"show_subject_topics: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as send_err:
            logger.error(f"show_subject_topics: send_message тоже не удался: {send_err}")

async def random_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает случайное задание из всех доступных
    """
    query = update.callback_query
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
        logger.info(f"random_task: установлен current_task_id: {task.id} для пользователя {user.username}")
    except Exception as prof_err:
        logger.warning(f"Не удалось сохранить current_task_id в профиль: {prof_err}")
    
    # Получаем название предмета безопасно
    subject_name = await db_get_subject_name_for_task(task)
    
    # Формируем текст задания
    task_text = f"""
📝 **Задание №{task.id}**
**Предмет:** {subject_name}

**Заголовок:** {task.title}

**Условие:**
{task.description or 'Описание задания отсутствует'}

Введите ваш ответ:
"""
    
    keyboard = [
        [InlineKeyboardButton("🤖 Спросить AI", callback_data=f"ai_help_{task.id}")],
        [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
    ]
    
    try:
        await query.edit_message_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_err:
        logger.warning(f"random_task: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error(f"random_task: send_message тоже не удался: {send_err}")

async def show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает правильный ответ на задание
    """
    query = update.callback_query
    await query.answer()
    
    # Извлекаем ID задания из callback_data
    task_id = int(query.data.split('_')[1])
    
    # Получаем задание
    try:
        task = await db_get_task_by_id(task_id)
    except Exception:
        await query.edit_message_text("❌ Задание не найдено")
        return
    
    # Получаем название предмета безопасно
    subject_name = await db_get_subject_name_for_task(task)
    
    answer_text = f"""
💡 **Ответ на задание №{task.id}**

**Предмет:** {subject_name}
**Заголовок:** {task.title}

✅ **Правильный ответ:** {task.answer or 'Ответ не указан'}

**Условие:**
{task.description or 'Описание задания отсутствует'}

**Источник:** {task.source or 'Не указан'}
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Следующее задание", callback_data="random_task")],
        [InlineKeyboardButton("📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    try:
        await query.edit_message_text(
            answer_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_err:
        logger.warning(f"show_answer: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=answer_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error(f"show_answer: send_message тоже не удался: {send_err}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает статистику пользователя
    
    Отображает количество решенных заданий, точность, рейтинг
    """
    query = update.callback_query
    await query.answer()
    
    user, _ = await db_get_or_create_user(update.effective_user)

    # Получаем статистику безопасно
    total_attempts = await sync_to_async(lambda: UserProgress.objects.filter(user=user).count())()  # type: ignore
    correct_answers = await sync_to_async(lambda: UserProgress.objects.filter(user=user, is_correct=True).count())()  # type: ignore
    accuracy = round((correct_answers / total_attempts * 100) if total_attempts > 0 else 0, 1)
    
    rating = await sync_to_async(lambda: UserRating.objects.get_or_create(user=user)[0])()  # type: ignore
    
    stats_text = f"""
📊 **Ваша статистика**

👤 **Пользователь:** {user.first_name or user.username}
✅ **Правильных ответов:** {correct_answers}
📝 **Всего попыток:** {total_attempts}
🎯 **Точность:** {accuracy}%
⭐ **Рейтинг:** {rating.total_points} очков

🏆 **Достижения:** {await sync_to_async(lambda: len([ach for ach in user.achievements.all()]))()}

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

async def learning_plan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает персональный план обучения пользователя
    
    Использует RAG систему для анализа прогресса и рекомендаций
    """
    try:
        query = update.callback_query
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
            await query.edit_message_text(f"❌ Ошибка: {learning_plan['error']}")
            return
        
        # Формируем текст плана
        plan_text = f"""
🎓 **ТВОЙ ПЕРСОНАЛЬНЫЙ ПЛАН ОБУЧЕНИЯ**

📊 **Текущий уровень:** {learning_plan.get('current_level', 1)}/5
🎯 **Точность:** {learning_plan.get('accuracy', 0)}%
📚 **Решено заданий:** {learning_plan.get('total_tasks', 0)}

🔴 **Слабые темы:**
"""
        
        weak_topics = learning_plan.get('weak_topics', [])
        if weak_topics:
            for topic in weak_topics[:3]:
                plan_text += f"• {topic}\n"
        else:
            plan_text += "• Нет данных\n"
        
        plan_text += "\n🟢 **Сильные темы:**\n"
        strong_topics = learning_plan.get('strong_topics', [])
        if strong_topics:
            for topic in strong_topics[:3]:
                plan_text += f"• {topic}\n"
        else:
            plan_text += "• Нет данных\n"
        
        plan_text += "\n💡 **Рекомендации:**\n"
        recommendations = learning_plan.get('recommendations', [])
        if recommendations:
            for rec in recommendations[:3]:
                plan_text += f"• {rec['title']}\n"
        else:
            plan_text += "• Начните с базовых заданий\n"
        
        plan_text += f"""

📅 **Цели:**
• Ежедневно: {learning_plan.get('daily_goal', 3)} заданий
• Еженедельно: {learning_plan.get('weekly_goal', 15)} заданий

🎯 **Следующие шаги:**\n"""
        
        next_steps = learning_plan.get('next_steps', [])
        if next_steps:
            for step in next_steps[:3]:
                plan_text += f"• {step['description']}\n"
        else:
            plan_text += "• Продолжайте решать задания\n"
        
        # Кнопки для навигации
        keyboard = [
            [InlineKeyboardButton("🎯 Начать обучение", callback_data="subjects")],
            [InlineKeyboardButton("📊 Детальная статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            plan_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь {user.id} получил план обучения")
        
    except Exception as e:
        logger.error(f"Ошибка в learning_plan_menu: {e}")
        await query.edit_message_text(
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
            await query.answer()
            user = update.effective_user
        else:
            query = None
            user = update.effective_user
        
        # Получаем пользователя
        user_obj, created = await db_get_or_create_user(user)
        
        # Проверяем формат callback_data (только для callback-запросов)
        if is_callback and query.data and query.data.startswith('ai_help_') and '_' in query.data:
            # Помощь с конкретным заданием
            try:
                task_id = int(query.data.split('_')[2])
                task = await db_get_task_by_id(task_id)
                
                if not task:
                    await query.edit_message_text("❌ Задание не найдено.")
                    return
                
                # Показываем сообщение о том, что AI думает
                thinking_message = await query.edit_message_text(
                    "🤔 AI анализирует задание и ваш прогресс...\n\n"
                    "Это может занять несколько секунд.",
                    parse_mode=None
                )
                
                # Получаем персонализированную помощь от AI
                ai_response = await get_ai_response(
                    "Объясни, как решить это задание. Дай пошаговое решение с объяснением каждого шага. "
                    "Учитывай мой текущий уровень и слабые темы.",
                    task_type='task_help',
                    user=user_obj,
                    task=task
                )
                
                # Формируем ответ с кнопками
                response_text = f"""
🤖 **AI ПОМОЩЬ ДЛЯ ЗАДАНИЯ №{task.id}**

{ai_response}

---
💡 **Дополнительные возможности:**
"""
                
                keyboard = [
                    [InlineKeyboardButton("💡 Только подсказка", callback_data=f"ai_hint_{task.id}")],
                    [InlineKeyboardButton("📚 Похожие задания", callback_data=f"similar_{task.id}")],
                    [InlineKeyboardButton("🎯 Моя персонализация", callback_data="personalization_menu")],
                    [InlineKeyboardButton("🔙 К заданию", callback_data=f"show_task_{task.id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Очищаем текст от проблемных символов Markdown
                clean_response = clean_markdown_text(response_text)
                
                await thinking_message.edit_text(  # type: ignore
                    clean_response,
                    reply_markup=reply_markup,
                    parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
                )
                
                logger.info(f"Пользователь {user_obj.id} получил персонализированную AI помощь для задания {task.id}")
                
            except (IndexError, ValueError) as e:
                logger.error(f"Ошибка парсинга task_id в ai_help_handler: {e}")
                await query.edit_message_text("❌ Ошибка формата данных. Попробуйте еще раз.")
                return
        else:
            # Общее меню ИИ с персонализацией
            ai_menu_text = """
🤖 **ИИ-ПОМОЩНИК EXAMFLOW**

Я могу помочь тебе с:

📚 **Объяснение тем** - с учетом твоего уровня
💡 **Подсказки к заданиям** - персональные советы
🎯 **Персональные рекомендации** - на основе прогресса
🔍 **Поиск похожих заданий** - для практики
📊 **Анализ слабых мест** - фокус на проблемных темах

**Выбери что нужно:**
"""
            
            keyboard = [
                [InlineKeyboardButton("📚 Объяснить тему", callback_data="ai_explain")],
                [InlineKeyboardButton("💡 Дать подсказку", callback_data="ai_hint")],
                [InlineKeyboardButton("🎯 Персональные советы", callback_data="ai_personal")],
                [InlineKeyboardButton("🔍 Похожие задания", callback_data="similar_tasks")],
                [InlineKeyboardButton("📊 Анализ прогресса", callback_data="my_analytics")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_callback:
                await query.edit_message_text(
                    ai_menu_text,
                    reply_markup=reply_markup,
                    parse_mode=None
                )
            else:
                await update.message.reply_text(
                    ai_menu_text,
                    reply_markup=reply_markup,
                    parse_mode=None
                )
        
    except Exception as e:
        logger.error(f"Ошибка в ai_help_handler: {e}")
        if is_callback and query:
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def ai_explain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для объяснения темы от ИИ
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(
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
        response_text = f"""
📚 **ОБЪЯСНЕНИЕ ТЕМ ОТ ИИ**

{ai_response}

---
💡 **Хотите получить подсказку к конкретному заданию?**
"""
        
        keyboard = [
            [InlineKeyboardButton("💡 Подсказка к заданию", callback_data="ai_hint")],
            [InlineKeyboardButton("🎯 Персональные советы", callback_data="ai_personal")],
            [InlineKeyboardButton("⬅️ Назад к ИИ", callback_data="ai_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)
        
        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=reply_markup,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )
        
        logger.info(f"Пользователь {user.id} получил объяснение темы от ИИ")
        
    except Exception as e:
        logger.error(f"Ошибка в ai_explain_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

async def ai_personal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для персональных советов от ИИ
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(
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
        response_text = f"""
🎯 **ПЕРСОНАЛЬНЫЕ СОВЕТЫ ОТ ИИ**

{ai_response}

---
📚 **Хотите получить объяснение конкретной темы?**
"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Объяснить тему", callback_data="ai_explain")],
            [InlineKeyboardButton("💡 Подсказка к заданию", callback_data="ai_hint")],
            [InlineKeyboardButton("⬅️ Назад к ИИ", callback_data="ai_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)
        
        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=reply_markup,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )
        
        logger.info(f"Пользователь {user.id} получил персональные советы от ИИ")
        
    except Exception as e:
        logger.error(f"Ошибка в ai_personal_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

async def ai_hint_general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Общий обработчик для подсказок от ИИ (когда нет конкретного задания)
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем пользователя
        user, created = await db_get_or_create_user(update.effective_user)
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(
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
        response_text = f"""
💡 **ОБЩИЕ ПОДСКАЗКИ ПО РЕШЕНИЮ ЗАДАЧ**

{ai_response}

---
🎯 **Хотите получить персональные советы?**
"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 Персональные советы", callback_data="ai_personal")],
            [InlineKeyboardButton("📚 Объяснить тему", callback_data="ai_explain")],
            [InlineKeyboardButton("⬅️ Назад к ИИ", callback_data="ai_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(response_text)
        
        await thinking_message.edit_text(  # type: ignore
            clean_response,
            reply_markup=reply_markup,
            parse_mode=None  # Отключаем Markdown для избежания ошибок парсинга
        )
        
        logger.info(f"Пользователь {user.id} получил общую подсказку от ИИ")
        
    except Exception as e:
        logger.error(f"Ошибка в ai_hint_general_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

# ============================================================================
# ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================================================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для прямого общения с ИИ и нижнего меню
    """
    try:
        user_message = update.message.text
        if not user_message:
            return
            
        user = update.effective_user
        
        # Проверяем, что сообщение не является командой
        if user_message.startswith('/'):
            return
        
        # Обработка нижнего меню
        if user_message in ["🚀 Старт", "🤖 Спросить ИИ", "📚 Предметы", "📊 Статистика"]:
            await handle_menu_button(update, context, user_message)
            return
        
        # Если это не кнопка меню, то это вопрос к ИИ
        await handle_ai_message(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_text_message: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла ошибка. Попробуйте позже.",
                reply_to_message_id=update.message.message_id
            )
        except Exception as send_err:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_err}")

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    """
    Обрабатывает нажатия кнопок нижнего меню
    """
    try:
        if button_text == "🚀 Старт":
            await start(update, context)
        elif button_text == "🤖 Спросить ИИ":
            await ai_help_handler(update, context)
        elif button_text == "📚 Предметы":
            await subjects_menu(update, context)
        elif button_text == "📊 Статистика":
            await show_stats(update, context)
    except Exception as e:
        logger.error(f"Ошибка в handle_menu_button: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для прямого общения с ИИ
    """
    try:
        user_message = update.message.text
        if not user_message:
            return
            
        user = update.effective_user
        
        # Получаем или создаем пользователя
        user_obj, created = await db_get_or_create_user(user)
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🤔 AI анализирует ваш вопрос...\n\nЭто может занять несколько секунд.",
            reply_to_message_id=update.message.message_id
        )
        
        # Получаем ответ от AI
        ai_response = await get_ai_response(
            user_message,
            task_type='direct_question',
            user=user_obj
        )
        
        # Очищаем текст от проблемных символов Markdown
        clean_response = clean_markdown_text(ai_response)
        
        # Формируем ответ с кнопками
        response_text = f"""
🤖 **ОТВЕТ ИИ**

{clean_response}

---
💡 **Дополнительные возможности:**
"""
        
        keyboard = [
            [InlineKeyboardButton("📚 Объяснить тему", callback_data="ai_explain")],
            [InlineKeyboardButton("💡 Дать подсказку", callback_data="ai_hint")],
            [InlineKeyboardButton("🎯 Персональные советы", callback_data="ai_personal")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
            [InlineKeyboardButton("🔄 Начать заново", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Обновляем сообщение с ответом
        await thinking_message.edit_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode=None
        )
        
        logger.info(f"Пользователь {user_obj.id} получил прямой ответ от ИИ на вопрос: {user_message[:50]}...")
        
    except Exception as e:
        logger.error(f"Ошибка в handle_ai_message: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла ошибка при обработке вашего вопроса. Попробуйте позже или используйте кнопку '🤖 Спросить ИИ'.",
                reply_to_message_id=update.message.message_id
            )
        except Exception as send_err:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_err}")

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def search_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик поиска по предмету
    """
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 **ПОИСК ПО ПРЕДМЕТУ**\n\n"
        "Введите название предмета или его часть:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="subjects")
        ]]),
        parse_mode='Markdown'
    )

async def random_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик случайного предмета
    """
    query = update.callback_query
    await query.answer()
    
    try:
        # Получаем случайный предмет с заданиями
        subjects = await db_get_all_subjects_with_tasks()
        if not subjects:
            await query.edit_message_text("❌ Нет доступных предметов")
            return
        
        import random
        random_subject = random.choice(subjects)
        
        # Показываем случайный предмет
        await query.edit_message_text(
            f"🎯 **СЛУЧАЙНЫЙ ПРЕДМЕТ**\n\n"
            f"📚 **{random_subject['name']}**\n"
            f"📝 **Заданий:** {random_subject['tasks_count']}\n"
            f"🎓 **Тип:** {random_subject['exam_type']}\n\n"
            f"Хотите решить задание по этому предмету?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Решить задание", callback_data=f"subject_{random_subject['id']}")],
                [InlineKeyboardButton("🎲 Другой предмет", callback_data="random_subject")],
                [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
            ]),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в random_subject_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

async def show_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает задание по ID
    """
    query = update.callback_query
    await query.answer()
    
    try:
        task_id = int(query.data.split('_')[1])
        task = await db_get_task_by_id(task_id)
        
        if not task:
            await query.edit_message_text("❌ Задание не найдено")
            return
        
        # Получаем информацию о предмете
        subject = await db_get_subject_by_id(task.subject.id)
        subject_name = subject.name if subject else "Неизвестный предмет"
        
        # Формируем текст задания
        task_text = f"""
📝 **ЗАДАНИЕ №{task.id}**
📚 **Предмет:** {subject_name}

**{task.title}**

**Условие:**
{task.description or 'Описание задания отсутствует'}

**Сложность:** {'⭐' * task.difficulty} ({task.difficulty}/5)
**Источник:** {task.source or 'Не указан'}

💡 **Введите ваш ответ или используйте кнопки ниже:**
"""

        keyboard = [
            [InlineKeyboardButton("🤖 Спросить ИИ", callback_data=f"ai_help_{task.id}")],
            [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
            [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
        ]

        await query.edit_message_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_task_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

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
