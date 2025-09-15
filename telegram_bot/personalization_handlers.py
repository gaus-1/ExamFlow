"""
Обработчики персонализации для Telegram бота
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.personalization_system import get_user_insights, PersonalizedRecommendations

logger = logging.getLogger(__name__)

async def personalization_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню персонализации"""
    try:
        keyboard = [
                InlineKeyboardButton("📊 Моя аналитика", callback_data="my_analytics"),
                InlineKeyboardButton("🎯 Рекомендации", callback_data="my_recommendations")
            ],
                InlineKeyboardButton("📚 План обучения", callback_data="study_plan"),
                InlineKeyboardButton("⚠️ Слабые темы", callback_data="weak_topics")
            ],
                InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            "🎓 *Персонализированное обучение*\n\n"
            "Выберите, что хотите узнать о своем прогрессе:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка в меню персонализации: {e}")
        await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")

async def show_my_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает аналитику пользователя"""
    try:
        query = update.callback_query
        await query.answer()

        user_id = context.user_data.get('user_id', 1)
        insights = get_user_insights(user_id)

        if not insights:
            await query.edit_message_text(
                "📊 *Аналитика*\n\n"
                "У вас пока нет данных для анализа.\n"
                "Начните решать задания!",
                parse_mode='Markdown'
            )
            return

        progress = insights.get('progress_summary', {})
        preferences = insights.get('preferences', {})

        message = "📊 *Ваша аналитика*\n\n"

        if progress:
            message += "📈 *Прогресс:*\n"
            message += "   • Решено: {progress.get('solved_tasks', 0)}\n"
            message += "   • Всего: {progress.get('total_tasks', 0)}\n"
            message += "   • Процент: {progress.get('completion_percentage', 0)}%\n\n"

        if preferences.get('favorite_subjects'):
            subjects = ', '.join(preferences['favorite_subjects'])
            message += "🎯 *Любимые предметы:* {subjects}\n"

        keyboard = [
                InlineKeyboardButton(
                    "🎯 Рекомендации", callback_data="my_recommendations"), InlineKeyboardButton(
                    "📚 План обучения", callback_data="study_plan")], [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data="personalization_menu")]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка при показе аналитики: {e}")
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при получении аналитики.",
            parse_mode='Markdown'
        )

async def show_my_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает персонализированные рекомендации"""
    try:
        query = update.callback_query
        await query.answer()

        user_id = context.user_data.get('user_id', 1)
        recommender = PersonalizedRecommendations(user_id)
        recommended_tasks = recommender.get_recommended_tasks(3)

        if not recommended_tasks:
            await query.edit_message_text(
                "🎯 *Рекомендации*\n\n"
                "У нас пока нет рекомендаций для вас.\n"
                "Решите несколько заданий!",
                parse_mode='Markdown'
            )
            return

        message = "🎯 *Персональные рекомендации*\n\n"

        for i, task in enumerate(recommended_tasks, 1):
            difficulty_stars = "⭐" * getattr(task, 'difficulty', 3)
            subject_name = getattr(
                task.subject, 'name', 'Неизвестно') if hasattr(
                task, 'subject') else 'Неизвестно'

            message += "{i}. **{getattr(task, 'title', 'Задание')}**\n"
            message += "   📚 {subject_name}\n"
            message += "   {difficulty_stars} Сложность: {getattr(task, 'difficulty', 3)}/5\n\n"

        keyboard = [
                InlineKeyboardButton("📚 План обучения", callback_data="study_plan"),
                InlineKeyboardButton("⚠️ Слабые темы", callback_data="weak_topics")
            ],
                InlineKeyboardButton("🔙 Назад", callback_data="personalization_menu")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка при показе рекомендаций: {e}")
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при получении рекомендаций.",
            parse_mode='Markdown'
        )

async def show_study_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает план обучения"""
    try:
        query = update.callback_query
        await query.answer()

        user_id = context.user_data.get('user_id', 1)
        recommender = PersonalizedRecommendations(user_id)
        study_plan = recommender.get_study_plan()

        message = "📚 *Ваш план обучения*\n\n"

        daily_goals = study_plan.get('daily_goals', [])
        if daily_goals:
            message += "🎯 *Ежедневные цели:*\n"
            for goal in daily_goals:
                message += "   • {goal.get('description', '')}\n"
            message += "\n"

        weekly_focus = study_plan.get('weekly_focus', [])
        if weekly_focus:
            message += "📅 *Еженедельный фокус:*\n"
            for focus in weekly_focus:
                subject = focus.get('subject', '')
                goal = focus.get('goal', '')
                message += "   • {subject}: {goal}\n"

        keyboard = [
                InlineKeyboardButton(
                    "🎯 Рекомендации", callback_data="my_recommendations"), InlineKeyboardButton(
                    "⚠️ Слабые темы", callback_data="weak_topics")], [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data="personalization_menu")]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка при показе плана обучения: {e}")
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при получении плана обучения.",
            parse_mode='Markdown'
        )

async def show_weak_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает слабые темы"""
    try:
        query = update.callback_query
        await query.answer()

        user_id = context.user_data.get('user_id', 1)
        recommender = PersonalizedRecommendations(user_id)
        weak_topics = recommender.get_weak_topics()

        if not weak_topics:
            await query.edit_message_text(
                "⚠️ *Слабые темы*\n\n"
                "Отлично! У вас пока нет слабых тем. 🎉",
                parse_mode='Markdown'
            )
            return

        message = "⚠️ *Ваши слабые темы*\n\n"

        for i, topic in enumerate(weak_topics[:3], 1):
            subject = topic.get('subject', 'Неизвестно')
            failed_tasks = topic.get('failed_tasks', 0)
            avg_difficulty = topic.get('avg_difficulty', 0)

            message += "{i}. **{subject}**\n"
            message += "   ❌ Провалено: {failed_tasks}\n"
            message += "   📊 Сложность: {avg_difficulty}/5\n\n"

        message += "💡 *Рекомендации:*\n"
        message += "• Решите больше заданий по этим темам\n"
        message += "• Начните с простых и усложняйте\n"

        keyboard = [
                InlineKeyboardButton(
                    "🎯 Рекомендации", callback_data="my_recommendations"), InlineKeyboardButton(
                    "📚 План обучения", callback_data="study_plan")], [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data="personalization_menu")]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Ошибка при показе слабых тем: {e}")
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при получении слабых тем.",
            parse_mode='Markdown'
        )
