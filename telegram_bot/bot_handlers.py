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
    """Получает ответ от ИИ с использованием RAG системы"""
    try:
        ai_service = AiService()
        
        # Если есть задание и пользователь, используем RAG
        if task and user:
            result = ai_service.ask_with_rag(prompt, user, task, task_type)
        else:
            result = ai_service.ask(prompt, user, task_type=task_type)
        
        if 'error' in result:
            return f"❌ Ошибка: {result['error']}"
        
        response = result['response']
        provider = result.get('provider', 'AI')
        
        # Добавляем информацию о провайдере
        response += f"\n\n🤖 Ответ сгенерирован через {provider}"
        
        # Если есть RAG контекст, добавляем его
        if 'rag_context' in result:
            rag = result['rag_context']
            
            # Добавляем похожие задания
            if rag.get('similar_tasks'):
                response += "\n\n📚 **Похожие задания для практики:**"
                for i, similar_task in enumerate(rag['similar_tasks'][:2], 1):
                    response += f"\n{i}. {similar_task['title']} (сложность {similar_task['difficulty']}/5)"
                    response += f"\n   Темы: {', '.join(similar_task['topics'])}"
            
            # Добавляем рекомендации
            if rag.get('recommendations'):
                response += "\n\n💡 **Персональные рекомендации:**"
                for rec in rag['recommendations'][:2]:
                    response += f"\n• {rec['title']}"
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при получении ответа от ИИ: {e}")
        return f"❌ Ошибка ИИ-ассистента: {str(e)}"

@sync_to_async
def db_get_subject_ids():
    return list(Task.objects.values_list('subject_id', flat=True).distinct())

@sync_to_async
def db_get_subjects_by_ids(ids):
    return list(Subject.objects.filter(id__in=ids))

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start - приветствие и главное меню
    
    Создает пользователя если его нет
    Показывает основные возможности бота
    """
    # Проверяем соединение с базой данных (в async контексте)
    try:
        ok = await db_check_connection()
    except Exception as e:
        logger.error(f"Ошибка проверки БД: {e}")
        ok = False
    if not ok:
        await update.message.reply_text(
            "❌ Сервис временно недоступен. База данных не отвечает.\n"
            "Попробуйте через 1-2 минуты."
        )
        return
    
    try:
        user, created = await db_get_or_create_user(update.effective_user)
        
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
            [InlineKeyboardButton("📊 Статистика", callback_data="stats"), InlineKeyboardButton("🎓 План обучения", callback_data="learning_plan")],
            [InlineKeyboardButton("🌐 Сайт", url="https://examflow.ru")],
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
            subject_ids = await db_get_subject_ids()
        except Exception as id_err:
            logger.error(f"subjects_menu: ошибка выборки subject_ids: {id_err}")
            subject_ids = []

        if not subject_ids:
            await query.edit_message_text("📚 Предметы пока загружаются... Попробуйте позже.")
            return

        subjects = await db_get_subjects_by_ids(subject_ids)

        keyboard = []
        for subject in subjects:
            try:
                tasks_count = await db_count_tasks_for_subject(subject.id)
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
    # Получаем список заданий для предмета в безопасном режиме
    tasks = await db_get_tasks_by_subject(subject_id)
    if not tasks:
        subject_name = await db_get_subject_name(subject_id)
        await query.edit_message_text(
            f"❌ В предмете {subject_name} пока нет заданий",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К предметам", callback_data="subjects")]])
        )
        return

    import random
    task = random.choice(list(tasks))

    # Устанавливаем текущее задание в профиле пользователя
    user, _ = await db_get_or_create_user(update.effective_user)
    await db_set_current_task_id(user, task.id)
    logger.info(f"show_subject_topics: установлен current_task_id: {task.id}")

    # Получаем название предмета безопасно
    subject_name = await db_get_subject_name_for_task(task)
    
    task_text = f"""
📝 **Задание №{task.id}**
**Предмет:** {subject_name}

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
    query = update.callback_query
    await query.answer()
    
    # Определяем источник: случайное по предмету или полностью случайное
    if query.data.startswith('subject_'):
        try:
            subject_id = int(query.data.split('_')[1])
        except Exception:
            await query.edit_message_text("❌ Некорректный выбор предмета")
            return
        tasks = await db_get_tasks_by_subject(subject_id)
        if not tasks:
            await query.edit_message_text(f"❌ В предмете пока нет заданий")
            return
        import random
        task = random.choice(list(tasks))
    elif query.data.startswith('random_subject_'):
        subject_id = int(query.data.split('_')[2])
        tasks = await db_get_tasks_by_subject(subject_id)
        if not tasks:
            await query.edit_message_text(f"❌ В предмете пока нет заданий")
            return
        import random
        task = random.choice(list(tasks))
    else:
        tasks = await db_get_all_tasks()
        if not tasks:
            await query.edit_message_text("❌ Задания пока не загружены")
            return
        
        import random
        task = random.choice(list(tasks))
    
    # Сохраняем текущее задание в профиль пользователя, чтобы не терять контекст
    try:
        user, _ = await db_get_or_create_user(update.effective_user)
        await db_set_current_task_id(user, task.id)
        logger.info(f"Установлен current_task_id: {task.id} для пользователя {user.username}")
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
        [InlineKeyboardButton("🔊 Голосовая подсказка", callback_data=f"voice_{task.id}")],
        [InlineKeyboardButton("🤖 Спросить AI", callback_data=f"ai_help_{task.id}")],
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
    logger.info(f"handle_answer вызван для пользователя {update.effective_user.id}")
    
    user, _ = await db_get_or_create_user(update.effective_user)


async def ai_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает запрос на помощь от AI
    
    Использует RAG систему для персонализированной помощи
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем ID задания из callback_data
        task_id = int(query.data.split('_')[2])
        
        # Получаем пользователя и задание
        user, _ = await db_get_or_create_user(update.effective_user)
        task = await db_get_task_by_id(task_id)
        
        if not task:
            await query.edit_message_text("❌ Задание не найдено.")
            return
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(
            "🤔 **AI анализирует задание и ваш прогресс...**\n\n"
            "Это может занять несколько секунд.",
            parse_mode='Markdown'
        )
        
        # Получаем помощь от AI через RAG
        ai_response = await get_ai_response(
            "Объясни, как решить это задание. Дай пошаговое решение с объяснением каждого шага.",
            task_type='task_explanation',
            user=user,
            task=task
        )
        
        # Формируем ответ с кнопками
        response_text = f"""
🤖 **AI ПОМОЩЬ ДЛЯ ЗАДАНИЯ №{task.id}**

{ai_response}

---
💡 **Хотите получить подсказку вместо полного решения?**
"""
        
        keyboard = [
            [InlineKeyboardButton("💡 Только подсказка", callback_data=f"ai_hint_{task.id}")],
            [InlineKeyboardButton("📚 Похожие задания", callback_data=f"similar_{task.id}")],
            [InlineKeyboardButton("🔙 К заданию", callback_data=f"show_task_{task.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await thinking_message.edit_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь {user.id} получил AI помощь для задания {task.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в ai_help_handler: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении AI помощи. Попробуйте позже."
        )


async def ai_hint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает запрос на подсказку от AI
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем ID задания из callback_data
        task_id = int(query.data.split('_')[2])
        
        # Получаем пользователя и задание
        user, _ = await db_get_or_create_user(update.effective_user)
        task = await db_get_task_by_id(task_id)
        
        if not task:
            await query.edit_message_text("❌ Задание не найдено.")
            return
        
        # Показываем сообщение о том, что AI думает
        thinking_message = await query.edit_message_text(
            "💡 **AI готовит подсказку...**\n\n"
            "Это может занять несколько секунд.",
            parse_mode='Markdown'
        )
        
        # Получаем подсказку от AI через RAG
        ai_response = await get_ai_response(
            "Дай подсказку для решения этого задания. НЕ давай полное решение, только направляй ученика.",
            task_type='hint_generation',
            user=user,
            task=task
        )
        
        # Формируем ответ с кнопками
        response_text = f"""
💡 **AI ПОДСКАЗКА ДЛЯ ЗАДАНИЯ №{task.id}**

{ai_response}

---
🤖 **Нужна более подробная помощь?**
"""
        
        keyboard = [
            [InlineKeyboardButton("🤖 Полное решение", callback_data=f"ai_help_{task.id}")],
            [InlineKeyboardButton("📚 Похожие задания", callback_data=f"similar_{task.id}")],
            [InlineKeyboardButton("🔙 К заданию", callback_data=f"show_task_{task.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await thinking_message.edit_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь {user.id} получил AI подсказку для задания {task.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в ai_hint_handler: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при получении AI подсказки. Попробуйте позже."
        )


async def similar_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает похожие задания для практики
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Получаем ID задания из callback_data
        task_id = int(query.data.split('_')[2])
        
        # Получаем задание
        task = await db_get_task_by_id(task_id)
        
        if not task:
            await query.edit_message_text("❌ Задание не найдено.")
            return
        
        # Получаем похожие задания через RAG
        similar_tasks = await sync_to_async(rag_service.find_similar_tasks)(task, limit=5)
        
        if not similar_tasks:
            await query.edit_message_text(
                "📚 **Похожих заданий не найдено**\n\n"
                "Попробуйте решить другие задания по этому предмету.",
                parse_mode='Markdown'
            )
            return
        
        # Формируем список похожих заданий
        response_text = f"""
📚 **ПОХОЖИЕ ЗАДАНИЯ ДЛЯ ПРАКТИКИ**

**Текущее задание:** {task.title}
**Предмет:** {task.subject.name if task.subject else 'Неизвестно'}

**Похожие задания:**
"""
        
        for i, similar_task in enumerate(similar_tasks[:5], 1):
            topics = [topic.name for topic in similar_task.topics.all()] if similar_task.topics.exists() else []
            response_text += f"""
{i}. **{similar_task.title}**
   • Сложность: {similar_task.difficulty}/5
   • Темы: {', '.join(topics) if topics else 'Не указаны'}
"""
        
        response_text += "\n💡 **Выберите задание для решения:**"
        
        # Создаем кнопки для похожих заданий
        keyboard = []
        for similar_task in similar_tasks[:5]:
            keyboard.append([
                InlineKeyboardButton(
                    f"📝 {similar_task.title[:30]}...",
                    callback_data=f"show_task_{similar_task.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 К заданию", callback_data=f"show_task_{task.id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь получил список похожих заданий для {task.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в similar_tasks_handler: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при поиске похожих заданий. Попробуйте позже."
        )


        user, _ = await db_get_or_create_user(update.effective_user)
    
    # Получаем текущее задание из профиля пользователя
    current_task_id = await sync_to_async(get_current_task_id)(user)
    
    if not current_task_id:
        await update.message.reply_text("❌ Сначала выберите задание!")
        return
    
    task = await db_get_task_by_id(current_task_id)  # type: ignore
    user_answer = (update.message.text or '').strip()
    
    # Проверяем ответ (простая текстовая проверка)
    correct_value = (task.answer or '').strip()
    is_correct = bool(correct_value) and (user_answer.lower() == correct_value.lower())
    
    # Сохраняем прогресс (безопасно для async)
    await db_save_progress(user, task, user_answer, is_correct)
    
    # Формируем ответ
    if is_correct:
        response = f"✅ **Правильно!** 🎉\n\n"
        # Обновляем рейтинг
        await db_update_rating_points(user, True)
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
    
    # Сбрасываем текущее задание в профиле
    await sync_to_async(set_current_task_id)(user, None)


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


async def voice_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет голосовую подсказку для задания (Premium функция)
    
    Проверяет подписку пользователя и отправляет аудио
    """
    query = update.callback_query
    await query.answer()
    
    user, _ = await db_get_or_create_user(update.effective_user)
    
    # Получаем текущее задание из профиля пользователя
    current_task_id = await sync_to_async(get_current_task_id)(user)
    
    if not current_task_id:
        await query.edit_message_text("❌ Задание не найдено")
        return
    
    # Проверяем подписку
    subscription = await sync_to_async(lambda: Subscription.objects.filter(user=user, is_active=True).first())() # type: ignore
    if not subscription:
        await query.edit_message_text(
            "🔊 **Голосовые подсказки доступны только в Premium**\n\n"
            "Оформите подписку на сайте для доступа к этой функции.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Оформить Premium", url="https://examflow.ru/dashboard/")
            ]])
        )
        return
    
    task = await sync_to_async(lambda: Task.objects.get(id=current_task_id))() # type: ignore
    
    # Здесь должна быть логика отправки голосового файла
    # Пока отправляем текстовую подсказку
    await query.edit_message_text(
        f"🔊 **Голосовая подсказка для задания №{task.id}**\n\n"
        f"📝 Подсказка пока не добавлена\n\n"
        "🎵 Голосовой файл будет добавлен в ближайшее время!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К заданию", callback_data=f"task_{task.id}")
        ]])
    )


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
        logger.warning(f"random_task: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=task_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as send_err:
            logger.error(f"random_task: send_message тоже не удался: {send_err}")


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Возвращает пользователя в главное меню
    """
    query = update.callback_query
    await query.answer()
    
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
    
    try:
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as edit_err:
        logger.warning(f"main_menu: edit_message_text не удался: {edit_err}. Пробуем send_message")
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,  # type: ignore
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as send_err:
            logger.error(f"main_menu: send_message тоже не удался: {send_err}")


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
