"""
Сервис еженедельных напоминаний: если пользователь не заходил в бота/сайт 7+ дней,
отправляем ему полезное сообщение с призывом вернуться к занятиям.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None

from core.models import UserProfile, ReminderLog

logger = logging.getLogger(__name__)


REMINDER_TEXT = (
    "Привет! Напоминаем о ExamFlow — можно тренироваться по заданиям ЕГЭ/ОГЭ, смотреть прогресс и повторять сложные темы. "
    "Возвращайтесь, чтобы не терять темп!")


def _send_tg_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not (requests and bot_token and chat_id):
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Не удалось отправить напоминание: {e}")
        return False


def send_weekly_inactive_reminders(limit: int = 200) -> int:
    """Отправляет напоминания тем, кто был неактивен >= 7 дней. Возвращает кол-во отправленных."""
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not (requests and bot_token):
        logger.info("Telegram недоступен или токен не задан — напоминания пропущены")
        return 0

    now = timezone.now()
    threshold = now - timedelta(days=7)
    sent = 0

    # Ищем профили с telegram_id и last_activity < 7 дней назад
    qs = UserProfile.objects.filter(
        telegram_id__isnull=False).select_related('user')  # type: ignore
    for profile in qs.iterator():
        if profile.last_activity and profile.last_activity > threshold:
            continue

        chat_id = str(profile.telegram_id)
        user = profile.user

        # Проверим лог: не слали ли уже за последние 7 дней
        log = ReminderLog.objects.filter(
            user=user, reminder_type='weekly_inactive').first()  # type: ignore
        if log and log.last_sent_at and log.last_sent_at > threshold:
            continue

        ok = _send_tg_message(bot_token, chat_id, REMINDER_TEXT)
        if ok:
            ReminderLog.objects.update_or_create(  # type: ignore
                user=user,
                reminder_type='weekly_inactive',
                defaults={'last_sent_at': now},
            )
            sent += 1

        if sent >= limit:
            break

    logger.info(f"Отправлено напоминаний: {sent}")
    return sent
