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
    Achievement, UserProfile, Subscription
)
from django.db.models import Count, Q
from django.utils import timezone

# Настройка логирования
logger = logging.getLogger(__name__)

# Функция для проверки соединения с базой данных
def check_db_connection():
    """Проверяет соединение с базой данных"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as e:
        logger.error(f"Ошибка соединения с базой: {e}")
        return False

# Функция для получения текущего задания пользователя из профиля
def get_current_task_id(user):
    """Получает ID текущего задания из профиля пользователя"""
    try:
        profile = UserProfile.objects.get(user=user)  # type: ignore
        return profile.current_task_id
    except UserProfile.DoesNotExist:
        return None

def set_current_task_id(user, task_id):
    """Устанавливает ID текущего задания в профиле пользователя"""
    try:
        profile = UserProfile.objects.get(user=user)  # type: ignore
        profile.current_task_id = task_id
        profile.save()
        logger.info(f"Установлен current_task_id: {task_id} для пользователя {user.username}")
    except UserProfile.DoesNotExist:
        logger.error(f"Профиль не найден для пользователя {user.username}")


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
    # Проверяем соединение с базой данных
    if not check_db_connection():
        await update.message.reply_text(
            "❌ Сервис временно недоступен. База данных не отвечает.\n"
            "Попробуйте через 1-2 минуты."
        )
        return
    
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

        # Надежное получение списка предметов, у которых есть хотя бы одно задание
        try:
            subject_ids = list(Task.objects.values_list('subject_id', flat=True).distinct())  # type: ignore
        except Exception as id_err:
            logger.error(f"subjects_menu: ошибка выборки subject_ids: {id_err}")
            subject_ids = []

        if not subject_ids:
            await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
            return

        subjects = Subject.objects.filter(id__in=subject_ids)  # type: ignore

        keyboard = []
        for subject in subjects:
            try:
                tasks_count = Task.objects.filter(subject_id=subject.id).count()  # type: ignore
            except Exception:
                tasks_count = 0
            button_text = f"{subject.name} ({tasks_count} заданий)"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"subject_{subject.id}")
            ])

        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                "📚 Выберите предмет:\n\nДоступные предметы для изучения:",
                reply_markup=reply_markup
            )
        except Exception as edit_err:
            logger.warning(f"subjects_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,  # type: ignore
                    text="📚 Выберите предмет:\n\nДоступные предметы для изучения:",
                    reply_markup=reply_markup
                )
            except Exception as send_err:
                logger.error(f"subjects_menu: send_message тоже не удался: {send_err}")

    except Exception as e:
        logger.error(f"Ошибка в subjects_menu: {e}")
        # Попробуем сообщить пользователю, что произошла ошибка, чтобы не было тишины
        try:
            await update.effective_chat.send_message("❌ Не удалось загрузить предметы. Попробуйте /start или повторите попытку позже.")  # type: ignore
        except Exception as send_err:
            logger.error(f"subjects_menu: не удалось отправить сообщение об ошибке: {send_err}")


async def show_subject_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает случайное задание выбранного предмета (упрощенный режим без тем)
    """
    query = update.callback_query
    await query.answer()

    subject_id = int(query.data.split('_')[1])
    subject = Subject.objects.get(id=subject_id)  # type: ignore

    tasks = Task.objects.filter(subject=subject)  # type: ignore
    if not tasks:
        await query.edit_message_text(
            f"❌ В предметe {subject.name} пока нет заданий",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]])
        )
        return

    import random
    task = random.choice(list(tasks))

    # Устанавливаем текущее задание в профиле пользователя
    user, _ = get_or_create_user(update.effective_user)
    set_current_task_id(user, task.id)
    logger.info(f"show_subject_topics: установлен current_task_id: {task.id}")

    task_text = f"""
📝 **Задание №{task.id}**
**Предмет:** {task.subject.name}

**Заголовок:** {task.title}

**Условие:**
{task.description or 'Описание задания отсутствует'}

Введите ваш ответ:
"""

    keyboard = [
        [InlineKeyboardButton("🔊 Голосовая подсказка", callback_data=f"voice_{task.id}")],
        [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]
    ]

    try:
        await query.edit_message_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as edit_err:
        logger.warning(f"show_subject_topics: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error(f"show_subject_topics: send_message тоже не удался: {send_err}")


async def show_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает задание пользователю
    
    Отображает условие задания и кнопки для ответа
    """
    global current_task_id
    
    query = update.callback_query
    await query.answer()
    
    # Определяем источник: случайное по предмету или полностью случайное
    if query.data.startswith('subject_'):
        try:
            subject_id = int(query.data.split('_')[1])
        except Exception:
            await query.edit_message_text("❌ Некорректный выбор предмета")
            return
        tasks = Task.objects.filter(subject_id=subject_id)  # type: ignore
        if not tasks:
            await query.edit_message_text(f"❌ В предмете пока нет заданий")
            return
        import random
        task = random.choice(list(tasks))
    elif query.data.startswith('random_subject_'):
        subject_id = int(query.data.split('_')[2])
        tasks = Task.objects.filter(subject_id=subject_id)  # type: ignore
        if not tasks:
            await query.edit_message_text(f"❌ В предмете пока нет заданий")
            return
        import random
        task = random.choice(list(tasks))
    else:
        tasks = Task.objects.all()  # type: ignore
        if not tasks:
            await query.edit_message_text("❌ Задания пока не загружены")
            return
        
        import random
        task = random.choice(list(tasks))
    
    # Сохраняем текущее задание в профиль пользователя, чтобы не терять контекст
    try:
        user, _ = get_or_create_user(update.effective_user)
        set_current_task_id(user, task.id)
    except Exception as prof_err:
        logger.warning(f"Не удалось сохранить current_task_id в профиль: {prof_err}")
    current_task_id = task.id
    logger.info(f"Установлен current_task_id: {current_task_id} для задания: {task.title}")
    
    # Формируем текст задания
    task_text = f"""
📝 **Задание №{task.id}**
**Предмет:** {task.subject.name}

**Заголовок:** {task.title}

**Условие:**
{task.description or 'Описание задания отсутствует'}

Введите ваш ответ:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔊 Голосовая подсказка", callback_data=f"voice_{task.id}")],
        [InlineKeyboardButton("💡 Показать ответ", callback_data=f"answer_{task.id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subjects")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(
            task_text,
            reply_markup=reply_markup
        )
    except Exception as edit_err:
        logger.warning(f"show_task: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=reply_markup
            )
        except Exception as send_err:
            logger.error(f"show_task: send_message тоже не удался: {send_err}")


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ответ пользователя на задание
    
    Проверяет правильность ответа и сохраняет прогресс
    """
    global current_task_id
    
    logger.info(f"handle_answer вызван. current_task_id: {current_task_id}")
    
    if not current_task_id:
        await update.message.reply_text("❌ Сначала выберите задание!")
        return
    
    user, _ = get_or_create_user(update.effective_user)
    task = Task.objects.get(id=current_task_id) # type: ignore
    user_answer = (update.message.text or '').strip()
    
    # Проверяем ответ (простая текстовая проверка)
    correct_value = (task.answer or '').strip()
    is_correct = bool(correct_value) and (user_answer.lower() == correct_value.lower())
    
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
    
    # У нас нет поля explanation в модели Task — показываем источник/подсказку, если есть
    if task.source:
        response += f"**Источник:** {task.source}"
    
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
    total_attempts = UserProgress.objects.filter(user=user).count()  # type: ignore
    correct_answers = UserProgress.objects.filter(user=user, is_correct=True).count()  # type: ignore
    accuracy = round((correct_answers / total_attempts * 100) if total_attempts > 0 else 0, 1)
    
    rating, _ = UserRating.objects.get_or_create(user=user)  # type: ignore
    
    stats_text = f"""
📊 **Ваша статистика**

👤 **Пользователь:** {user.first_name or user.username}
✅ **Правильных ответов:** {correct_answers}
📝 **Всего попыток:** {total_attempts}
🎯 **Точность:** {accuracy}%
⭐ **Рейтинг:** {rating.total_points} очков

🏆 **Достижения:** {Achievement.objects.filter(user=user).count()}

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
